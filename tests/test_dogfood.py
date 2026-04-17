"""
Dogfood gate — the Opus 4.7 source MUST score 6/6 under this auditor.

Rationale:
    The entire repo's premise is "we reverse-engineered 12 primitives
    from the Opus 4.7 source, then built an auditor that enforces them."
    If the auditor fails the source, one of three things is wrong:
    (a) the regex is overfit to the author's taste, not the source;
    (b) a primitive was over-generalized beyond what the source practises;
    (c) CL4R1T4S drifted.

    This test makes (a) impossible to ship by accident. It fetches the
    source once, caches it, and asserts the score.

Network dependency:
    The test skips gracefully when offline. CI provides a fixture at
    /tmp/opus47.txt populated by a prior curl step. Set the env var
    OPUS_MIND_SOURCE_PATH to point at a pinned copy.

Run:
    python3 -m pytest tests/test_dogfood.py -v
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPTS = REPO / "skills" / "opus-mind" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit  # type: ignore  # noqa: E402

SOURCE_URL = (
    "https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/"
    "main/ANTHROPIC/Claude-Opus-4.7.txt"
)
CACHE = Path(os.environ.get("OPUS_MIND_SOURCE_PATH", "/tmp/opus47.txt"))


def _fetch_source() -> Path | None:
    if CACHE.exists() and CACHE.stat().st_size > 50_000:
        return CACHE
    try:
        with urllib.request.urlopen(SOURCE_URL, timeout=10) as resp:
            text = resp.read().decode("utf-8")
        CACHE.write_text(text, encoding="utf-8")
        return CACHE
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


@pytest.fixture(scope="module")
def opus47_path() -> Path:
    p = _fetch_source()
    if p is None:
        pytest.skip("Opus 4.7 source unavailable (offline, no cache)")
    return p


def test_opus47_scores_six_of_six(opus47_path: Path) -> None:
    report = audit.audit(opus47_path)
    failing = [k for k, v in report.pass_flags.items() if not v]
    assert not failing, (
        f"AUDITOR REGRESSION: Opus 4.7 source fails {failing}. "
        f"The auditor is no longer faithful to the primitives it claims "
        f"to extract. Score: {report.score}.\n"
        f"Metrics: {report.metrics}"
    )


def test_opus47_meets_calibration_floor(opus47_path: Path) -> None:
    report = audit.audit(opus47_path)
    # Thresholds mirror .opus-mind.json calibration block.
    assert report.metrics["narration"] == 0, \
        f"narration leak: {report.metrics['narration']}"
    assert report.metrics["numeric_constraints"] >= 30, \
        f"too few numeric constraints: {report.metrics['numeric_constraints']}"
    assert report.metrics["ladder_signals"] >= 3, \
        f"too few ladder signals: {report.metrics['ladder_signals']}"
    assert report.metrics["reframe_signals"] >= 1, \
        f"no reframe clause: {report.metrics['reframe_signals']}"
    assert report.metrics["consequences"] >= 10, \
        f"too few consequence statements: {report.metrics['consequences']}"
    assert report.metrics["hedge_density"] <= 0.25, \
        f"hedge density too high: {report.metrics['hedge_density']}"
    assert report.metrics["number_density"] >= 0.10, \
        f"number density too low: {report.metrics['number_density']}"


def test_opus47_stylebook_intentionally_fails(opus47_path: Path) -> None:
    # --stylebook intentionally flags the source — the stylebook is the
    # author's taste, not the source's principles. If stylebook passes
    # the source it means we accidentally stopped applying it.
    report = audit.audit(opus47_path, stylebook=True)
    hits = report.metrics.get("stylebook_tier1", 0) + \
           report.metrics.get("stylebook_tier2_no_number", 0)
    assert hits >= 5, (
        f"stylebook found only {hits} flags in the Opus 4.7 source. "
        f"Either the stylebook module is not loaded, or the lists have "
        f"been gutted to force a pass on the source."
    )
