"""
Tests for boost.py — the user-prompt coach.

Boost is NOT lint. It doesn't score against agent-design invariants;
it measures whether a user's request is specified enough AND whether
it invokes the reasoning techniques that improve answer quality.

10 slots in two layers:
    Specification (B1-B7): task, format, length, context, few_shot,
                           constraints, clarify
    Reasoning (B8-B10):    reasoning (CoT), verification, decomposition

Fixtures layout:
    boost/filled/    — complete prompts, coverage expected 10/10
    boost/empty/     — one-liners, coverage expected ≤ 2/10
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
    total = len(report.slots)
    assert not empty, (
        f"{path.name} expected {total}/{total} coverage, missing: {empty}. "
        f"evidence: {[(s, h.evidence) for s, h in report.slots.items()]}"
    )


@pytest.mark.parametrize("path", EMPTY, ids=lambda p: p.name)
def test_empty_fixtures_cover_almost_nothing(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    total = len(report.slots)
    # A one-liner should fill ≤ 2 slots (often just B1 task, sometimes B3 if
    # a number appears). Anything higher means our detectors are trigger-happy.
    assert report.filled_count <= 2, (
        f"{path.name} filled {report.filled_count}/{total} — too many false positives. "
        f"hits: {[(s, h.evidence) for s, h in report.slots.items() if h.filled]}"
    )


REASONING_FP_FIXTURES = sorted((FIXTURES / "partial").glob("reasoning-fp-*.txt"))


@pytest.mark.parametrize(
    "path", REASONING_FP_FIXTURES, ids=lambda p: p.name,
)
def test_reasoning_layer_no_false_positives(path: Path) -> None:
    """Imperative sequencing ('first X, then Y'), 'check' as a verb, and
    'for each <noun>' should NOT trigger the reasoning-layer slots.
    These prompts do real work but don't ASK for chain-of-thought,
    self-verification, or explicit decomposition."""
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    for slot in ("B8", "B9", "B10"):
        hit = report.slots[slot]
        assert not hit.filled, (
            f"{path.name}: {slot} {SLOT_LABEL_REMINDER.get(slot, '')} "
            f"false-positive — evidence {hit.evidence}. "
            f"Tighten the regex in boost.py."
        )


SLOT_LABEL_REMINDER = {
    "B8": "(reasoning)",
    "B9": "(verification)",
    "B10": "(decomposition)",
}


def test_partial_task_and_length_fills_B1_B3_only() -> None:
    """Canonical partial: 'Write a 300-word summary' hits task + length."""
    path = FIXTURES / "partial" / "task-and-length.txt"
    text = path.read_text(encoding="utf-8")
    report = boost.check(text, source_label=str(path))
    assert report.slots["B1"].filled, "B1 task should hit on 'Write a summary'"
    assert report.slots["B3"].filled, "B3 length should hit on '300-word'"
    # Other slots must stay empty on a pure task+length one-liner. B8-B10
    # (reasoning layer) also stay empty — a vague request for a summary
    # does not ask for chain-of-thought, verification, or decomposition.
    for slot in ["B2", "B5", "B6", "B7", "B8", "B9", "B10"]:
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
    # The answers block (the bulleted list following
    # "provided answers to the missing slots:") must only list slots
    # the user actually answered. Documentation sections that mention
    # "B1 task / B2 format / ..." live elsewhere in the template and
    # are allowed to reference slot names.
    marker = "provided answers to the missing slots:"
    assert marker in rendered, (
        f"expand template missing the answers marker — schema regression"
    )
    answers_block = rendered.split(marker, 1)[1].split("\n\n", 1)[0]
    for unanswered in ("B1", "B5", "B6", "B7"):
        assert unanswered not in answers_block, (
            f"answers block smuggled {unanswered} the user did not supply: "
            f"{answers_block!r}"
        )


def test_check_json_shape_stable() -> None:
    """JSON output must carry the stable keys downstream tools depend on."""
    import json
    text = "write 200 words about trees"
    report = boost.check(text)
    # Re-use the formatter
    payload = json.loads(boost._format_check_json(report))
    assert "coverage" in payload
    assert "filled_count" in payload
    # 10 slots — B1-B7 specification, B8-B10 reasoning.
    assert set(payload["slots"].keys()) == {
        "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
    }
    for slot_data in payload["slots"].values():
        assert "filled" in slot_data
        assert "evidence" in slot_data
        assert "suggestions" in slot_data


def test_fixture_counts() -> None:
    assert len(FILLED) >= 1, "need at least 1 filled fixture"
    assert len(EMPTY) >= 1, "need at least 1 empty fixture"
    assert len(PARTIAL) >= 1, "need at least 1 partial fixture"
