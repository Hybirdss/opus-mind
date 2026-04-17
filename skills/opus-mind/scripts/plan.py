#!/usr/bin/env python3
"""
opus-mind plan.py — completeness gap report.

Takes a prompt, infers the domain heuristically, reports which
primitives are present, missing, and which of the missing ones are
REQUIRED given the prompt's shape. Output is a TODO checklist — not
a score. The goal is action, not a number.

Usage:
    python3 plan.py <path>
    python3 plan.py <path> --json
    python3 plan.py -                  # stdin

Domain inference (structural, no hardcoded product terms):
    - has_tools        = directives mention calls / tools / web_search pattern
    - has_refusals     = refusal_topic_signals >= 2
    - has_examples     = examples >= 1
    - is_long          = directives >= 12 or lines > 100
    - has_conflicts    = refusal_topic_signals >= 2 AND directives >= 8

Required primitives per domain signal:
    has_refusals       → I3 (reframe), I10 (tier labels)
    has_conflicts      → I11 (hierarchical override)
    is_long            → I9 (self-check)
    has_tools          → I12 capability-disclosure (advisory only, not gated)
    always             → I1, I2, I6, I7
    has_examples       → I5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit  # type: ignore  # noqa: E402
import decode  # type: ignore  # noqa: E402


INVARIANT_TO_PRIMITIVE = {
    "I1_reduce_interpretation": "03 hard-numbers",
    "I2_no_rule_conflicts": "02 decision-ladders",
    "I3_motivated_reasoning": "09 reframe-as-signal",
    "I4_anti_narration": "08 anti-narration",
    "I5_example_rationale": "06 example-plus-rationale",
    "I6_failure_modes_explicit": "04 consequence-statement",
    "I7_namespace_balance": "01 namespace-blocks",
    "I8_default_exception": "04 default-plus-exception",
    "I9_self_check": "07 self-check-assertions",
    "I10_tier_labels": "hard-tier-labels (pattern)",
    "I11_hierarchical_override": "12 hierarchical-override",
}

INVARIANT_TO_FIX = {
    "I2_no_rule_conflicts": "ladder",
    "I3_motivated_reasoning": "reframe-guard",
    "I6_failure_modes_explicit": "consequences",
    "I8_default_exception": "defaults",
    "I9_self_check": "self-check",
    "I10_tier_labels": "tier-labels",
    "I11_hierarchical_override": "tier-labels",
}

TOOL_MENTION_RE = re.compile(
    r"\b(?:tool(?:s|_\w+)?|web_search|function|calls?|MCP|connector)\b",
    re.IGNORECASE,
)


def _infer_domain(report: audit.Report, text: str) -> dict[str, bool]:
    lines = text.splitlines()
    has_tools = any(TOOL_MENTION_RE.search(line) for line in lines)
    return {
        "has_tools": has_tools,
        "has_refusals": report.metrics["refusal_topic_signals"] >= 2,
        "has_examples": report.metrics["examples"] >= 1,
        "is_long": (
            report.metrics["directives"] >= 12
            or report.line_count > 100
        ),
        "has_conflicts": (
            report.metrics["refusal_topic_signals"] >= 2
            and report.metrics["directives"] >= 8
        ),
    }


def _required_invariants(domain: dict[str, bool]) -> set[str]:
    # Always required
    required = {
        "I1_reduce_interpretation",
        "I2_no_rule_conflicts",
        "I6_failure_modes_explicit",
        "I7_namespace_balance",
    }
    if domain["has_refusals"]:
        required.add("I3_motivated_reasoning")
        required.add("I10_tier_labels")
    if domain["has_conflicts"]:
        required.add("I11_hierarchical_override")
    if domain["is_long"]:
        required.add("I9_self_check")
    if domain["has_examples"]:
        required.add("I5_example_rationale")
    # I4 (anti-narration) and I8 (default+exception) are always applicable
    required.add("I4_anti_narration")
    required.add("I8_default_exception")
    return required


def plan(path: Path | None = None, text: str | None = None) -> dict:
    if text is None:
        assert path is not None
        text = path.read_text(encoding="utf-8")
        label = str(path)
    else:
        label = "<stdin>"

    report = audit.audit_text(text, source_label=label)
    decoded = decode.decode_text(text)
    domain = _infer_domain(report, text)
    required = _required_invariants(domain)

    missing = [
        inv for inv in required
        if not report.pass_flags.get(inv, True)
    ]
    passing_required = [
        inv for inv in required if report.pass_flags.get(inv, False)
    ]
    by_num = {d.number: d for d in decoded["detections"]}

    return {
        "path": label,
        "score": report.score,
        "domain": domain,
        "required_invariants": sorted(required),
        "missing_required": sorted(missing),
        "passing_required": sorted(passing_required),
        "primitive_detections": {
            num: det.confidence for num, det in by_num.items()
        },
        "report": report,
    }


def _format_human(result: dict) -> str:
    out = []
    out.append(f"path: {result['path']}")
    out.append(f"score: {result['score']}")
    out.append("")

    domain = result["domain"]
    domain_tags = [k for k, v in domain.items() if v]
    out.append(
        f"domain signals: {', '.join(domain_tags) if domain_tags else '(none)'}"
    )
    out.append(f"required invariants: {len(result['required_invariants'])}")
    out.append("")

    if not result["missing_required"]:
        out.append("✓ all required primitives present. nothing to add.")
    else:
        out.append("TODO — missing required primitives:")
        for inv in result["missing_required"]:
            fix_key = INVARIANT_TO_FIX.get(inv)
            fix_hint = (
                f"  (fix: fix.py --add {fix_key})" if fix_key else ""
            )
            out.append(
                f"  [ ] {inv}  → {INVARIANT_TO_PRIMITIVE[inv]}{fix_hint}"
            )

    out.append("")
    out.append("primitive coverage (all 12, not just required):")
    for num in sorted(result["primitive_detections"].keys()):
        conf = result["primitive_detections"][num]
        flag = "✓" if conf in {"high", "medium"} else " "
        out.append(f"  [{flag}] {num}  {conf}")

    return "\n".join(out)


def _format_json(result: dict) -> str:
    # Drop the non-serializable Report object.
    payload = {k: v for k, v in result.items() if k != "report"}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="opus-mind planner — completeness gap report"
    )
    parser.add_argument("path", help="prompt file to plan (use '-' for stdin)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
        if not text.strip():
            print("error: stdin is empty", file=sys.stderr)
            return 2
        result = plan(text=text)
    else:
        p = Path(args.path)
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
        try:
            result = plan(path=p)
        except UnicodeDecodeError:
            print(f"error: {p} is not valid UTF-8 text", file=sys.stderr)
            return 2

    print(_format_json(result) if args.json else _format_human(result))
    return 0 if not result["missing_required"] else 1


if __name__ == "__main__":
    sys.exit(main())
