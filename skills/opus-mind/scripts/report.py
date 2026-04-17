#!/usr/bin/env python3
"""
opus-mind report.py — one-shot prompt evaluation + ranked action plan.

Combines audit (structural health), plan (domain coverage), and decode
(primitive inventory) into a single readable report with:

    - Quality score: health × coverage (geometric mean, 0-10 scale)
    - Verdict: THIN / POOR / BORDERLINE / GOOD
    - Per-failing-invariant findings + TL;DR snippet from the primitive doc
    - Missing-required primitives + TL;DR + quick-fix command
    - Ranked 3-step improvement plan with predicted score delta

Usage:
    python3 report.py <path>              # human-readable
    python3 report.py <path> --json       # structured JSON
    python3 report.py <path> --md         # markdown (PR comment friendly)
    python3 report.py -                   # stdin
    python3 report.py <path> --no-snippet # skip TL;DR loading (faster, terser)

Design contract:
    - Zero LLM calls. Score is deterministic. Snippets are file reads.
    - Coverage score fixes the "empty file scores 10/11" hole: if a
      required primitive for this domain is missing, coverage drops.
    - Verdict=THIN short-circuits when the prompt is too small to audit
      (directives < 3 AND lines < 10). Prevents "empty → near-perfect".
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit  # type: ignore  # noqa: E402
import decode  # type: ignore  # noqa: E402
import plan as plan_mod  # type: ignore  # noqa: E402


# Primitive / technique doc locations (via skill references/ symlinks).
SKILL_ROOT = HERE.parent
PRIMITIVES_DIR = SKILL_ROOT / "references" / "primitives"
TECHNIQUES_DIR = SKILL_ROOT / "references" / "techniques"

# Invariant → (human label, primitive-file pointer, fix-add key or None)
INVARIANT_META: dict[str, tuple[str, Path, str | None]] = {
    "I1_reduce_interpretation":
        ("Reduce interpretation surface",
         PRIMITIVES_DIR / "03-hard-numbers.md", None),
    "I2_no_rule_conflicts":
        ("Eliminate rule conflicts",
         PRIMITIVES_DIR / "02-decision-ladders.md", "ladder"),
    "I3_motivated_reasoning":
        ("Catch motivated reasoning",
         PRIMITIVES_DIR / "09-reframe-as-signal.md", "reframe-guard"),
    "I4_anti_narration":
        ("Keep internals private",
         PRIMITIVES_DIR / "08-anti-narration.md", None),
    "I5_example_rationale":
        ("Calibrate through examples",
         PRIMITIVES_DIR / "06-example-plus-rationale.md", None),
    "I6_failure_modes_explicit":
        ("Make failure modes explicit",
         TECHNIQUES_DIR / "04-consequence-statement.md", "consequences"),
    "I7_namespace_balance":
        ("Namespace block balance",
         PRIMITIVES_DIR / "01-namespace-blocks.md", None),
    "I8_default_exception":
        ("Default + exception",
         PRIMITIVES_DIR / "04-default-plus-exception.md", "defaults"),
    "I9_self_check":
        ("Self-check before emit",
         PRIMITIVES_DIR / "07-self-check-assertions.md", "self-check"),
    "I10_tier_labels":
        ("Hard tier labels",
         PRIMITIVES_DIR / "10-asymmetric-trust.md", "tier-labels"),
    "I11_hierarchical_override":
        ("Hierarchical override",
         PRIMITIVES_DIR / "12-hierarchical-override.md", "tier-labels"),
}

# --add keys that fix.py knows about and what invariants they lift.
FIX_ADD_LIFTS: dict[str, set[str]] = {
    "ladder": {"I2_no_rule_conflicts"},
    "reframe-guard": {"I3_motivated_reasoning"},
    "consequences": {"I6_failure_modes_explicit"},
    "defaults": {"I8_default_exception"},
    "self-check": {"I9_self_check"},
    "tier-labels": {"I10_tier_labels", "I11_hierarchical_override"},
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass
class Score:
    health: int                # invariant pass count (0-11)
    health_total: int          # 11
    coverage_passing: int      # required invariants currently passing
    coverage_total: int        # required invariants count for this domain
    quality: float             # geometric mean, 0-10
    verdict: str               # THIN / POOR / BORDERLINE / GOOD
    thin_reason: str | None    # populated when verdict == THIN

    @property
    def health_str(self) -> str:
        return f"{self.health}/{self.health_total}"

    @property
    def coverage_str(self) -> str:
        return f"{self.coverage_passing}/{self.coverage_total}"


def _compute_score(
    report: audit.Report,
    required: set[str],
    passing_required: set[str],
    directives: int,
    lines: int,
) -> Score:
    health = sum(1 for v in report.pass_flags.values() if v)
    health_total = len(report.pass_flags) or 1
    coverage_total = len(required) or 1
    coverage_passing = len(passing_required)

    # Thin-content guard: too small to audit meaningfully.
    thin_reason: str | None = None
    if directives < 3 and lines < 10:
        thin_reason = (
            f"too thin to audit: {directives} directives, {lines} lines "
            f"(need ≥ 3 directives or ≥ 10 lines)"
        )

    # Quality on 0-10 scale via geometric mean of normalized health and
    # coverage. Both must be present; one being 0 crashes the score.
    h_norm = health / health_total
    c_norm = coverage_passing / coverage_total
    if thin_reason is not None:
        quality = 0.0
    else:
        quality = round(10.0 * math.sqrt(h_norm * c_norm), 1)

    if thin_reason is not None:
        verdict = "THIN"
    elif quality >= 7.5:
        verdict = "GOOD"
    elif quality >= 5.0:
        verdict = "BORDERLINE"
    else:
        verdict = "POOR"

    return Score(
        health=health,
        health_total=health_total,
        coverage_passing=coverage_passing,
        coverage_total=coverage_total,
        quality=quality,
        verdict=verdict,
        thin_reason=thin_reason,
    )


# ---------------------------------------------------------------------------
# Primitive TL;DR loader
# ---------------------------------------------------------------------------


_TLDR_HEADER = re.compile(r"^##\s+TL;DR\s*$", re.IGNORECASE)
_NEXT_SECTION = re.compile(r"^##\s+\S")


def _load_tldr(doc_path: Path, max_chars: int = 320) -> str:
    """Extract the ## TL;DR section text from a primitive / technique doc."""
    if not doc_path.exists():
        return ""
    text = doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    buf: list[str] = []
    capturing = False
    for line in lines:
        if _TLDR_HEADER.match(line):
            capturing = True
            continue
        if capturing and _NEXT_SECTION.match(line):
            break
        if capturing and line.strip():
            buf.append(line.strip())
    out = " ".join(buf)
    if len(out) > max_chars:
        out = out[:max_chars].rstrip() + "..."
    return out


# ---------------------------------------------------------------------------
# Ranked improvement plan
# ---------------------------------------------------------------------------


@dataclass
class PlanStep:
    rank: int
    kind: str              # "batch-fix" / "manual" / "recheck"
    description: str
    command: str | None
    predicted_delta: str | None  # e.g. "+2 health, +2 coverage"


def _build_action_plan(
    failing: list[str],
    missing_required: list[str],
    report: audit.Report,
    path_arg: str,
) -> list[PlanStep]:
    steps: list[PlanStep] = []

    # Step 1 — batch-fix for anything the --add keys can inject.
    addable: list[str] = []
    lifts_health: set[str] = set()
    lifts_coverage: set[str] = set()
    for add_key, invs in FIX_ADD_LIFTS.items():
        inv_set = set(invs)
        if inv_set & set(failing):
            addable.append(add_key)
            lifts_health |= inv_set & set(failing)
        if inv_set & set(missing_required):
            if add_key not in addable:
                addable.append(add_key)
            lifts_coverage |= inv_set & set(missing_required)

    if addable:
        delta_parts = []
        if lifts_health:
            delta_parts.append(f"+{len(lifts_health)} health")
        if lifts_coverage:
            delta_parts.append(f"+{len(lifts_coverage)} coverage")
        steps.append(PlanStep(
            rank=1,
            kind="batch-fix",
            description=(
                "Inject structural skeletons for "
                f"{', '.join(addable)}. "
                "Then fill the placeholder content with domain-specific words."
            ),
            command=(
                f"opus-mind fix {path_arg} --add {','.join(addable)} --apply"
            ),
            predicted_delta=" / ".join(delta_parts) or None,
        ))

    # Step 2 — manual fixes for I1 (hedges/slop/adj-no-number) and I4
    # (narration), since those require rewording, not structural injection.
    manual_targets: list[str] = []
    if "I1_reduce_interpretation" in failing:
        h = int(report.metrics.get("hedges", 0))
        hd = float(report.metrics.get("hedge_density", 0.0))
        manual_targets.append(
            f"Replace hedges with numeric constraints "
            f"(hedges={h}, density={hd:.2f} > 0.25)"
        )
    if "I4_anti_narration" in failing:
        n = int(report.metrics.get("narration", 0))
        manual_targets.append(
            f"Delete {n} narration phrase(s) "
            f"('Let me', 'per my guidelines', ...)"
        )
    if "I5_example_rationale" in failing:
        ex = int(report.metrics.get("examples", 0))
        manual_targets.append(
            f"Add a rationale to each of {ex} example(s) "
            "(use `{rationale}...{/rationale}`)"
        )
    if manual_targets:
        steps.append(PlanStep(
            rank=len(steps) + 1,
            kind="manual",
            description="; ".join(manual_targets),
            command=None,
            predicted_delta=None,
        ))

    # Step 3 — re-check.
    if steps:
        steps.append(PlanStep(
            rank=len(steps) + 1,
            kind="recheck",
            description="Re-score and verify the verdict moves up.",
            command=f"opus-mind report {path_arg}",
            predicted_delta=None,
        ))

    return steps


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


@dataclass
class InvariantFailure:
    invariant: str
    label: str
    findings: list[dict]            # {line, snippet, issue}
    primitive_ref: str              # "references/primitives/NN-name.md"
    tldr: str
    fix_add_key: str | None


@dataclass
class MissingPrimitive:
    invariant: str
    label: str
    primitive_ref: str
    tldr: str
    fix_add_key: str | None


@dataclass
class Report:
    path: str
    lines: int
    score: Score
    domain: dict[str, bool]
    failing: list[InvariantFailure]
    missing_required: list[MissingPrimitive]
    action_plan: list[PlanStep]
    raw_metrics: dict = field(default_factory=dict)


def build_report(
    path: Path | None = None,
    text: str | None = None,
    include_snippets: bool = True,
) -> Report:
    if text is None:
        assert path is not None
        text = path.read_text(encoding="utf-8")
        label = str(path)
        path_arg = str(path)
    else:
        label = "<stdin>"
        path_arg = "-"

    plan_result = plan_mod.plan(path=path, text=text)
    audit_report: audit.Report = plan_result["report"]
    required = set(plan_result["required_invariants"])
    passing_required = set(plan_result["passing_required"])
    missing_required_keys = plan_result["missing_required"]
    failing_invariants = [
        k for k, v in audit_report.pass_flags.items() if not v
    ]

    score = _compute_score(
        audit_report,
        required=required,
        passing_required=passing_required,
        directives=int(audit_report.metrics.get("directives", 0)),
        lines=audit_report.line_count,
    )

    # Per-invariant findings grouped by invariant code.
    findings_by_inv: dict[str, list[dict]] = {}
    for f in audit_report.findings:
        findings_by_inv.setdefault(f.invariant, []).append({
            "line": f.line,
            "snippet": f.snippet[:120],
            "issue": f.issue,
        })

    failures: list[InvariantFailure] = []
    for inv in failing_invariants:
        meta = INVARIANT_META.get(inv)
        if meta is None:
            continue
        label, doc, fix_key = meta
        tldr = _load_tldr(doc) if include_snippets else ""
        failures.append(InvariantFailure(
            invariant=inv,
            label=label,
            findings=findings_by_inv.get(
                inv.split("_")[0], [],  # audit uses "I1", not "I1_reduce_..."
            ),
            primitive_ref=str(doc.relative_to(SKILL_ROOT.parent))
                if SKILL_ROOT.parent in doc.parents else str(doc),
            tldr=tldr,
            fix_add_key=fix_key,
        ))

    missing: list[MissingPrimitive] = []
    for inv in missing_required_keys:
        meta = INVARIANT_META.get(inv)
        if meta is None:
            continue
        label, doc, fix_key = meta
        tldr = _load_tldr(doc) if include_snippets else ""
        missing.append(MissingPrimitive(
            invariant=inv,
            label=label,
            primitive_ref=str(doc.relative_to(SKILL_ROOT.parent))
                if SKILL_ROOT.parent in doc.parents else str(doc),
            tldr=tldr,
            fix_add_key=fix_key,
        ))

    action_plan = _build_action_plan(
        failing=failing_invariants,
        missing_required=missing_required_keys,
        report=audit_report,
        path_arg=path_arg,
    )

    return Report(
        path=label,
        lines=audit_report.line_count,
        score=score,
        domain=plan_result["domain"],
        failing=failures,
        missing_required=missing,
        action_plan=action_plan,
        raw_metrics=dict(audit_report.metrics),
    )


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _verdict_marker(verdict: str) -> str:
    return {
        "GOOD": "[GOOD]",
        "BORDERLINE": "[BORDERLINE]",
        "POOR": "[POOR]",
        "THIN": "[THIN]",
    }.get(verdict, f"[{verdict}]")


def format_human(r: Report) -> str:
    out: list[str] = []
    out.append(f"path: {r.path}  ({r.lines} lines)")
    out.append("")
    out.append("== Quality ==")
    out.append(f"  structural health: {r.score.health_str}")
    out.append(f"  coverage:          {r.score.coverage_str}  (required for this domain)")
    out.append(f"  quality:           {r.score.quality}/10")
    out.append(f"  verdict:           {_verdict_marker(r.score.verdict)}")
    if r.score.thin_reason:
        out.append(f"  note:              {r.score.thin_reason}")
    out.append("")

    active = [k for k, v in r.domain.items() if v]
    if active:
        out.append(f"domain signals: {', '.join(active)}")
    else:
        out.append("domain signals: (none)")
    out.append("")

    if r.failing:
        out.append(f"== Failing invariants ({len(r.failing)}) ==")
        for f in r.failing:
            out.append(f"  [{f.invariant}] {f.label}")
            for finding in f.findings[:3]:
                if finding["line"]:
                    out.append(
                        f"    L{finding['line']}: {finding['issue']}"
                    )
                else:
                    out.append(f"    - {finding['issue']}")
            if len(f.findings) > 3:
                out.append(f"    ... +{len(f.findings) - 3} more")
            if f.tldr:
                out.append(f"    why: {f.tldr}")
            out.append(f"    read: {f.primitive_ref}")
            if f.fix_add_key:
                out.append(f"    fix:  opus-mind fix <path> --add {f.fix_add_key}")
            out.append("")

    if r.missing_required:
        out.append(
            f"== Missing required primitives ({len(r.missing_required)}) =="
        )
        for m in r.missing_required:
            out.append(f"  [{m.invariant}] {m.label}")
            if m.tldr:
                out.append(f"    why: {m.tldr}")
            out.append(f"    read: {m.primitive_ref}")
            if m.fix_add_key:
                out.append(f"    fix:  opus-mind fix <path> --add {m.fix_add_key}")
            out.append("")

    if r.action_plan:
        out.append("== Improvement plan ==")
        for step in r.action_plan:
            prefix = f"  {step.rank}. [{step.kind}]"
            out.append(f"{prefix} {step.description}")
            if step.command:
                out.append(f"     $ {step.command}")
            if step.predicted_delta:
                out.append(f"     predicted: {step.predicted_delta}")
            out.append("")
    elif not r.score.thin_reason:
        out.append("== Improvement plan ==")
        out.append("  (nothing to do — all required primitives present, no failing invariants)")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def format_markdown(r: Report) -> str:
    out: list[str] = []
    out.append(f"# Evaluation Report — `{r.path}`")
    out.append("")
    out.append(f"**Verdict: {r.score.verdict}** · quality **{r.score.quality}/10** · {r.lines} lines")
    out.append("")
    out.append("| Axis | Score |")
    out.append("|---|---|")
    out.append(f"| Structural health | {r.score.health_str} |")
    out.append(f"| Coverage (for this domain) | {r.score.coverage_str} |")
    out.append(f"| Overall quality | {r.score.quality}/10 |")
    if r.score.thin_reason:
        out.append("")
        out.append(f"> **Note:** {r.score.thin_reason}")
    out.append("")

    active = [k for k, v in r.domain.items() if v]
    if active:
        out.append(f"**Domain signals:** {', '.join(f'`{a}`' for a in active)}")
        out.append("")

    if r.failing:
        out.append(f"## Failing invariants ({len(r.failing)})")
        out.append("")
        for f in r.failing:
            out.append(f"### `{f.invariant}` — {f.label}")
            if f.findings:
                for finding in f.findings[:5]:
                    if finding["line"]:
                        out.append(f"- L{finding['line']}: {finding['issue']}")
                    else:
                        out.append(f"- {finding['issue']}")
                if len(f.findings) > 5:
                    out.append(f"- _+{len(f.findings) - 5} more_")
            if f.tldr:
                out.append("")
                out.append(f"> **Why it matters:** {f.tldr}")
            out.append("")
            out.append(f"Read: [`{f.primitive_ref}`](../../{f.primitive_ref})")
            if f.fix_add_key:
                out.append(
                    f"Fix: `opus-mind fix <path> --add {f.fix_add_key}`"
                )
            out.append("")

    if r.missing_required:
        out.append(f"## Missing required primitives ({len(r.missing_required)})")
        out.append("")
        for m in r.missing_required:
            out.append(f"### `{m.invariant}` — {m.label}")
            if m.tldr:
                out.append(f"> {m.tldr}")
                out.append("")
            out.append(f"Read: [`{m.primitive_ref}`](../../{m.primitive_ref})")
            if m.fix_add_key:
                out.append(
                    f"Fix: `opus-mind fix <path> --add {m.fix_add_key}`"
                )
            out.append("")

    if r.action_plan:
        out.append("## Improvement plan")
        out.append("")
        for step in r.action_plan:
            out.append(f"**{step.rank}. {step.kind}** — {step.description}")
            if step.command:
                out.append("")
                out.append("```bash")
                out.append(step.command)
                out.append("```")
            if step.predicted_delta:
                out.append(f"_Predicted: {step.predicted_delta}_")
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def format_json(r: Report) -> str:
    payload = {
        "path": r.path,
        "lines": r.lines,
        "score": {
            "health": r.score.health,
            "health_total": r.score.health_total,
            "coverage_passing": r.score.coverage_passing,
            "coverage_total": r.score.coverage_total,
            "quality": r.score.quality,
            "verdict": r.score.verdict,
            "thin_reason": r.score.thin_reason,
        },
        "domain": r.domain,
        "failing": [
            {
                "invariant": f.invariant,
                "label": f.label,
                "findings": f.findings,
                "primitive_ref": f.primitive_ref,
                "tldr": f.tldr,
                "fix_add_key": f.fix_add_key,
            }
            for f in r.failing
        ],
        "missing_required": [
            {
                "invariant": m.invariant,
                "label": m.label,
                "primitive_ref": m.primitive_ref,
                "tldr": m.tldr,
                "fix_add_key": m.fix_add_key,
            }
            for m in r.missing_required
        ],
        "action_plan": [
            {
                "rank": s.rank,
                "kind": s.kind,
                "description": s.description,
                "command": s.command,
                "predicted_delta": s.predicted_delta,
            }
            for s in r.action_plan
        ],
        "raw_metrics": {
            k: (float(v) if isinstance(v, (int, float)) else v)
            for k, v in r.raw_metrics.items()
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="opus-mind report — evaluate a prompt + ranked action plan"
    )
    parser.add_argument(
        "path",
        help="prompt file to evaluate (use '-' for stdin)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true", help="JSON output")
    mode.add_argument("--md", action="store_true", help="Markdown output")
    parser.add_argument(
        "--no-snippet", action="store_true",
        help="skip loading primitive TL;DR snippets (faster)",
    )
    args = parser.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
        if not text.strip():
            print("error: stdin is empty", file=sys.stderr)
            return 2
        r = build_report(text=text, include_snippets=not args.no_snippet)
    else:
        p = Path(args.path)
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
        try:
            r = build_report(path=p, include_snippets=not args.no_snippet)
        except UnicodeDecodeError:
            print(f"error: {p} is not valid UTF-8 text", file=sys.stderr)
            return 2

    if args.json:
        print(format_json(r))
    elif args.md:
        print(format_markdown(r))
    else:
        print(format_human(r))

    # Exit code: 0 on GOOD, 1 on BORDERLINE/POOR/THIN (so CI can gate).
    return 0 if r.score.verdict == "GOOD" else 1


if __name__ == "__main__":
    sys.exit(main())
