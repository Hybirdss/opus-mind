#!/usr/bin/env python3
"""
opus-mind audit.py — deterministic system-prompt scorer.

Usage:
    python3 audit.py <prompt.md>              # full report
    python3 audit.py <prompt.md> --json       # machine-readable
    python3 audit.py <prompt.md> --stylebook  # add author's anti-slop list
    python3 audit.py --self                   # audit this skill's own SKILL.md

Grounding:
    Every signal set below is traceable to a specific line range in the
    Opus 4.7 source (CL4R1T4S mirror of Claude-Opus-4.7.txt). An author
    may also have opinionated anti-slop preferences; those live in
    `stylebook.py` and are opt-in via --stylebook so they don't pollute
    the Opus-4.7-grounded score.

    I1 reduce interpretation surface   — primitive 03, source L664 (15-word limit as numeric constant)
    I2 eliminate rule conflicts        — primitive 02, source L515-L537 (request_evaluation_checklist)
    I3 catch motivated reasoning       — primitive 09, source L33 (reframe as refusal signal)
    I4 keep internals private          — primitive 08, source L536, L560 (anti-narration)
    I5 calibrate through examples      — primitive 06, source L710-L750 (copyright examples with rationale)
    I6 make failure modes explicit     — technique 04, source L753-L759 (consequence block)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Opus 4.7-grounded signals only. Every item below is backed by a source line
# reference or a structural feature of the Opus 4.7 prompt.
# ---------------------------------------------------------------------------

# Narration phrases explicitly cited in Opus 4.7 as forbidden preambles.
# Source: line 536 (`"per my guidelines"`) and line 560 (`"let me load the
# diagram module"`). Every phrase here appears in the source as a NEGATIVE
# example — a phrase Claude should NOT emit.
NARRATION = [
    r"\blet me\b",              # L560: "No 'let me load the diagram module.'"
    r"\bper my guidelines\b",   # L536: "Claude doesn't say 'per my guidelines'"
]

# Hedge words that soften rules without adding a numeric constraint.
# Opus 4.7 does not publish a hedge blacklist; this list is the minimal
# intersection of (a) common English rule-softeners the prompt itself avoids
# when stating bright-line rules (see line 664 "15 words" vs "short quotes")
# and (b) words whose primary semantic job is to weaken a directive.
#
# NOTE: Opus 4.7 itself uses "generally", "often", "typically" in narrative
# passages. That is why the I1 threshold is a ratio, not an absolute count.
HEDGES = [
    r"\bprobably\b",
    r"\bmight\b",
    r"\bmay be\b",
    r"\bshould work\b",
    r"\bI think\b",
    r"\bwhen appropriate\b",
    r"\bif possible\b",
    r"\bperhaps\b",
]

LADDER_SIGNALS = [
    # Source line 515 opens the canonical decision-ladder block:
    # "Before producing any visual output, Claude walks these steps in
    # order, stopping at the first match." Patterns mirror that wording.
    r"Step\s*0\b", r"Step\s*1\b", r"first[- ]match[- ]wins",
    r"stop(?:s|ping)? at (?:the )?first match",
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

# ---------------------------------------------------------------------------
# Structural detectors for invariants I7-I13. The design goal here is to
# minimise word-level hardcoding — these detectors look at SHAPE, not
# vocabulary, so they generalize across languages and house styles.
# ---------------------------------------------------------------------------

# I11 — Tier labels (primitive-pattern "hard-tier-labels").
# Opus 4.7 emits tier labels as ALLCAPS multi-word tokens: "SEVERE VIOLATION"
# (L640), "HARD LIMIT" (L682), "NON-NEGOTIABLE" (L657), "ABSOLUTE LIMITS"
# (L678), "STRICT QUOTATION RULE" (L664). We detect any ≥2-word ALLCAPS
# token sequence whose tokens are length ≥ 3 (avoids "IS A" noise).
TIER_LABEL_RE = re.compile(
    r"\b[A-Z][A-Z0-9]{2,}(?:[ -][A-Z][A-Z0-9]{2,})+\b"
)

# I13 — Hierarchical override.
# Priority expressed structurally as either:
#   (a) two or more "Tier N" tokens in the doc, or
#   (b) a comparison-chain "X > Y > Z" with ≥ 3 operands, or
#   (c) "precedence over" / "takes precedence" (tight fallback phrase set).
TIER_TOKEN_RE = re.compile(r"\btier\s*[0-9]+\b", re.IGNORECASE)
PRIORITY_CHAIN_RE = re.compile(r"[A-Za-z][A-Za-z_/ ]{1,20}>\s*[A-Za-z][A-Za-z_/ ]{1,20}(?:\s*>\s*[A-Za-z][A-Za-z_/ ]{1,20})+")
PRECEDENCE_RE = re.compile(r"\b(?:takes? precedence|precedence over|non[- ]negotiable)\b", re.IGNORECASE)

# I10 — Self-check assertions.
# A self-check block has (a) a framing clause ("ask internally" / "before
# emit" / `{self_check}` xml tag) AND (b) a dense question cluster — ≥ 3
# question-ending lines within a 10-line window.
SELF_CHECK_FRAMING_RE = re.compile(
    r"(?:ask(?:s|ing)? (?:internally|itself)|before (?:emit|producing|returning|responding|sending|any (?:output|response))|self[- ]check|pre[- ]emit)",
    re.IGNORECASE,
)
# {self_check} xml block — structurally identical to any other namespace
# block, detected by name via XML_OPEN scan in _check_xml_balance.

# I8 — Default + exception.
# A default-plus-exception block has "default" and an exception keyword
# within a small window (same line or adjacent lines). We check windowed
# co-occurrence at line granularity so cross-paragraph drift counts.
DEFAULT_TOKEN_RE = re.compile(r"\bdefault(?:s|ed|ing)?\b", re.IGNORECASE)
EXCEPTION_TOKEN_RE = re.compile(
    r"\b(?:exception|unless|except|only when|only if|opt[- ]in)\b",
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


# Negators that, when present on the same line as a match, indicate the
# match is being FORBIDDEN — not practiced. "Claude doesn't say 'let me'"
# should not flag "let me" as narration.
NEGATOR_PATTERNS = [
    r"\bdoes not\b", r"\bdo not\b", r"\bdon't\b", r"\bdoesn't\b",
    r"\bnever\b", r"\bno longer\b", r"\bavoid(?:s|ing|ed)?\b",
    r"\bforbid(?:s|den|ding)?\b", r"\bprohibit(?:s|ed|ing)?\b",
    r"\brefuse(?:s|d|ing)?\b", r"\breject(?:s|ed|ing)?\b",
    r"\bwon't\b", r"\bwill not\b", r"\bmust not\b", r"\bshould not\b",
    r"\bcannot\b", r"\bcan't\b",
    r"^\s*-\s*no\b", r"^\s*No\s+[\"']",     # bullet "No 'X'"
    r"facilitates? (?:grooming|harm|illegal|abuse|bypass)",   # harm-list phrasing
    r"not (?:to |going to )?(?:facilitate|enable|help)",
]
_NEGATOR_RE = re.compile("|".join(NEGATOR_PATTERNS), re.IGNORECASE)

# Inline quoted counterexamples: `"let me..."` or `'per my guidelines'`.
# Anything inside matched quotes on a line is treated as illustrative,
# not practiced. Captures `"..."`, `'...'`, and backtick spans.
_QUOTE_SPAN_RE = re.compile(
    r'"[^"\n]{0,200}?"'       # double-quoted span
    r"|'[^'\n]{0,200}?'"       # single-quoted span
    r"|`[^`\n]{0,200}?`"       # backtick span
)


def _has_negator_context(line: str) -> bool:
    """True when the line scopes matches as forbidden, not practiced."""
    return bool(_NEGATOR_RE.search(line))


def _match_inside_quotes(line: str, match_start: int, match_end: int) -> bool:
    """True when the [match_start, match_end] span is inside any quoted span."""
    for m in _QUOTE_SPAN_RE.finditer(line):
        if m.start() < match_start and m.end() > match_end:
            return True
    return False


def _iter_findings(
    lines: list[str], patterns: Iterable[str], *, flags: int = 0,
) -> list[tuple[int, str, str]]:
    # Presence-only scan. Used for signals whose role is detection, not
    # violation: rationale markers, ladder signals, reframe clauses,
    # consequence phrases, refusal topics, example markers. A match still
    # counts even if the line is negated — "Claude declines requests…"
    # IS refusal-topic content we want to count.
    hits: list[tuple[int, str, str]] = []
    pat_list = list(patterns)
    for idx, line in enumerate(lines, start=1):
        for pat in pat_list:
            for m in re.finditer(pat, line, flags=flags):
                hits.append((idx, line.rstrip(), m.group(0)))
    return hits


def _iter_violations(
    lines: list[str], patterns: Iterable[str], *, flags: int = 0,
) -> list[tuple[int, str, str]]:
    # Violation scan. Used for signals that indicate the prompt PRACTICES
    # the bad behavior: slop words, hedges, narration phrases. A line that
    # forbids the bad behavior ("Claude does not say 'let me'") or that
    # cites the bad behavior as a counterexample inside quotes is NOT a
    # violation — suppress those matches.
    hits: list[tuple[int, str, str]] = []
    pat_list = list(patterns)
    for idx, line in enumerate(lines, start=1):
        negated = _has_negator_context(line)
        for pat in pat_list:
            for m in re.finditer(pat, line, flags=flags):
                if negated:
                    continue
                if _match_inside_quotes(line, m.start(), m.end()):
                    continue
                hits.append((idx, line.rstrip(), m.group(0)))
    return hits


def _stem_hits(lines: list[str], words: Iterable[str]) -> list[tuple[int, str, str]]:
    # Inflection-tolerant: utilize → utilizes, utilized, utilizing (1-3 letter suffix).
    patterns = [rf"\b{re.escape(w)}\w{{0,3}}\b" for w in words]
    return _iter_violations(lines, patterns, flags=re.IGNORECASE)


def _exact_hits(lines: list[str], words: Iterable[str]) -> list[tuple[int, str, str]]:
    # Exact word boundary — no inflection.
    patterns = [rf"\b{re.escape(w)}\b" for w in words]
    return _iter_violations(lines, patterns, flags=re.IGNORECASE)


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


def audit(path: Path, stylebook: bool = False) -> Report:
    text = path.read_text(encoding="utf-8")
    return audit_text(text, source_label=str(path), stylebook=stylebook)


def audit_text(
    text: str, source_label: str = "<text>", stylebook: bool = False
) -> Report:
    lines = text.splitlines()
    report = Report(path=source_label, line_count=len(lines))

    # --- raw counts ---
    hedges = _iter_violations(lines, HEDGES, flags=re.IGNORECASE)
    narration = _iter_violations(lines, NARRATION, flags=re.IGNORECASE)
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
    hedge_density = (
        len(hedges) / max(len(directives), 1) if directives else 0.0
    )

    # Optional: author's anti-slop stylebook. Opt-in via --stylebook.
    # Not grounded in Opus 4.7 — kept separate so the primary score
    # reflects the source-derived principles only.
    slop_metrics = {}
    if stylebook:
        try:
            from stylebook import SLOP_TIER1_STEM, SLOP_TIER1_EXACT, \
                SLOP_TIER2_STEM, SLOP_TIER2_EXACT
        except ImportError:
            SLOP_TIER1_STEM = SLOP_TIER1_EXACT = []
            SLOP_TIER2_STEM = SLOP_TIER2_EXACT = []
        slop1 = _stem_hits(lines, SLOP_TIER1_STEM) + _exact_hits(lines, SLOP_TIER1_EXACT)
        slop2 = _stem_hits(lines, SLOP_TIER2_STEM) + _exact_hits(lines, SLOP_TIER2_EXACT)
        slop2_flagged = [
            (ln, snip, match)
            for (ln, snip, match) in slop2
            if not NUMBER_CONSTRAINT.search(snip)
        ]
        slop_metrics = {
            "stylebook_tier1": len(slop1),
            "stylebook_tier2_no_number": len(slop2_flagged),
        }
        for ln, snip, match in slop1:
            report.findings.append(Finding(
                "stylebook", ln, snip, f"Tier 1 slop word: {match!r}",
                "skills/opus-mind/scripts/stylebook.py",
            ))
        for ln, snip, match in slop2_flagged:
            report.findings.append(Finding(
                "stylebook", ln, snip, f"Adj without number: {match!r}",
                "skills/opus-mind/scripts/stylebook.py",
            ))

    report.metrics = {
        "hedges": len(hedges),
        "hedge_density": round(hedge_density, 3),
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
        **slop_metrics,
    }

    # --- I1: reduce interpretation surface ---
    # Primitive 03 (hard numbers). The Opus 4.7 source uses hedges and
    # adjectives too — what it avoids is *unbacked rule-softening*. We
    # measure (a) hedge density and (b) numeric-constraint density relative
    # to directive count. Opus 4.7 itself measures hedge_density ≈ 0.16,
    # number_density ≈ 0.20. Thresholds are set above the source floor so
    # the source passes its own bar.
    i1_hedge_ok = report.metrics["hedge_density"] <= 0.25 or len(directives) < 3
    i1_number_ok = (
        report.metrics["number_density"] >= 0.10
        or len(directives) < 3
    )
    i1_pass = i1_hedge_ok and i1_number_ok
    report.pass_flags["I1_reduce_interpretation"] = i1_pass
    if not i1_hedge_ok:
        report.findings.append(Finding(
            "I1", 0, "",
            f"hedge_density {report.metrics['hedge_density']:.2f} > 0.25 "
            f"({len(hedges)} hedges / {len(directives)} directives)",
            "references/primitives/03-hard-numbers.md",
        ))
    if not i1_number_ok:
        report.findings.append(Finding(
            "I1", 0, "",
            f"number_density {report.metrics['number_density']:.2f} < 0.10 "
            f"({len(numbers)} numbers / {len(directives)} directives)",
            "references/primitives/03-hard-numbers.md",
        ))
    for ln, snip, match in hedges[:10]:
        report.findings.append(Finding(
            "I1_hint", ln, snip, f"Hedge word: {match!r}",
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

    # --- I7: namespace balance (primitive 01) ---
    # Every XML block that opens must close. Purely structural.
    # Only gates when the doc uses namespace blocks at all (xml_coverage > 0).
    i7_pass = (xml_coverage == 0) or (len(xml_unmatched) == 0)
    report.pass_flags["I7_namespace_balance"] = i7_pass
    if not i7_pass:
        for ln, snip in xml_unmatched[:5]:
            report.findings.append(Finding(
                "I7", ln, snip, "unmatched XML block",
                "references/primitives/01-namespace-blocks.md",
            ))

    # --- I8: default + exception (primitive 04) ---
    # A prompt with ≥ 6 directives should express at least one default/exception
    # pairing. Detected structurally: a line containing "default" with an
    # exception keyword in the same line or the next 3 lines.
    default_lines = {
        idx for idx, line in enumerate(lines, start=1)
        if DEFAULT_TOKEN_RE.search(line)
    }
    exception_lines = {
        idx for idx, line in enumerate(lines, start=1)
        if EXCEPTION_TOKEN_RE.search(line)
    }
    default_exception_pairs = sum(
        1 for d in default_lines
        if any(e for e in exception_lines if 0 <= (e - d) <= 3)
    )
    report.metrics["default_exception_pairs"] = default_exception_pairs
    needs_default = report.metrics["directives"] >= 6
    i8_pass = (not needs_default) or default_exception_pairs >= 1
    report.pass_flags["I8_default_exception"] = i8_pass
    if not i8_pass:
        report.findings.append(Finding(
            "I8", 0, "",
            f"{report.metrics['directives']} directives, no default+exception pair",
            "references/primitives/04-default-plus-exception.md",
        ))

    # --- I9: self-check assertions (primitive 07) ---
    # A long prompt (> 80 directive-bearing lines OR examples present) should
    # have a self-check block. Structural signature: either a {self_check}
    # xml block, OR a framing phrase ("ask internally", "before emit") with
    # a dense question cluster (≥3 question-ending lines within 10-line window).
    has_self_check_xml = any(
        XML_OPEN.match(line) and "self_check" in line.lower()
        for line in lines
    )
    framing_lines = [
        idx for idx, line in enumerate(lines, start=1)
        if SELF_CHECK_FRAMING_RE.search(line)
    ]
    question_lines = [
        idx for idx, line in enumerate(lines, start=1)
        if re.search(r"\?\s*$", line)
    ]
    question_cluster = False
    for fl in framing_lines:
        in_window = sum(1 for q in question_lines if 0 <= (q - fl) <= 10)
        if in_window >= 3:
            question_cluster = True
            break
    has_self_check = has_self_check_xml or question_cluster
    report.metrics["has_self_check"] = int(has_self_check)
    needs_self_check = (
        report.metrics["directives"] >= 12
        or report.metrics["examples"] >= 2
    )
    i9_pass = (not needs_self_check) or has_self_check
    report.pass_flags["I9_self_check"] = i9_pass
    if not i9_pass:
        report.findings.append(Finding(
            "I9", 0, "",
            f"{report.metrics['directives']} directives / "
            f"{report.metrics['examples']} examples, no self-check block",
            "references/primitives/07-self-check-assertions.md",
        ))

    # --- I10: tier labels (pattern: hard-tier-labels) ---
    # ALLCAPS multi-word tokens (≥2 words, ≥3 letters each). Opus 4.7 uses
    # these as compiler-directive-grade severity markers. Required when the
    # prompt carries "high-stakes" rules — proxied as: has refusal content
    # OR ≥ 8 directives.
    tier_labels = [
        (idx, line.rstrip(), m.group(0))
        for idx, line in enumerate(lines, start=1)
        for m in TIER_LABEL_RE.finditer(line)
    ]
    report.metrics["tier_labels"] = len(tier_labels)
    needs_tier_labels = (
        report.metrics["refusal_topic_signals"] >= 2
        or report.metrics["directives"] >= 8
    )
    i10_pass = (not needs_tier_labels) or len(tier_labels) >= 1
    report.pass_flags["I10_tier_labels"] = i10_pass
    if not i10_pass:
        report.findings.append(Finding(
            "I10", 0, "",
            "high-stakes content without ALLCAPS tier labels "
            "(e.g. SEVERE VIOLATION, HARD LIMIT, NON-NEGOTIABLE)",
            "references/patterns/hard-tier-labels.md",
        ))

    # --- I11: hierarchical override (primitive 12) ---
    # Priority expressed as (a) 2+ "Tier N" tokens, (b) comparison chain
    # X > Y > Z, or (c) precedence-language phrases. Needed when there
    # are multiple high-stakes categories (proxy: refusal content +
    # ≥ 8 directives, so rule collisions are likely).
    tier_tokens = len(TIER_TOKEN_RE.findall(text))
    priority_chains = len(PRIORITY_CHAIN_RE.findall(text))
    precedence_phrases = len(PRECEDENCE_RE.findall(text))
    report.metrics["priority_signals"] = (
        tier_tokens + priority_chains + precedence_phrases
    )
    needs_override = (
        report.metrics["refusal_topic_signals"] >= 2
        and report.metrics["directives"] >= 8
    )
    i11_pass = (not needs_override) or (
        tier_tokens >= 2 or priority_chains >= 1 or precedence_phrases >= 1
    )
    report.pass_flags["I11_hierarchical_override"] = i11_pass
    if not i11_pass:
        report.findings.append(Finding(
            "I11", 0, "",
            "refusal content with multiple rules, no explicit priority "
            "(tiers, X > Y > Z, or 'takes precedence over')",
            "references/primitives/12-hierarchical-override.md",
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
    parser.add_argument(
        "--stylebook", action="store_true",
        help="opt-in: also apply the author's anti-slop wordlist (not Opus 4.7-grounded)",
    )
    args = parser.parse_args()

    if args.self:
        target = Path(__file__).resolve().parent.parent / "SKILL.md"
        report = audit(target, stylebook=args.stylebook)
    elif args.path == "-":
        text = sys.stdin.read()
        if not text.strip():
            print("error: stdin is empty", file=sys.stderr)
            return 2
        report = audit_text(text, source_label="<stdin>", stylebook=args.stylebook)
    elif args.path:
        target = Path(args.path)
        if not target.exists():
            print(f"error: {target} not found", file=sys.stderr)
            return 2
        try:
            report = audit(target, stylebook=args.stylebook)
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
