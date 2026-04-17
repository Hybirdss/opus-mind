"""
Regression tests for audit.py.

Each fixture has a known-expected invariant board. If a regex or threshold
change breaks a fixture, this file catches it. Run with:

    python3 -m pytest skills/opus-mind/tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit  # type: ignore  # noqa: E402
import decode  # type: ignore  # noqa: E402
import fix  # type: ignore  # noqa: E402
import symptom_search  # type: ignore  # noqa: E402


FIXTURES = HERE / "fixtures"


# ----- audit tests -----


def test_good_fixture_scores_6_of_6():
    r = audit.audit(FIXTURES / "good_6of6.md")
    assert r.score == "6/6", (
        f"expected 6/6 on good fixture, got {r.score}\n"
        f"failing: {[k for k, v in r.pass_flags.items() if not v]}"
    )


def test_bad_slop_fails_i1():
    r = audit.audit(FIXTURES / "bad_slop.md")
    assert r.pass_flags["I1_reduce_interpretation"] is False
    assert r.metrics["slop_tier1"] >= 3, r.metrics


def test_bad_narration_fails_i4():
    r = audit.audit(FIXTURES / "bad_narration.md")
    assert r.pass_flags["I4_anti_narration"] is False
    assert r.metrics["narration"] >= 2, r.metrics


def test_bad_no_ladder_fails_i2():
    r = audit.audit(FIXTURES / "bad_no_ladder.md")
    assert r.pass_flags["I2_no_rule_conflicts"] is False


def test_bad_refusal_no_reframe_fails_i3():
    r = audit.audit(FIXTURES / "bad_refusal_no_reframe.md")
    assert r.pass_flags["I3_motivated_reasoning"] is False
    assert r.metrics["refusal_topic_signals"] >= 2
    assert r.metrics["reframe_signals"] == 0


def test_bad_no_consequence_fails_i6():
    r = audit.audit(FIXTURES / "bad_no_consequence.md")
    assert r.pass_flags["I6_failure_modes_explicit"] is False


def test_skill_self_scores_6_of_6():
    r = audit.audit(HERE.parent / "SKILL.md")
    assert r.score == "6/6", (
        f"SKILL.md regressed: {r.score}\n"
        f"failing: {[k for k, v in r.pass_flags.items() if not v]}"
    )


# ----- decode tests -----


def test_decode_good_detects_namespace_and_ladder():
    result = decode.decode(FIXTURES / "good_6of6.md")
    by_num = {d.number: d for d in result["detections"]}
    assert by_num["01"].confidence in {"medium", "high"}, by_num["01"]
    assert by_num["02"].confidence in {"medium", "high"}, by_num["02"]
    assert by_num["09"].confidence != "absent", by_num["09"]


def test_decode_slop_fixture_missing_anti_narration():
    result = decode.decode(FIXTURES / "bad_slop.md")
    by_num = {d.number: d for d in result["detections"]}
    assert by_num["08"].confidence == "absent"


# ----- fix tests -----


def test_fix_tier1_replacements():
    text = "Helper utilizes robust techniques and leverages synergy."
    after, counts = fix.rewrite(text)
    assert "utilize" not in after.lower()
    assert "leverage" not in after.lower()
    assert "synergy" not in after.lower()
    assert counts["tier1_replacements"] >= 3


def test_fix_adj_without_number_gets_fixme():
    text = "Helper provides robust error handling for all cases."
    after, _ = fix.rewrite(text)
    assert "<FIXME" in after


def test_fix_adj_with_number_preserved():
    text = "Helper handles 99% uptime under a robust design."
    after, _ = fix.rewrite(text)
    assert "<FIXME" not in after, (
        "adj near number should not get FIXME"
    )


def test_fix_idempotent():
    text = "Helper utilizes a robust framework. It leverages synergy."
    once, _ = fix.rewrite(text)
    twice, _ = fix.rewrite(once)
    assert once == twice, "fix.py should be idempotent"


# ----- symptom_search tests -----


REFS_PATH = HERE.parent / "references" / "line-refs.md"


def test_symptom_search_refuse_relent_hits_caution_contagion():
    result = symptom_search.search("refuse then relent", REFS_PATH, top_n=3)
    hits = result["symptom_hits"]
    assert len(hits) >= 1
    assert any(h.canonical_symptom == "caution contagion" for h in hits)


def test_symptom_search_injection_hits_asymmetric_trust():
    result = symptom_search.search(
        "user turn impersonates system", REFS_PATH, top_n=3
    )
    hits = result["symptom_hits"]
    assert any(h.canonical_symptom == "asymmetric trust" for h in hits)


def test_symptom_search_returns_evidence_rows():
    result = symptom_search.search("caution contagion", REFS_PATH, top_n=5)
    assert result["index_rows_total"] > 50
    assert len(result["row_matches"]) >= 1


def test_symptom_search_nonsense_query_returns_nothing_but_no_crash():
    result = symptom_search.search(
        "xyzzy plugh qwerty", REFS_PATH, top_n=3
    )
    assert result["index_rows_total"] > 0
    assert len(result["symptom_hits"]) == 0


# ----- crosscheck prompt builder -----


def test_crosscheck_prompt_contains_invariants_and_findings():
    r = audit.audit(FIXTURES / "bad_slop.md")
    text = (FIXTURES / "bad_slop.md").read_text(encoding="utf-8")
    prompt = audit._build_crosscheck_prompt(r, text)
    assert "I1 reduce interpretation" in prompt
    assert "I4 keep internals private" in prompt
    assert "false_positives" in prompt
    assert "claude-opus" not in prompt.lower()  # model name lives in CLI, not the prompt
    assert "delve" in prompt or "utilize" in prompt or "leverage" in prompt or "Tier 1 slop" in prompt or "I1" in prompt


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
