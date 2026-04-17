"""
Tests for boost.py — the user-prompt coach.

Boost is NOT lint. It doesn't score against agent-design invariants;
it measures whether a user's request is specified enough to yield a
great answer. 7 slots: task, format, length, context, few_shot,
constraints, clarify.

Fixtures layout:
    boost/filled/    — spec-complete prompts, coverage expected 7/7
    boost/empty/     — one-liners, coverage expected ≤ 2/7
    boost/partial/   — mid-coverage prompts, with per-file expectations
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


FIXTURES = HERE / "fixtures" / "boost"
FILLED = sorted((FIXTURES / "filled").glob("*.txt"))
EMPTY = sorted((FIXTURES / "empty").glob("*.txt"))
PARTIAL = sorted((FIXTURES / "partial").glob("*.txt"))


@pytest.mark.parametrize("path", FILLED, ids=lambda p: p.name)
def test_filled_fixtures_cover_all_slots(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    empty = [s for s, h in report.slots.items() if not h.filled]
    assert not empty, (
        f"{path.name} expected 7/7 coverage, missing: {empty}. "
        f"evidence: {[(s, h.evidence) for s, h in report.slots.items()]}"
    )


@pytest.mark.parametrize("path", EMPTY, ids=lambda p: p.name)
def test_empty_fixtures_cover_almost_nothing(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    # A one-liner should fill ≤ 2 slots (often just B1 task, sometimes B3 if
    # a number appears). Anything higher means our detectors are trigger-happy.
    assert report.filled_count <= 2, (
        f"{path.name} filled {report.filled_count}/7 — too many false positives. "
        f"hits: {[(s, h.evidence) for s, h in report.slots.items() if h.filled]}"
    )


def test_partial_task_and_length_fills_B1_B3_only() -> None:
    """Canonical partial: 'Write a 300-word summary' hits task + length."""
    path = FIXTURES / "partial" / "task-and-length.txt"
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    assert report.slots["B1"].filled, "B1 task should hit on 'Write a summary'"
    assert report.slots["B3"].filled, "B3 length should hit on '300-word'"
    # Other slots must stay empty on a pure task+length one-liner.
    for slot in ["B2", "B5", "B6", "B7"]:
        assert not report.slots[slot].filled, (
            f"{slot} false positive on partial fixture: "
            f"{report.slots[slot].evidence}"
        )


def test_ask_returns_one_per_empty_slot() -> None:
    path = FIXTURES / "empty" / "one-liner.txt"
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    questions = boost.ask(report)
    empty_slots = [s for s, h in report.slots.items() if not h.filled]
    # Exactly one question per empty slot.
    question_slots = [q["slot"] for q in questions]
    assert set(question_slots) == set(empty_slots), (
        f"ask mismatch: questions={question_slots} empty={empty_slots}"
    )
    # Every question has a hint and a question text.
    for q in questions:
        assert q["question"]
        assert isinstance(q["hints"], list)


def test_expand_prompt_contains_original_and_answers() -> None:
    original = "write me a thing"
    answers = {
        "B2": "JSON",
        "B3": "50 lines",
        "B4": "for my team lead who hates jargon",
    }
    rendered = boost.build_expand_prompt(original, answers)
    assert original in rendered
    assert "JSON" in rendered
    assert "50 lines" in rendered
    assert "team lead" in rendered
    # Must not smuggle slots the user did not answer.
    assert "B1" not in rendered.split("answers to")[1] if "answers to" in rendered else True


def test_check_json_shape_stable() -> None:
    """JSON output must carry the stable keys downstream tools depend on."""
    import json
    text = "write 200 words about trees"
    report = boost.check(text)
    # Re-use the formatter
    payload = json.loads(boost._format_check_json(report))
    assert "coverage" in payload
    assert "filled_count" in payload
    assert set(payload["slots"].keys()) == {
        "B1", "B2", "B3", "B4", "B5", "B6", "B7"
    }
    for slot_data in payload["slots"].values():
        assert "filled" in slot_data
        assert "evidence" in slot_data
        assert "suggestions" in slot_data


def test_fixture_counts() -> None:
    assert len(FILLED) >= 1, "need at least 1 filled fixture"
    assert len(EMPTY) >= 1, "need at least 1 empty fixture"
    assert len(PARTIAL) >= 1, "need at least 1 partial fixture"
