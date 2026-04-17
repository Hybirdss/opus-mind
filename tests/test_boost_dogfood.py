"""
Dogfood gate for BOOST — fixtures sourced verbatim from Anthropic's
official prompt-engineering guide (docs.claude.com / docs.anthropic.com).

Rationale:
    BOOST claims to measure "specification quality" of user prompts.
    If canonical, officially-published "more effective" examples from
    Anthropic score 0/7 on our slot detector, our detector is wrong —
    it's not measuring what good spec actually looks like.

    The dogfood rule: complex, spec-complete examples must score ≥ 5/7.
    Short single-rule snippets (a one-line constraint, a one-line
    task) are NOT full prompts and are exempt — but we assert they
    still surface at least one correct slot so the detector isn't
    blind on legitimate shorter input.

Fixtures live at tests/fixtures/boost/dogfood/anthropic-*.txt. Each
file is a verbatim Anthropic-published canonical example, pulled from
the live docs. The file's filename encodes its expected class.

Complex fixtures (≥ 5/7 required):
    anthropic-multi-document.txt    multi-doc physician's-assistant with
                                    context + example format + clarify policy
    anthropic-explicit-action.txt   "Change this function" with example,
                                    explicit action, clarify on side effects

Snippet fixtures (≥ 1/7 required — i.e., at least one slot lights up):
    anthropic-analytics-dashboard.txt   "Create an analytics dashboard..."
                                        a task-only expansion example
    anthropic-tts-ellipses.txt          "Your response will be read aloud..."
                                        a constraint-only snippet

If Anthropic updates their guide and the fixtures drift, update the
fixtures and note the new URL / retrieval date in a comment at the
top of each file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPTS = REPO / "skills" / "opus-mind" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import boost  # type: ignore  # noqa: E402


FIXTURES = HERE / "fixtures" / "boost" / "dogfood"

COMPLEX_FIXTURES = [
    "anthropic-multi-document.txt",
    "anthropic-explicit-action.txt",
]

SNIPPET_FIXTURES = [
    "anthropic-analytics-dashboard.txt",
    "anthropic-tts-ellipses.txt",
]


@pytest.mark.parametrize("name", COMPLEX_FIXTURES)
def test_complex_anthropic_example_scores_at_least_five(name: str) -> None:
    """Canonical complex user prompts from Anthropic must score ≥ 5/7.

    Anything lower means BOOST's slot detectors are missing specification
    cues that the official docs treat as essential.
    """
    path = FIXTURES / name
    assert path.exists(), f"missing dogfood fixture: {name}"
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    assert report.filled_count >= 5, (
        f"{name} scored {report.filled_count}/7 — BOOST detector is failing "
        f"on a canonical 'more effective' prompt from the Anthropic docs.\n"
        f"filled: {[s for s, h in report.slots.items() if h.filled]}\n"
        f"empty:  {[s for s, h in report.slots.items() if not h.filled]}"
    )


@pytest.mark.parametrize("name", SNIPPET_FIXTURES)
def test_snippet_anthropic_example_surfaces_at_least_one_slot(name: str) -> None:
    """Short Anthropic 'more effective' snippets must light at least one slot.

    These aren't full prompts — they're rule fragments meant to be composed
    into a bigger prompt. But each demonstrates ONE specific slot being
    applied correctly (task expansion, constraint, etc.) — BOOST should
    surface that slot.
    """
    path = FIXTURES / name
    assert path.exists(), f"missing dogfood fixture: {name}"
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    assert report.filled_count >= 1, (
        f"{name} scored 0/7 — BOOST is blind on an Anthropic-canonical "
        f"snippet. The detector is failing on its narrowest use case."
    )


def test_empty_one_liner_scores_below_complex_minimum() -> None:
    """Empty one-liner must score strictly below the 5/7 complex floor.

    This asserts BOOST actually discriminates — complex prompts clear a
    bar that minimal one-liners cannot. Without this, the complex test
    could pass trivially on any input.
    """
    empty_path = HERE / "fixtures" / "boost" / "empty" / "one-liner.txt"
    if not empty_path.exists():
        pytest.skip("empty fixture missing")
    text = empty_path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(empty_path))
    assert report.filled_count < 5, (
        f"empty one-liner scored {report.filled_count}/7 — detector is "
        f"trigger-happy; cannot discriminate spec-complete from vague."
    )


def test_dogfood_fixtures_present() -> None:
    assert FIXTURES.is_dir(), "dogfood fixture directory missing"
    found = sorted(p.name for p in FIXTURES.glob("anthropic-*.txt"))
    expected = sorted(COMPLEX_FIXTURES + SNIPPET_FIXTURES)
    assert found == expected, (
        f"dogfood fixture set drifted.\nexpected: {expected}\nfound:    {found}"
    )
