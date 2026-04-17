"""
Tests for draft.py — _render, _load_answers, QUESTIONS coverage.

Run with:
    python3 -m pytest skills/opus-mind/tests/test_draft.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import draft  # type: ignore  # noqa: E402


FULL_ANSWERS = {
    "product_name": "AcmeBot",
    "assistant_name": "Acme",
    "role_one_line": "a customer support agent",
    "mission": "Answer questions about orders and returns.",
    "modal_user": "a shopper who placed an order",
    "modal_request": "order status checks",
    "refusal_criterion": "the request involves illegal activity",
    "tier1_never": "doxxing, CSAM, weapon synthesis",
    "default_length_words": "120",
    "tool_list": "order_lookup, refund_request",
    "facts_that_change": "order status, delivery dates",
    "top_violated_rules": "no speculation, cite sources, refuse CSAM",
}


def test_render_full_answers_contains_product_name():
    result = draft._render(FULL_ANSWERS)
    assert "AcmeBot" in result


def test_render_full_answers_contains_assistant_name():
    result = draft._render(FULL_ANSWERS)
    assert "Acme" in result


def test_render_full_answers_contains_mission():
    result = draft._render(FULL_ANSWERS)
    assert "Answer questions about orders and returns." in result


def test_render_full_answers_contains_tier1_never():
    result = draft._render(FULL_ANSWERS)
    assert "doxxing, CSAM, weapon synthesis" in result


def test_render_full_answers_contains_tool_list():
    result = draft._render(FULL_ANSWERS)
    assert "order_lookup, refund_request" in result


def test_render_fixme_placeholder_answer_appears_in_output():
    answers = dict(FULL_ANSWERS)
    answers["mission"] = "<FIXME: mission>"
    result = draft._render(answers)
    assert "<FIXME: mission>" in result


def test_render_returns_string():
    result = draft._render(FULL_ANSWERS)
    assert isinstance(result, str)
    assert len(result) > 200


def test_render_skeleton_has_all_section_blocks():
    result = draft._render(FULL_ANSWERS)
    for block in ("{role}", "{priority_hierarchy}", "{refusal_handling}",
                  "{output_routing}", "{self_check}", "{examples}"):
        assert block in result, f"missing block: {block}"


def test_load_answers_happy_path(tmp_path):
    data = {k: f"val_{k}" for k, _ in draft.QUESTIONS}
    p = tmp_path / "answers.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    answers = draft._load_answers(p)
    for key, _ in draft.QUESTIONS:
        assert answers[key] == f"val_{key}", f"key {key!r} wrong"


def test_load_answers_missing_key_returns_fixme(tmp_path):
    p = tmp_path / "partial.json"
    p.write_text(json.dumps({"product_name": "X"}), encoding="utf-8")
    answers = draft._load_answers(p)
    for key, _ in draft.QUESTIONS:
        if key == "product_name":
            assert answers[key] == "X"
        else:
            assert answers[key] == f"<FIXME: {key}>"


def test_load_answers_all_keys_present(tmp_path):
    p = tmp_path / "full.json"
    p.write_text(json.dumps({}), encoding="utf-8")
    answers = draft._load_answers(p)
    for key, _ in draft.QUESTIONS:
        assert key in answers, f"key {key!r} not in loaded answers"


def test_questions_has_12_entries():
    assert len(draft.QUESTIONS) == 12


def test_questions_keys_are_unique():
    keys = [k for k, _ in draft.QUESTIONS]
    assert len(keys) == len(set(keys)), "duplicate question keys"


if __name__ == "__main__":
    import pytest as _pytest
    import sys as _sys
    _sys.exit(_pytest.main([__file__, "-v"]))
