#!/usr/bin/env python3
"""
opus-mind benchmark.py — living leaderboard for public system prompts.

Pulls a curated set of leaked system prompts from the CL4R1T4S archive,
scores each with audit.py, and prints a markdown table that can be
pasted directly into README.md or posted to a blog.

Designed to run in CI on a weekly schedule:
    - fresh scores track model updates as vendors refresh prompts
    - the table becomes content — "this week Cursor's prompt dropped
      to 5/11 after their 2.3 rewrite" is viral material

Usage:
    python3 benchmark.py                  # human-readable table
    python3 benchmark.py --json           # structured JSON
    python3 benchmark.py --update-readme  # patch README.md's live table
    python3 benchmark.py --offline CACHE  # read from local dir instead

Every target is a tuple (label, cl4r1t4s-path). Add new leaks by
appending to TARGETS — the fetch + score pipeline runs over them
uniformly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit  # type: ignore  # noqa: E402


# CL4R1T4S mirror — the canonical leak archive. Every entry below
# resolves to a raw.githubusercontent URL when combined with the
# BASE_URL template.
BASE_URL = "https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/main/"

# (display_label, path_in_archive). Paths may contain spaces and
# require URL-encoding; we handle that in _fetch.
TARGETS: list[tuple[str, str]] = [
    ("Claude Opus 4.7",          "ANTHROPIC/Claude-Opus-4.7.txt"),
    ("Claude Code (Mar 2024)",   "ANTHROPIC/Claude_Code_03-04-24.md"),
    ("Cursor Prompt",            "CURSOR/Cursor_Prompt.md"),
    ("ChatGPT-5 (Aug 2025)",     "OPENAI/ChatGPT5-08-07-2025.mkd"),
    ("ChatGPT Personality v2",   "OPENAI/ChatGPT_Personality_v2_Change.md"),
]


@dataclass
class BenchmarkRow:
    label: str
    archive_path: str
    fetched_bytes: int
    score: str
    verdict: str
    failing: list[str]
    error: str | None = None

    @property
    def source_url(self) -> str:
        return (
            "https://github.com/elder-plinius/CL4R1T4S/blob/main/"
            + urllib.parse.quote(self.archive_path)
        )


def _fetch(archive_path: str, timeout: float = 15.0) -> str | None:
    url = BASE_URL + urllib.parse.quote(archive_path)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def _read_local(root: Path, archive_path: str) -> str | None:
    candidate = root / archive_path
    if not candidate.exists():
        return None
    try:
        return candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _score_text(label: str, archive_path: str, text: str) -> BenchmarkRow:
    if not text.strip():
        return BenchmarkRow(
            label=label, archive_path=archive_path, fetched_bytes=0,
            score="-", verdict="-", failing=[],
            error="empty body",
        )
    report = audit.audit_text(text, source_label=label)
    failing = sorted(
        k.split("_")[0] for k, v in report.pass_flags.items() if not v
    )
    return BenchmarkRow(
        label=label,
        archive_path=archive_path,
        fetched_bytes=len(text.encode("utf-8")),
        score=report.score,
        verdict=report.verdict,
        failing=failing,
    )


def run(offline_root: Path | None = None) -> list[BenchmarkRow]:
    rows: list[BenchmarkRow] = []
    for label, archive_path in TARGETS:
        text: str | None
        if offline_root:
            text = _read_local(offline_root, archive_path)
            if text is None:
                rows.append(BenchmarkRow(
                    label=label, archive_path=archive_path, fetched_bytes=0,
                    score="-", verdict="-", failing=[],
                    error=f"not in cache {offline_root}",
                ))
                continue
        else:
            text = _fetch(archive_path)
            if text is None:
                rows.append(BenchmarkRow(
                    label=label, archive_path=archive_path, fetched_bytes=0,
                    score="-", verdict="-", failing=[],
                    error="fetch failed (network or 404)",
                ))
                continue
        rows.append(_score_text(label, archive_path, text))
    return rows


def format_markdown(rows: list[BenchmarkRow], when: str) -> str:
    out: list[str] = []
    out.append(f"### Live benchmark — {when}")
    out.append("")
    out.append(
        "Every row re-scored from the CL4R1T4S raw source. Invariants "
        "that do not apply to short prompts (I9 self-check, I10 tier "
        "labels) naturally keep shorter prompts below 11/11 even when "
        "they are well-written for their scope."
    )
    out.append("")
    out.append("| Source | Score | Verdict | Bytes | Chief gaps |")
    out.append("|---|---|---|---|---|")
    for r in rows:
        if r.error:
            out.append(
                f"| [{r.label}]({r.source_url}) | — | — | — | fetch error: {r.error} |"
            )
            continue
        gaps = (
            ", ".join(r.failing[:5])
            + (f" (+{len(r.failing) - 5} more)" if len(r.failing) > 5 else "")
        ) or "—"
        out.append(
            f"| [{r.label}]({r.source_url}) | **{r.score}** | {r.verdict} | "
            f"{r.fetched_bytes:,} | {gaps} |"
        )
    out.append("")
    out.append(
        "Reproduce with `python3 skills/opus-mind/scripts/benchmark.py`."
    )
    return "\n".join(out)


def format_json(rows: list[BenchmarkRow], when: str) -> str:
    payload = {
        "generated_at": when,
        "base_url": BASE_URL,
        "rows": [
            {
                "label": r.label,
                "archive_path": r.archive_path,
                "source_url": r.source_url,
                "fetched_bytes": r.fetched_bytes,
                "score": r.score,
                "verdict": r.verdict,
                "failing": r.failing,
                "error": r.error,
            }
            for r in rows
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# Marker tokens in README.md that bracket the auto-updatable block.
# Anything between these lines is overwritten by --update-readme.
README_MARKER_BEGIN = "<!-- benchmark:begin -->"
README_MARKER_END = "<!-- benchmark:end -->"


def patch_readme(readme_path: Path, table_md: str) -> bool:
    if not readme_path.exists():
        return False
    original = readme_path.read_text(encoding="utf-8")
    if README_MARKER_BEGIN not in original or README_MARKER_END not in original:
        # Markers absent — skip silently. The benchmark table is still
        # valid output; inserting it is the maintainer's call.
        return False
    head, rest = original.split(README_MARKER_BEGIN, 1)
    _, tail = rest.split(README_MARKER_END, 1)
    block = (
        README_MARKER_BEGIN + "\n\n" + table_md + "\n\n" + README_MARKER_END
    )
    readme_path.write_text(head + block + tail, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Score a curated set of public system prompts against the "
            "opus-mind auditor. Produces a living leaderboard suitable "
            "for README.md or a weekly CI artefact."
        )
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--update-readme", action="store_true",
        help=(
            "overwrite the <!-- benchmark:begin --> ... <!-- benchmark:end --> "
            "block in README.md with the fresh table"
        ),
    )
    parser.add_argument(
        "--offline",
        help=(
            "read targets from a local directory that mirrors the CL4R1T4S "
            "layout (ANTHROPIC/, CURSOR/, OPENAI/ ...) instead of fetching "
            "over HTTPS. Useful for sandboxed CI or reproducible runs."
        ),
    )
    args = parser.parse_args()

    offline_root: Path | None = None
    if args.offline:
        offline_root = Path(args.offline)
        if not offline_root.is_dir():
            print(f"error: --offline path not a directory: {offline_root}",
                  file=sys.stderr)
            return 2

    when = time.strftime("%Y-%m-%d", time.gmtime())
    rows = run(offline_root=offline_root)

    if args.json:
        print(format_json(rows, when))
    else:
        print(format_markdown(rows, when))

    if args.update_readme:
        repo_root = HERE.parent.parent.parent
        readme = repo_root / "README.md"
        table = format_markdown(rows, when)
        ok = patch_readme(readme, table)
        if ok:
            print(
                f"\n[update-readme] patched {readme}", file=sys.stderr,
            )
        else:
            print(
                f"\n[update-readme] no marker block in {readme}; skipped.\n"
                f"                 add these two lines to enable:\n"
                f"                   {README_MARKER_BEGIN}\n"
                f"                   {README_MARKER_END}",
                file=sys.stderr,
            )

    # Exit non-zero only when every target errored — partial runs still
    # produce a usable table (weekly CI shouldn't red-build on a single
    # archive URL change).
    if rows and all(r.error for r in rows):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
