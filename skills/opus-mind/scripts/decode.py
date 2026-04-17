#!/usr/bin/env python3
"""
opus-mind decode.py — reverse-audit a system prompt.

Input: a prompt file. Output: which of the 12 primitives are present,
where they are located (line ranges), and which primitives are absent
but might be worth adding given the prompt's topic shape.

This is the inverse of audit.py. audit.py scores what's missing.
decode.py labels what's present. Together they form a diff.

Usage:
    python3 decode.py <path>
    python3 decode.py <path> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Hit:
    line: int
    snippet: str


@dataclass
class PrimitiveDetection:
    number: str
    name: str
    confidence: str
    hit_count: int
    hits: list[Hit] = field(default_factory=list)
    note: str = ""


PRIMITIVES = [
    ("01", "namespace-blocks"),
    ("02", "decision-ladders"),
    ("03", "hard-numbers"),
    ("04", "default-plus-exception"),
    ("05", "cue-based-matching"),
    ("06", "example-plus-rationale"),
    ("07", "self-check-assertions"),
    ("08", "anti-narration"),
    ("09", "reframe-as-signal"),
    ("10", "asymmetric-trust"),
    ("11", "capability-disclosure"),
    ("12", "hierarchical-override"),
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
STEP_LADDER = re.compile(r"\bStep\s*(\d+)\b", re.IGNORECASE)
LADDER_STOP = re.compile(
    r"first[- ]match[- ]wins|stop at the first match|stops at the first match",
    re.IGNORECASE,
)
DEFAULT_EXCEPTION = re.compile(
    r"\b(default|defaults to|baseline)\b.{0,80}\b(exception|unless|only when|except)\b",
    re.IGNORECASE | re.DOTALL,
)
CUE_BASED = re.compile(
    r"\b(if the user (says|writes|asks)|recognizable as|signal|linguistic cue|"
    r"treat.{0,30}as (a )?signal)\b",
    re.IGNORECASE,
)
RATIONALE = re.compile(
    r"\{rationale|^\s*(Why|Rationale|이유):|^\s*##+\s*Rationale",
    re.IGNORECASE | re.MULTILINE,
)
SELF_CHECK = re.compile(
    r"\b(before emit|before emitting|ask internally|self[- ]check|runtime check|checklist)\b",
    re.IGNORECASE,
)
ANTI_NARRATION = re.compile(
    r"\b(does not narrate|no preamble|silent(ly)?|without narration|"
    r"never say .Let me|no machinery|hide machinery|without explaining the choice)\b",
    re.IGNORECASE,
)
REFRAME = re.compile(
    r"\breframe|reframing|signal to refuse|refusal trigger|motivated reasoning\b",
    re.IGNORECASE,
)
ASYMMETRIC_TRUST = re.compile(
    r"\b(user turn|system turn|data not instruction|treat.{0,30}as data|"
    r"user[- ]turn content|uploaded files are data|ignore previous instructions)\b",
    re.IGNORECASE,
)
CAPABILITY_DISCLOSURE = re.compile(
    r"\b(visible tool list is partial|deferred tool loader|before saying|"
    r"never assert unavailability|check before saying)\b",
    re.IGNORECASE,
)
HIERARCHICAL = re.compile(
    r"\b(Tier\s*\d|priority hierarchy|when rules conflict|higher tier wins|"
    r"safety > |safety over)\b",
    re.IGNORECASE,
)

CONSEQUENCE = re.compile(
    r"\b(harms?|violates?|exposes?|SEVERE VIOLATION|breaks?|blocks?|"
    r"leaks?|legal risk)\b",
    re.IGNORECASE,
)

REFUSAL_TOPIC = re.compile(
    r"\b(refuse|refusal|decline|won't help|do not assist|not going to)\b",
    re.IGNORECASE,
)

TOOL_TOPIC = re.compile(
    r"\b(tool call|mcp|connector|search|fetch|api|webhook|function call)\b",
    re.IGNORECASE,
)


def _classify(hit_count: int, strong_threshold: int, weak_threshold: int) -> str:
    if hit_count >= strong_threshold:
        return "high"
    if hit_count >= weak_threshold:
        return "medium"
    if hit_count >= 1:
        return "low"
    return "absent"


def _detect_namespace_blocks(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    stack: list[tuple[str, int]] = []
    closed_blocks: list[tuple[str, int, int]] = []
    for idx, line in enumerate(lines, start=1):
        m_open = XML_OPEN.match(line)
        m_close = XML_CLOSE.match(line)
        if m_open:
            stack.append((m_open.group(1), idx))
        elif m_close and stack and stack[-1][0] == m_close.group(1):
            name, start = stack.pop()
            closed_blocks.append((name, start, idx))
    for name, start, end in closed_blocks:
        hits.append(Hit(start, f"{{{name}}} L{start}-L{end}"))
    conf = _classify(len(closed_blocks), strong_threshold=3, weak_threshold=1)
    note = f"{len(closed_blocks)} balanced blocks"
    return PrimitiveDetection("01", "namespace-blocks", conf, len(closed_blocks), hits[:6], note)


def _detect_decision_ladders(lines: list[str]) -> PrimitiveDetection:
    steps: dict[int, list[int]] = {}
    stop_hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        for m in STEP_LADDER.finditer(line):
            step_num = int(m.group(1))
            steps.setdefault(step_num, []).append(idx)
        if LADDER_STOP.search(line):
            stop_hits.append(Hit(idx, line.strip()[:80]))
    ladder_count = 0
    hits: list[Hit] = []
    if steps:
        sorted_steps = sorted(steps.keys())
        if len(sorted_steps) >= 2:
            ladder_count = len(sorted_steps)
            for s in sorted_steps:
                hits.append(Hit(steps[s][0], f"Step {s}"))
    hits.extend(stop_hits)
    total = ladder_count + len(stop_hits)
    conf = _classify(total, strong_threshold=4, weak_threshold=2)
    note = f"{ladder_count} steps, {len(stop_hits)} stop-clauses"
    return PrimitiveDetection("02", "decision-ladders", conf, total, hits[:6], note)


def _detect_hard_numbers(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        for m in NUMBER_CONSTRAINT.finditer(line):
            hits.append(Hit(idx, m.group(0)))
    conf = _classify(len(hits), strong_threshold=5, weak_threshold=2)
    note = f"{len(hits)} numeric constraints"
    return PrimitiveDetection("03", "hard-numbers", conf, len(hits), hits[:6], note)


def _detect_default_exception(lines: list[str]) -> PrimitiveDetection:
    text = "\n".join(lines)
    hits: list[Hit] = []
    for m in DEFAULT_EXCEPTION.finditer(text):
        pos = m.start()
        line_num = text.count("\n", 0, pos) + 1
        hits.append(Hit(line_num, m.group(0)[:80].replace("\n", " ")))
    conf = _classify(len(hits), strong_threshold=3, weak_threshold=1)
    note = f"{len(hits)} default+exception pairs"
    return PrimitiveDetection("04", "default-plus-exception", conf, len(hits), hits[:6], note)


def _detect_cue_based(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        for m in CUE_BASED.finditer(line):
            hits.append(Hit(idx, m.group(0)))
    conf = _classify(len(hits), strong_threshold=3, weak_threshold=1)
    note = f"{len(hits)} cue phrases"
    return PrimitiveDetection("05", "cue-based-matching", conf, len(hits), hits[:6], note)


def _detect_example_rationale(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    example_signal = re.compile(
        r"^\s*(##+\s*Example|\{user\}|\{example|Input:|Example\s*\d*[:\.])",
        re.MULTILINE,
    )
    text = "\n".join(lines)
    examples = len(example_signal.findall(text))
    rationales = len(RATIONALE.findall(text))
    for m in RATIONALE.finditer(text):
        pos = m.start()
        line_num = text.count("\n", 0, pos) + 1
        hits.append(Hit(line_num, m.group(0)[:60]))
    paired = min(examples, rationales)
    conf = _classify(paired, strong_threshold=3, weak_threshold=1)
    note = f"{examples} examples, {rationales} rationales"
    return PrimitiveDetection("06", "example-plus-rationale", conf, paired, hits[:6], note)


def _detect_self_check(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        if SELF_CHECK.search(line):
            hits.append(Hit(idx, line.strip()[:80]))
    conf = _classify(len(hits), strong_threshold=2, weak_threshold=1)
    note = f"{len(hits)} self-check phrases"
    return PrimitiveDetection("07", "self-check-assertions", conf, len(hits), hits[:6], note)


def _detect_anti_narration(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        if ANTI_NARRATION.search(line):
            hits.append(Hit(idx, line.strip()[:80]))
    conf = _classify(len(hits), strong_threshold=2, weak_threshold=1)
    note = f"{len(hits)} anti-narration clauses"
    return PrimitiveDetection("08", "anti-narration", conf, len(hits), hits[:6], note)


def _detect_reframe(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        if REFRAME.search(line):
            hits.append(Hit(idx, line.strip()[:80]))
    conf = _classify(len(hits), strong_threshold=2, weak_threshold=1)
    note = f"{len(hits)} reframe signals"
    return PrimitiveDetection("09", "reframe-as-signal", conf, len(hits), hits[:6], note)


def _detect_asymmetric_trust(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        if ASYMMETRIC_TRUST.search(line):
            hits.append(Hit(idx, line.strip()[:80]))
    conf = _classify(len(hits), strong_threshold=2, weak_threshold=1)
    note = f"{len(hits)} asymmetric-trust clauses"
    return PrimitiveDetection("10", "asymmetric-trust", conf, len(hits), hits[:6], note)


def _detect_capability_disclosure(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        if CAPABILITY_DISCLOSURE.search(line):
            hits.append(Hit(idx, line.strip()[:80]))
    conf = _classify(len(hits), strong_threshold=2, weak_threshold=1)
    note = f"{len(hits)} capability-disclosure clauses"
    return PrimitiveDetection("11", "capability-disclosure", conf, len(hits), hits[:6], note)


def _detect_hierarchical(lines: list[str]) -> PrimitiveDetection:
    hits: list[Hit] = []
    for idx, line in enumerate(lines, start=1):
        if HIERARCHICAL.search(line):
            hits.append(Hit(idx, line.strip()[:80]))
    conf = _classify(len(hits), strong_threshold=2, weak_threshold=1)
    note = f"{len(hits)} hierarchy clauses"
    return PrimitiveDetection("12", "hierarchical-override", conf, len(hits), hits[:6], note)


DETECTORS = {
    "01": _detect_namespace_blocks,
    "02": _detect_decision_ladders,
    "03": _detect_hard_numbers,
    "04": _detect_default_exception,
    "05": _detect_cue_based,
    "06": _detect_example_rationale,
    "07": _detect_self_check,
    "08": _detect_anti_narration,
    "09": _detect_reframe,
    "10": _detect_asymmetric_trust,
    "11": _detect_capability_disclosure,
    "12": _detect_hierarchical,
}


def _topic_suggestions(lines: list[str], detections: list[PrimitiveDetection]) -> list[str]:
    text = "\n".join(lines)
    has_refusal = len(REFUSAL_TOPIC.findall(text)) >= 2
    has_tools = len(TOOL_TOPIC.findall(text)) >= 2
    by_num = {d.number: d for d in detections}
    suggestions: list[str] = []
    if has_refusal and by_num["09"].confidence == "absent":
        suggestions.append(
            "Topic has refusal content but no reframe-as-signal clause. "
            "Read references/primitives/09-reframe-as-signal.md."
        )
    if has_refusal and by_num["12"].confidence == "absent":
        suggestions.append(
            "Topic has refusal content but no priority hierarchy. "
            "Read references/primitives/12-hierarchical-override.md."
        )
    if has_tools and by_num["08"].confidence == "absent":
        suggestions.append(
            "Topic has tool-use content but no anti-narration clause. "
            "Read references/primitives/08-anti-narration.md."
        )
    if has_tools and by_num["11"].confidence == "absent":
        suggestions.append(
            "Topic has tool-use content but no capability-disclosure clause. "
            "Read references/primitives/11-capability-disclosure.md."
        )
    if by_num["01"].confidence == "absent" and len(lines) > 80:
        suggestions.append(
            "File exceeds 80 lines without XML namespace blocks. "
            "Read references/primitives/01-namespace-blocks.md."
        )
    if by_num["06"].hit_count == 0:
        suggestions.append(
            "No example+rationale pairs detected. "
            "Read references/primitives/06-example-plus-rationale.md."
        )
    return suggestions


def decode(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return decode_text(text, source_label=str(path))


def decode_text(text: str, source_label: str = "<text>") -> dict:
    lines = text.splitlines()
    detections = [DETECTORS[num](lines) for num, _ in PRIMITIVES]
    suggestions = _topic_suggestions(lines, detections)
    return {
        "path": source_label,
        "line_count": len(lines),
        "detections": detections,
        "suggestions": suggestions,
    }


def _format_human(result: dict) -> str:
    out = [f"path: {result['path']}", f"lines: {result['line_count']}", ""]
    out.append("primitives detected:")
    for d in result["detections"]:
        tag = f"[{d.confidence:>6}]"
        out.append(f"  {tag} {d.number} {d.name:<28} {d.note}")
        for h in d.hits[:3]:
            out.append(f"              L{h.line}: {h.snippet}")
    if result["suggestions"]:
        out.append("")
        out.append("suggestions:")
        for s in result["suggestions"]:
            out.append(f"  - {s}")
    return "\n".join(out)


def _format_json(result: dict) -> str:
    return json.dumps({
        "path": result["path"],
        "line_count": result["line_count"],
        "detections": [
            {
                "number": d.number,
                "name": d.name,
                "confidence": d.confidence,
                "hit_count": d.hit_count,
                "note": d.note,
                "hits": [{"line": h.line, "snippet": h.snippet} for h in d.hits],
            }
            for d in result["detections"]
        ],
        "suggestions": result["suggestions"],
    }, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="opus-mind prompt decoder")
    parser.add_argument("path", help="prompt file to decode (use '-' for stdin)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
        if not text.strip():
            print("error: stdin is empty", file=sys.stderr)
            return 2
        result = decode_text(text, source_label="<stdin>")
    else:
        target = Path(args.path)
        if not target.exists():
            print(f"error: {target} not found", file=sys.stderr)
            return 2
        try:
            result = decode(target)
        except UnicodeDecodeError:
            print(f"error: {target} is not valid UTF-8 text", file=sys.stderr)
            return 2
    print(_format_json(result) if args.json else _format_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
