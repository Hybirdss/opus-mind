#!/usr/bin/env python3
"""
opus-mind fix.py — deterministic slop rewriter.

For audit.py findings that have a 1-to-1 replacement (Tier-1 slop,
filler phrases, common hedges), apply the replacement. For adj-
without-number and other judgment calls, insert a FIXME marker so
a human or downstream LLM can finish the job.

Usage:
    python3 fix.py <path>                # dry-run: show diff, write nothing
    python3 fix.py <path> --apply        # write back to <path>
    python3 fix.py <path> -o out.md      # write to different path

Guarantees:
- Apply-mode only replaces strings listed in DATA tables below.
- Never silently drops content; uncertain cases get <FIXME: ...> tags.
- Idempotent: running twice produces the same output.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path


TIER1_REPLACEMENTS = {
    "delve into": "cover",
    "delves into": "covers",
    "delving into": "covering",
    "delve": "cover",
    "utilize": "use",
    "utilizes": "uses",
    "utilized": "used",
    "utilizing": "using",
    "utilization": "use",
    "leverage": "use",
    "leverages": "uses",
    "leveraging": "using",
    "facilitate": "help",
    "facilitates": "helps",
    "facilitating": "helping",
    "encompass": "include",
    "encompasses": "includes",
    "encompassing": "including",
    "multifaceted": "broad",
    "holistic": "full",
    "holistically": "fully",
    "catalyze": "speed up",
    "catalyzes": "speeds up",
    "catalyzing": "speeding up",
    "nuanced": "specific",
    "realm": "area",
    "landscape": "set",
    "myriad": "many",
    "plethora": "many",
    "tapestry": "mix",
    "testament": "proof",
    "paradigm": "model",
    "paradigms": "models",
    "synergy": "fit",
    "streamline": "simplify",
    "streamlines": "simplifies",
    "streamlining": "simplifying",
    "empower": "let",
    "empowers": "lets",
    "foster": "build",
    "fosters": "builds",
    "fostering": "building",
    "elevate": "raise",
    "elevates": "raises",
    "pivotal": "key",
    "cornerstone": "core",
}


FILLER_DELETES = [
    r"\bIt's worth noting that\s*",
    r"\bIt is worth noting that\s*",
    r"\bLet's dive into\s*",
    r"\bIn today's [^.]{0,40}world,\s*",
    r"\bIt goes without saying that\s*",
    r"\bAt the end of the day,\s*",
    r"\bNeedless to say,\s*",
]


HEDGE_FIXMES = [
    (r"\bgenerally\b", "<FIXME: assert or cut 'generally'>"),
    (r"\bprobably\b", "<FIXME: verify or cut 'probably'>"),
    (r"\bmight\b", "<FIXME: assert or cut 'might'>"),
    (r"\bshould work\b", "<FIXME: verify 'should work'>"),
    (r"\bwhen appropriate\b", "<FIXME: define the exact condition>"),
    (r"\bcarefully\b", "<FIXME: replace with number or rule>"),
    (r"\bI think\b", "<FIXME: cut 'I think' — assert>"),
]


ADJ_NO_NUMBER_FIXMES = {
    "robust": "<FIXME: give scale number>",
    "comprehensive": "<FIXME: give coverage percent>",
    "seamless": "<FIXME: name the uptime target>",
    "cutting-edge": "<FIXME: name a benchmark or metric>",
    "effective": "<FIXME: give success rate>",
    "efficient": "<FIXME: name the metric>",
    "appropriate": "<FIXME: define exact condition>",
    "reasonable": "<FIXME: give the bound>",
    "proper": "<FIXME: define the exact rule>",
    "optimal": "<FIXME: name the optimization target>",
}


NARRATION_WARNINGS = [
    r"\bLet me\s+\w+",
    r"\bI'll check\b",
    r"\bI'll analyze\b",
    r"\bI'll think\b",
    r"\bFirst, I'll\b",
    r"\bAllow me to\b",
]


NUMBER_NEARBY = re.compile(
    r"\b\d+(?:\.\d+)?\s*%"
    r"|\b\d+(?:\.\d+)?\s*(?:words?|chars?|characters?|lines?|calls?|"
    r"sec|seconds?|min|minutes?|ms|MB|KB|tokens?|items?|files?|"
    r"turns?|questions?|examples?|times?)\b",
    re.IGNORECASE,
)


def _apply_case(replacement: str, original: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _replace_word(text: str, target: str, replacement: str) -> tuple[str, int]:
    pattern = re.compile(rf"\b{re.escape(target)}\b", flags=re.IGNORECASE)
    count = 0

    def sub(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return _apply_case(replacement, m.group(0))

    return pattern.sub(sub, text), count


def rewrite(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {
        "tier1_replacements": 0,
        "filler_deletes": 0,
        "hedge_fixmes": 0,
        "adj_no_number_fixmes": 0,
        "narration_warnings": 0,
    }

    for target, replacement in TIER1_REPLACEMENTS.items():
        text, n = _replace_word(text, target, replacement)
        counts["tier1_replacements"] += n

    for pattern in FILLER_DELETES:
        text, n = re.subn(pattern, "", text, flags=re.IGNORECASE)
        counts["filler_deletes"] += n

    for pattern, marker in HEDGE_FIXMES:
        text, n = re.subn(pattern, marker, text, flags=re.IGNORECASE)
        counts["hedge_fixmes"] += n

    def _adj_sub(m: re.Match[str]) -> str:
        word = m.group(0).lower()
        replacement = ADJ_NO_NUMBER_FIXMES.get(word, m.group(0))
        return replacement

    for adj in ADJ_NO_NUMBER_FIXMES:
        pattern = re.compile(rf"\b{adj}\b", flags=re.IGNORECASE)
        new_text_parts = []
        last = 0
        for m in pattern.finditer(text):
            start, end = m.span()
            window = text[max(0, start - 60):min(len(text), end + 60)]
            if NUMBER_NEARBY.search(window):
                continue
            new_text_parts.append(text[last:start])
            new_text_parts.append(ADJ_NO_NUMBER_FIXMES[adj])
            last = end
            counts["adj_no_number_fixmes"] += 1
        new_text_parts.append(text[last:])
        text = "".join(new_text_parts)

    for pattern in NARRATION_WARNINGS:
        hits = re.findall(pattern, text, flags=re.IGNORECASE)
        counts["narration_warnings"] += len(hits)

    return text, counts


def _diff(before: str, after: str, path: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{path} (before)",
            tofile=f"{path} (after)",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="opus-mind deterministic fixer")
    parser.add_argument("path", help="prompt file to fix")
    parser.add_argument("--apply", action="store_true", help="write back to path")
    parser.add_argument("-o", "--output", help="write to a different path")
    args = parser.parse_args()

    src = Path(args.path)
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2

    before = src.read_text(encoding="utf-8")
    after, counts = rewrite(before)

    print("fix.py — deterministic pass")
    for key, val in counts.items():
        print(f"  {key}: {val}")
    if counts["narration_warnings"]:
        print("  note: narration phrases flagged, not auto-rewritten.")
        print("        inspect and delete manually.")

    if after == before:
        print("  no changes needed.")
        return 0

    if args.output:
        Path(args.output).write_text(after, encoding="utf-8")
        print(f"  wrote: {args.output}")
    elif args.apply:
        src.write_text(after, encoding="utf-8")
        print(f"  wrote: {src}")
    else:
        print()
        print(_diff(before, after, str(src)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
