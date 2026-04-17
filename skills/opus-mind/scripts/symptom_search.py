#!/usr/bin/env python3
"""
opus-mind symptom_search.py — symptom → source evidence.

Takes a natural-language description of a failure ("refuse then relent",
"model narrates tool calls", "user turn impersonates system") and returns
the best-matching rows from evidence/line-refs.md plus pointers to the
primitive and technique files that apply.

Usage:
    python3 symptom_search.py "refuse then relent"
    python3 symptom_search.py "tool call narration" --json
    python3 symptom_search.py "injection" -n 5

Index source: references/line-refs.md (parsed as markdown tables).
Pointer source: a static symptom → primitive table built from
methodology.md's failure-mode taxonomy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


SYMPTOM_TABLE: list[tuple[list[str], str, list[str]]] = [
    (
        ["refuse then relent", "caution contagion", "refuses once",
         "soft follow-up", "relents on follow-up", "relents later",
         "weakens caution"],
        "caution contagion",
        ["primitives/09-reframe-as-signal.md", "techniques/03-caution-contagion.md"],
    ),
    (
        ["reframe", "motivated reasoning", "sanitizing request",
         "refusal reframed", "sanitization impulse"],
        "reframe-as-signal",
        ["primitives/09-reframe-as-signal.md"],
    ),
    (
        ["adj drift", "adjective drift", "vague constraint",
         "rule weakens", "constraint loosens", "short but not short enough"],
        "hard numbers",
        ["primitives/03-hard-numbers.md"],
    ),
    (
        ["narration", "let me check", "preamble", "meta-commentary",
         "talks about the tool", "explains the choice",
         "announces the tool call"],
        "anti-narration",
        ["primitives/08-anti-narration.md"],
    ),
    (
        ["rule conflict", "rules contradict", "picks vibes",
         "inconsistent behavior", "which rule wins"],
        "decision ladders",
        ["primitives/02-decision-ladders.md"],
    ),
    (
        ["unscoped", "rules everywhere", "single big list",
         "nested rules", "no sections"],
        "namespace blocks",
        ["primitives/01-namespace-blocks.md"],
    ),
    (
        ["injection", "impersonate system", "user pretends system",
         "ignore previous instructions", "override via user turn"],
        "asymmetric trust",
        ["primitives/10-asymmetric-trust.md", "techniques/05-injection-defense-in-band.md"],
    ),
    (
        ["denies capability", "says cannot", "assumes no tool",
         "gives up before searching", "doesn't try the tool"],
        "capability disclosure",
        ["primitives/11-capability-disclosure.md"],
    ),
    (
        ["safety loses", "priority unclear", "what wins",
         "tier confusion", "override hierarchy"],
        "hierarchical override",
        ["primitives/12-hierarchical-override.md"],
    ),
    (
        ["rephrased attack", "rule survives rephrase",
         "consequence missing", "harm unstated"],
        "consequence statement",
        ["techniques/04-consequence-statement.md"],
    ),
    (
        ["rationalizes out of rule", "category matching",
         "argues around the rule"],
        "category match",
        ["primitives/07-self-check-assertions.md", "techniques/07-category-match.md"],
    ),
    (
        ["surprising behavior", "forgot to forbid",
         "not covered by rule", "edge case missed"],
        "negative space",
        ["primitives/04-default-plus-exception.md", "techniques/06-negative-space.md"],
    ),
    (
        ["stale facts", "knows old version", "didn't search",
         "prior knowledge won over search", "tool skipped"],
        "force tool call",
        ["techniques/01-force-tool-call.md"],
    ),
    (
        ["quote too long", "copyright creep", "long verbatim",
         "multi-quote per source", "same source quoted twice"],
        "paraphrase with numeric limits",
        ["techniques/02-paraphrase-with-numeric-limits.md"],
    ),
]


STOPWORDS = {
    "the", "a", "an", "to", "of", "in", "on", "and", "or", "is", "are",
    "was", "were", "be", "been", "being", "it", "its", "this", "that",
    "these", "those", "then", "when", "if", "not", "no", "at", "by",
    "for", "with", "from", "about", "as", "but",
}


@dataclass
class IndexRow:
    concept: str
    lines: str
    paraphrase: str
    source_file: str


@dataclass
class Match:
    row: IndexRow
    score: float
    matched_tokens: list[str]


@dataclass
class SymptomHit:
    alias_matched: list[str]
    canonical_symptom: str
    pointers: list[str]


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9가-힣]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 2]


def _load_index(refs_path: Path) -> list[IndexRow]:
    rows: list[IndexRow] = []
    row_pattern = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
    for line in refs_path.read_text(encoding="utf-8").splitlines():
        m = row_pattern.match(line)
        if not m:
            continue
        concept, lines_ref, paraphrase = m.groups()
        if concept.lower().startswith("claim") or "---" in concept:
            continue
        rows.append(IndexRow(
            concept=concept.strip(),
            lines=lines_ref.strip(),
            paraphrase=paraphrase.strip(),
            source_file=str(refs_path.name),
        ))
    return rows


def _score_row(query_tokens: set[str], row: IndexRow) -> tuple[float, list[str]]:
    row_text = f"{row.concept} {row.paraphrase}".lower()
    row_tokens = set(_tokenize(row_text))
    if not row_tokens:
        return 0.0, []
    matched = sorted(query_tokens & row_tokens)
    if not matched:
        return 0.0, []
    overlap = len(matched) / max(len(query_tokens), 1)
    concept_bonus = 0.0
    for t in matched:
        if t in _tokenize(row.concept):
            concept_bonus += 0.25
    return overlap + concept_bonus, matched


def _symptom_table_hits(query: str) -> list[SymptomHit]:
    q_lower = query.lower()
    q_tokens = set(_tokenize(query))
    hits: list[SymptomHit] = []
    for aliases, canonical, pointers in SYMPTOM_TABLE:
        matched_aliases: list[str] = []
        for alias in aliases:
            if alias in q_lower:
                matched_aliases.append(alias)
                continue
            alias_tokens = set(_tokenize(alias))
            if alias_tokens and alias_tokens.issubset(q_tokens):
                matched_aliases.append(alias)
                continue
            if alias_tokens and len(alias_tokens & q_tokens) >= 2:
                matched_aliases.append(alias)
        if matched_aliases:
            hits.append(SymptomHit(
                alias_matched=matched_aliases,
                canonical_symptom=canonical,
                pointers=pointers,
            ))
    return hits


def search(query: str, refs_path: Path, top_n: int = 3) -> dict:
    rows = _load_index(refs_path)
    q_tokens = set(_tokenize(query))
    scored: list[Match] = []
    for row in rows:
        score, matched = _score_row(q_tokens, row)
        if score > 0:
            scored.append(Match(row=row, score=score, matched_tokens=matched))
    scored.sort(key=lambda m: m.score, reverse=True)
    top = scored[:top_n]
    symptom_hits = _symptom_table_hits(query)
    return {
        "query": query,
        "row_matches": top,
        "symptom_hits": symptom_hits,
        "index_rows_total": len(rows),
    }


def _format_human(result: dict) -> str:
    out = [f"query: {result['query']}", f"indexed: {result['index_rows_total']} rows", ""]
    if result["symptom_hits"]:
        out.append("symptom table matches:")
        for h in result["symptom_hits"]:
            aliases = ", ".join(h.alias_matched)
            out.append(f"  canonical: {h.canonical_symptom}")
            out.append(f"  matched:   {aliases}")
            for p in h.pointers:
                out.append(f"  read:      references/{p}")
            out.append("")
    if result["row_matches"]:
        out.append(f"top {len(result['row_matches'])} evidence rows:")
        for m in result["row_matches"]:
            out.append(
                f"  [{m.score:.2f}] source L{m.row.lines} — {m.row.concept}"
            )
            out.append(f"         > {m.row.paraphrase}")
            out.append(f"         tokens: {', '.join(m.matched_tokens)}")
    else:
        out.append("no evidence row matched. try broader keywords.")
    return "\n".join(out)


def _format_json(result: dict) -> str:
    return json.dumps({
        "query": result["query"],
        "indexed_rows": result["index_rows_total"],
        "symptom_hits": [
            {
                "canonical": h.canonical_symptom,
                "aliases_matched": h.alias_matched,
                "pointers": h.pointers,
            }
            for h in result["symptom_hits"]
        ],
        "row_matches": [
            {
                "score": round(m.score, 3),
                "concept": m.row.concept,
                "lines": m.row.lines,
                "paraphrase": m.row.paraphrase,
                "tokens_matched": m.matched_tokens,
            }
            for m in result["row_matches"]
        ],
    }, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="opus-mind symptom-to-evidence search")
    parser.add_argument("query", help="natural-language symptom description")
    parser.add_argument("-n", "--top", type=int, default=3, help="top N evidence rows")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--refs",
        help="path to line-refs.md (default: references/line-refs.md)",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    refs_path = Path(args.refs) if args.refs else (here.parent / "references" / "line-refs.md")
    if not refs_path.exists():
        print(f"error: {refs_path} not found", file=sys.stderr)
        return 2

    result = search(args.query, refs_path, top_n=args.top)
    print(_format_json(result) if args.json else _format_human(result))
    found = bool(result["row_matches"] or result["symptom_hits"])
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
