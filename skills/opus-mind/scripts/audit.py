#!/usr/bin/env python3
"""
opus-mind audit.py — deterministic system-prompt scorer.

Usage:
    python3 audit.py <prompt.md>           # full report
    python3 audit.py <prompt.md> --json    # machine-readable
    python3 audit.py --self                # audit this skill's own SKILL.md

Scores a prompt against the 6 invariants from methodology/README.md:
    I1 reduce interpretation surface
    I2 eliminate rule conflicts
    I3 catch motivated reasoning (only when refusal content present)
    I4 keep internals private
    I5 calibrate through examples (only when examples present)
    I6 make failure modes explicit

Not heuristic vibes. Every check is a regex or count with an explicit
threshold. Output cites the failing lines so the user can fix.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Tier 1 verbs — inflection-tolerant (utilize → utilizes, utilized, utilizing).
SLOP_TIER1_STEM = [
    "delve", "utilize", "leverage", "facilitate", "encompass",
    "catalyze",
]

# Tier 1 exact — these appear bare; no inflection needed.
SLOP_TIER1_EXACT = [
    "multifaceted", "tapestry", "testament", "paradigm", "synergy",
    "holistic", "nuanced", "realm", "landscape", "myriad", "plethora",
]

# Tier 2 verbs — inflection-tolerant.
SLOP_TIER2_STEM = [
    "streamline", "empower", "foster", "elevate", "resonate",
]

# Tier 2 exact — bare adjectives and nouns.
# Words like "proper" and "reasonable" removed: too ambiguous in English
# (legal/philosophy uses — "proper noun", "reasonable doubt" — are legitimate).
# Prefer false negative over false positive on ambiguous words.
SLOP_TIER2_EXACT = [
    "robust", "comprehensive", "seamless", "cutting-edge", "innovative",
    "pivotal", "intricate", "cornerstone", "effective",
    "efficient", "appropriate", "optimal", "enhance",
]

HEDGES = [
    r"\bgenerally\b", r"\bprobably\b", r"\bmight\b", r"\bshould work\b",
    r"\bwhen appropriate\b", r"\bcarefully\b", r"\boften\b",
    r"\busually\b", r"\bsometimes\b", r"\btypically\b", r"\bideally\b",
    r"\broughly\b", r"\bI think\b", r"\bmay be\b",
    r"\b아마\b", r"것 같", r"~일 수", r"~할 수도",
]

NARRATION = [
    r"\bLet me\b", r"\bLet's dive\b", r"\bI'll check\b",
    r"\bI'll analyze\b", r"\bI'll think\b", r"\bFirst, I'll\b",
    r"\bper my guidelines\b", r"\bI'll route\b", r"\bAllow me to\b",
]

LADDER_SIGNALS = [
    r"Step\s*0\b", r"Step\s*1\b", r"first[- ]match[- ]wins",
    r"Stop at the first match", r"Stops at the first match",
]

REFRAME_SIGNALS = [
    r"reframe", r"reframing", r"signal to refuse",
    r"refusal trigger", r"motivated reasoning",
]

CONSEQUENCE_SIGNALS = [
    r"harms?\b", r"violates?\b", r"exposes?\b",
    r"SEVERE VIOLATION", r"breaks?\b", r"blocks?\b",
    r"fails?\b", r"leaks?\b", r"legal risk",
]

REFUSAL_TOPIC_SIGNALS = [
    r"refuse", r"refusal", r"decline", r"won't help",
    r"do not assist", r"not going to",
]

EXAMPLE_SIGNALS = [
    r"^\s*##+\s*Example", r"^\s*\{user\}", r"^\s*\{example",
    r"^\s*Input:", r"^\s*Example\s*\d*[:\.]",
]

RATIONALE_SIGNALS = [
    r"\{rationale", r"^\s*(Why|이유|Rationale):",
    r"^\s*##+\s*Rationale",
]

XML_OPEN = re.compile(r"^\s*\{([a-zA-Z_][a-zA-Z0-9_]*)\}\s*$")
XML_CLOSE = re.compile(r"^\s*\{/([a-zA-Z_][a-zA-Z0-9_]*)\}\s*$")

NUMBER_CONSTRAINT = re.compile(
    r"\b\d+(?:\.\d+)?\s*%"
    r"|\b\d+(?:\.\d+)?\s*(?:words?|chars?|characters?|lines?|calls?|"
    r"sec|seconds?|min|minutes?|hours?|ms|MB|KB|tokens?|items?|files?|"
    r"turns?|questions?|examples?|times?|requests?|users?|iterations?|"
    r"attempts?|retries|pages?|rows?|bytes?|dollars?)\b"
    r"|\b\d+(?:\.\d+)?\s*(?:per|/)\s*(?:sec|second|min|minute|hour|day|"
    r"call|request|query|turn)s?\b",
    re.IGNORECASE,
)

DIRECTIVE_VERBS = re.compile(
    r"\b(must|do not|don't|never|always|avoid|prefer|default|refuse|"
    r"decline|reject|limit|cap|keep|maintain|ensure)\b",
    re.IGNORECASE,
)


@dataclass
class Finding:
    invariant: str
    line: int
    snippet: str
    issue: str
    fix_pointer: str


@dataclass
class Report:
    path: str
    line_count: int
    pass_flags: dict[str, bool] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def score(self) -> str:
        passed = sum(1 for v in self.pass_flags.values() if v)
        total = len(self.pass_flags)
        return f"{passed}/{total}"


def _iter_findings(
    lines: list[str], patterns: Iterable[str], *, flags: int = 0
) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines, start=1):
        for pat in patterns:
            for m in re.finditer(pat, line, flags=flags):
                hits.append((idx, line.rstrip(), m.group(0)))
    return hits


def _stem_hits(lines: list[str], words: Iterable[str]) -> list[tuple[int, str, str]]:
    # Inflection-tolerant: utilize → utilizes, utilized, utilizing (1-3 letter suffix).
    patterns = [rf"\b{re.escape(w)}\w{{0,3}}\b" for w in words]
    return _iter_findings(lines, patterns, flags=re.IGNORECASE)


def _exact_hits(lines: list[str], words: Iterable[str]) -> list[tuple[int, str, str]]:
    # Exact word boundary — no inflection.
    patterns = [rf"\b{re.escape(w)}\b" for w in words]
    return _iter_findings(lines, patterns, flags=re.IGNORECASE)


def _check_xml_balance(lines: list[str]) -> tuple[int, list[tuple[int, str]]]:
    stack: list[tuple[str, int]] = []
    coverage_lines = 0
    unmatched: list[tuple[int, str]] = []
    inside_depth = 0
    for idx, line in enumerate(lines, start=1):
        m_open = XML_OPEN.match(line)
        m_close = XML_CLOSE.match(line)
        if m_open:
            stack.append((m_open.group(1), idx))
            inside_depth += 1
            continue
        if m_close:
            if stack and stack[-1][0] == m_close.group(1):
                stack.pop()
                inside_depth -= 1
            else:
                unmatched.append((idx, line.rstrip()))
            continue
        if inside_depth > 0 and line.strip():
            coverage_lines += 1
    for name, idx in stack:
        unmatched.append((idx, f"unclosed {{{name}}}"))
    return coverage_lines, unmatched


def audit(path: Path) -> Report:
    text = path.read_text(encoding="utf-8")
    return audit_text(text, source_label=str(path))


def audit_text(text: str, source_label: str = "<text>") -> Report:
    lines = text.splitlines()
    report = Report(path=source_label, line_count=len(lines))

    # --- raw counts ---
    slop1 = _stem_hits(lines, SLOP_TIER1_STEM) + _exact_hits(lines, SLOP_TIER1_EXACT)
    slop2 = _stem_hits(lines, SLOP_TIER2_STEM) + _exact_hits(lines, SLOP_TIER2_EXACT)
    slop2_flagged = [
        (ln, snip, match)
        for (ln, snip, match) in slop2
        if not NUMBER_CONSTRAINT.search(snip)
    ]
    hedges = _iter_findings(lines, HEDGES, flags=re.IGNORECASE)
    narration = _iter_findings(lines, NARRATION, flags=re.IGNORECASE)
    ladder = _iter_findings(lines, LADDER_SIGNALS, flags=re.IGNORECASE)
    reframe = _iter_findings(lines, REFRAME_SIGNALS, flags=re.IGNORECASE)
    consequences = _iter_findings(lines, CONSEQUENCE_SIGNALS, flags=re.IGNORECASE)
    refusal_topic = _iter_findings(lines, REFUSAL_TOPIC_SIGNALS, flags=re.IGNORECASE)
    examples = _iter_findings(lines, EXAMPLE_SIGNALS, flags=re.MULTILINE)
    rationales = _iter_findings(lines, RATIONALE_SIGNALS, flags=re.MULTILINE)
    numbers = [
        (idx, line.rstrip(), m.group(0))
        for idx, line in enumerate(lines, start=1)
        for m in NUMBER_CONSTRAINT.finditer(line)
    ]
    directives = [
        idx
        for idx, line in enumerate(lines, start=1)
        if DIRECTIVE_VERBS.search(line)
    ]
    xml_coverage, xml_unmatched = _check_xml_balance(lines)

    number_density = (
        len(numbers) / max(len(directives), 1) if directives else 0.0
    )
    xml_coverage_pct = (
        xml_coverage / max(len(lines) - xml_coverage, 1)
    )

    report.metrics = {
        "slop_tier1": len(slop1),
        "slop_tier2_no_number": len(slop2_flagged),
        "hedges": len(hedges),
        "narration": len(narration),
        "ladder_signals": len(ladder),
        "reframe_signals": len(reframe),
        "consequences": len(consequences),
        "refusal_topic_signals": len(refusal_topic),
        "examples": len(examples),
        "rationales": len(rationales),
        "numeric_constraints": len(numbers),
        "directives": len(directives),
        "number_density": round(number_density, 3),
        "xml_inside_lines": xml_coverage,
        "xml_unmatched": len(xml_unmatched),
    }

    # --- I1: reduce interpretation surface ---
    i1_pass = (
        report.metrics["slop_tier1"] == 0
        and report.metrics["slop_tier2_no_number"] == 0
        and report.metrics["hedges"] <= 2
    )
    report.pass_flags["I1_reduce_interpretation"] = i1_pass
    for ln, snip, match in slop1:
        report.findings.append(Finding(
            "I1", ln, snip, f"Tier 1 slop word: {match!r}",
            "references/primitives/03-hard-numbers.md",
        ))
    for ln, snip, match in slop2_flagged:
        report.findings.append(Finding(
            "I1", ln, snip, f"Adj without number: {match!r}",
            "references/primitives/03-hard-numbers.md",
        ))
    for ln, snip, match in hedges[2:]:
        report.findings.append(Finding(
            "I1", ln, snip, f"Hedge word: {match!r}",
            "references/primitives/03-hard-numbers.md",
        ))

    # --- I2: eliminate rule conflicts ---
    # Need a ladder whenever the doc has >=3 directives on any routing topic.
    # Proxy: if directives >= 6, require at least one ladder signal.
    needs_ladder = report.metrics["directives"] >= 6
    i2_pass = (not needs_ladder) or report.metrics["ladder_signals"] >= 1
    report.pass_flags["I2_no_rule_conflicts"] = i2_pass
    if not i2_pass:
        report.findings.append(Finding(
            "I2", 0, "",
            f"{report.metrics['directives']} directives, 0 ladders",
            "references/primitives/02-decision-ladders.md",
        ))

    # --- I3: catch motivated reasoning ---
    # Only required when the doc discusses refusals.
    has_refusal_content = report.metrics["refusal_topic_signals"] >= 2
    i3_pass = (not has_refusal_content) or report.metrics["reframe_signals"] >= 1
    report.pass_flags["I3_motivated_reasoning"] = i3_pass
    if not i3_pass:
        report.findings.append(Finding(
            "I3", 0, "",
            "refusal content lacks reframe-as-signal guard",
            "references/primitives/09-reframe-as-signal.md",
        ))

    # --- I4: keep internals private ---
    i4_pass = report.metrics["narration"] == 0
    report.pass_flags["I4_anti_narration"] = i4_pass
    for ln, snip, match in narration:
        report.findings.append(Finding(
            "I4", ln, snip, f"Narration phrase: {match!r}",
            "references/primitives/08-anti-narration.md",
        ))

    # --- I5: calibrate through examples ---
    # If the doc has examples at all, they must carry rationale.
    has_examples = report.metrics["examples"] >= 1
    i5_pass = (not has_examples) or report.metrics["rationales"] >= 1
    report.pass_flags["I5_example_rationale"] = i5_pass
    if not i5_pass:
        report.findings.append(Finding(
            "I5", 0, "",
            f"{report.metrics['examples']} examples, 0 rationales",
            "references/primitives/06-example-plus-rationale.md",
        ))

    # --- I6: failure modes explicit ---
    # Every 10 directives should have at least 1 consequence statement.
    required = max(1, report.metrics["directives"] // 10)
    i6_pass = report.metrics["consequences"] >= required
    report.pass_flags["I6_failure_modes_explicit"] = i6_pass
    if not i6_pass:
        report.findings.append(Finding(
            "I6", 0, "",
            f"{report.metrics['consequences']} consequences, need ≥ {required}",
            "references/techniques/04-consequence-statement.md",
        ))

    # --- structural warnings (not gating, but surfaced) ---
    for ln, snip in xml_unmatched:
        report.findings.append(Finding(
            "structural", ln, snip, "unmatched XML block",
            "references/primitives/01-namespace-blocks.md",
        ))

    return report


def _format_human(r: Report) -> str:
    out = []
    out.append(f"path: {r.path}")
    out.append(f"lines: {r.line_count}")
    out.append(f"score: {r.score}")
    out.append("")
    out.append("invariants:")
    for key, val in r.pass_flags.items():
        mark = "PASS" if val else "FAIL"
        out.append(f"  [{mark}] {key}")
    out.append("")
    out.append("metrics:")
    for key, val in r.metrics.items():
        out.append(f"  {key}: {val}")
    if r.findings:
        out.append("")
        out.append("findings:")
        for f in r.findings:
            prefix = f"  L{f.line}" if f.line else "  --"
            out.append(
                f"{prefix} [{f.invariant}] {f.issue}"
            )
            if f.snippet:
                snip = f.snippet[:100]
                out.append(f"        > {snip}")
            out.append(f"        fix: {f.fix_pointer}")
    return "\n".join(out)


def _format_json(r: Report) -> str:
    return json.dumps({
        "path": r.path,
        "line_count": r.line_count,
        "score": r.score,
        "pass": r.pass_flags,
        "metrics": r.metrics,
        "findings": [
            {
                "invariant": f.invariant,
                "line": f.line,
                "snippet": f.snippet,
                "issue": f.issue,
                "fix_pointer": f.fix_pointer,
            }
            for f in r.findings
        ],
    }, indent=2, ensure_ascii=False)


CROSSCHECK_PROMPT_HEADER = """\
You are a second reviewer for a system-prompt auditor.

A deterministic auditor (regex + counts, no LLM) has scored the target prompt
against 6 invariants:
- I1 reduce interpretation surface (no vague adj, no hedges)
- I2 eliminate rule conflicts (decision ladders for routing)
- I3 catch motivated reasoning (reframe-as-signal for refusals)
- I4 keep internals private (no machinery narration)
- I5 calibrate through examples (every example has rationale)
- I6 make failure modes explicit (consequences stated)

Your job:
1. Verify the deterministic findings below. Flag any false positives.
2. Surface semantic violations the regex checker cannot catch, such as:
   - rules that contradict each other on some input (even if no ladder)
   - examples whose rationale is actually non-load-bearing filler
   - consequence statements that name a weak or wrong harm
   - refusal policy that silently exempts a high-risk category
   - capability claims that are brittle under rephrase
3. Output: JSON with { false_positives: [], additional_findings: [],
   severity_delta: {I1..I6: "+/-/none"} }.

Use the primitive references below for vocabulary. Cite source/opus-4.7.txt
line numbers when relevant.
"""


def _build_crosscheck_prompt(r: Report, target_text: str) -> str:
    lines = [CROSSCHECK_PROMPT_HEADER, ""]
    lines.append("## Auditor report (deterministic)")
    lines.append("")
    lines.append(f"path: {r.path}")
    lines.append(f"score: {r.score}")
    lines.append("")
    lines.append("invariants:")
    for k, v in r.pass_flags.items():
        mark = "PASS" if v else "FAIL"
        lines.append(f"  [{mark}] {k}")
    lines.append("")
    lines.append("findings:")
    for f in r.findings:
        prefix = f"L{f.line}" if f.line else "--"
        lines.append(f"  {prefix} [{f.invariant}] {f.issue}")
        if f.snippet:
            lines.append(f"       > {f.snippet[:120]}")
    lines.append("")
    lines.append("## Target prompt (the thing being audited)")
    lines.append("")
    lines.append("```")
    lines.append(target_text[:12000])
    lines.append("```")
    lines.append("")
    lines.append("## Primitive vocabulary")
    lines.append(
        "01 namespace-blocks, 02 decision-ladders, 03 hard-numbers, "
        "04 default-plus-exception, 05 cue-based-matching, "
        "06 example-plus-rationale, 07 self-check, 08 anti-narration, "
        "09 reframe-as-signal, 10 asymmetric-trust, "
        "11 capability-disclosure, 12 hierarchical-override."
    )
    lines.append("")
    lines.append(
        "Respond with JSON only. Keys: "
        "false_positives, additional_findings, severity_delta, overall_verdict."
    )
    return "\n".join(lines)


def _try_api_call(prompt: str, model: str) -> str | None:
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main() -> int:
    parser = argparse.ArgumentParser(description="opus-mind prompt auditor")
    parser.add_argument("path", nargs="?", help="prompt file to audit")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--self", action="store_true",
        help="audit the SKILL.md next to this script",
    )
    parser.add_argument(
        "--crosscheck",
        choices=["prompt", "exec"],
        help="emit LLM crosscheck prompt (prompt) or call the API (exec)",
    )
    parser.add_argument(
        "--crosscheck-model",
        default="claude-opus-4-7",
        help="model to use for --crosscheck exec (default: claude-opus-4-7)",
    )
    args = parser.parse_args()

    if args.self:
        target = Path(__file__).resolve().parent.parent / "SKILL.md"
        report = audit(target)
    elif args.path == "-":
        text = sys.stdin.read()
        if not text.strip():
            print("error: stdin is empty", file=sys.stderr)
            return 2
        report = audit_text(text, source_label="<stdin>")
    elif args.path:
        target = Path(args.path)
        if not target.exists():
            print(f"error: {target} not found", file=sys.stderr)
            return 2
        try:
            report = audit(target)
        except UnicodeDecodeError:
            print(f"error: {target} is not valid UTF-8 text", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 2

    if args.crosscheck:
        target_text = target.read_text(encoding="utf-8")
        prompt = _build_crosscheck_prompt(report, target_text)
        if args.crosscheck == "prompt":
            print(prompt)
            return 0
        response = _try_api_call(prompt, args.crosscheck_model)
        if response is None:
            print(
                "note: ANTHROPIC_API_KEY missing or anthropic SDK not installed.",
                file=sys.stderr,
            )
            print("emitting prompt for manual paste.", file=sys.stderr)
            print(prompt)
            return 2
        print(response)
        return 0

    print(_format_json(report) if args.json else _format_human(report))
    return 0 if all(report.pass_flags.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
