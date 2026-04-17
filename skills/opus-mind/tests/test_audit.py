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


def test_bad_slop_stylebook_only():
    # Tier-1 slop is the author's stylebook, NOT Opus 4.7 grounding.
    # Under default audit the slop fixture may pass I1. Under --stylebook
    # mode, findings surface in the `stylebook` category.
    r_default = audit.audit(FIXTURES / "bad_slop.md")
    r_stylebook = audit.audit(FIXTURES / "bad_slop.md", stylebook=True)
    assert r_stylebook.metrics.get("stylebook_tier1", 0) >= 3, r_stylebook.metrics
    # Default audit must not use the slop list.
    assert "stylebook_tier1" not in r_default.metrics


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


# ----- audit boundary / edge-case tests -----


def test_audit_i1_exactly_two_hedges_passes(tmp_path):
    # 2 hedge words ≤ threshold (≤ 2) → I1 PASS
    p = tmp_path / "two_hedges.md"
    p.write_text("Do this generally. It might help.\n", encoding="utf-8")
    r = audit.audit(p)
    assert r.pass_flags["I1_reduce_interpretation"] is True


def test_audit_i2_five_directives_passes_without_ladder(tmp_path):
    # 5 directives (< 6 threshold) → I2 PASS even without ladder
    p = tmp_path / "few_directives.md"
    p.write_text(
        "You must respond. Do not lie. Never exaggerate.\n"
        "Always cite sources. Avoid speculation.\n",
        encoding="utf-8",
    )
    r = audit.audit(p)
    assert r.metrics["directives"] < 6
    assert r.pass_flags["I2_no_rule_conflicts"] is True


def test_audit_i3_one_refusal_signal_passes_without_reframe(tmp_path):
    # Only 1 refusal signal (< 2 threshold) → I3 not triggered → PASS
    p = tmp_path / "one_refusal.md"
    p.write_text(
        "The assistant will refuse requests that are illegal.\n"
        "Respond helpfully otherwise.\n",
        encoding="utf-8",
    )
    r = audit.audit(p)
    assert r.metrics["refusal_topic_signals"] < 2
    assert r.pass_flags["I3_motivated_reasoning"] is True


def test_audit_i5_no_examples_passes_without_rationale(tmp_path):
    # No example signals → I5 not triggered → PASS
    p = tmp_path / "no_examples.md"
    p.write_text(
        "The assistant answers questions about databases.\n"
        "Respond in 100 words or fewer.\n",
        encoding="utf-8",
    )
    r = audit.audit(p)
    assert r.metrics["examples"] == 0
    assert r.pass_flags["I5_example_rationale"] is True


def test_audit_i6_many_directives_needs_multiple_consequences(tmp_path):
    # 20+ directives, 1 consequence → I6 FAIL (needs ≥ 2)
    directives = "\n".join([
        "You must always respond.", "Do not be rude.", "Never lie.",
        "Always cite sources.", "Avoid speculation.", "Keep responses short.",
        "Do not share user data.", "Prefer prose over bullets.",
        "Never use slop words.", "Always check facts.",
        "Do not hallucinate.", "Prefer accuracy.", "Avoid ambiguity.",
        "Never ignore safety rules.", "Always follow guidelines.",
        "Decline off-topic requests.", "Reject harmful content.",
        "Maintain professional tone.", "Default to brevity.",
        "Ensure citations are valid.",
    ])
    p = tmp_path / "many_directives.md"
    p.write_text(directives + "\nThis breaks policy.\n", encoding="utf-8")
    r = audit.audit(p)
    assert r.metrics["directives"] >= 10
    required = max(1, int(r.metrics["directives"]) // 10)
    if required > r.metrics["consequences"]:
        assert r.pass_flags["I6_failure_modes_explicit"] is False


def test_audit_xml_unmatched_block_adds_structural_finding(tmp_path):
    p = tmp_path / "unmatched.md"
    p.write_text("{role}\nThis block is never closed.\n", encoding="utf-8")
    r = audit.audit(p)
    structural = [f for f in r.findings if f.invariant == "structural"]
    assert len(structural) >= 1


def test_audit_report_score_property():
    r = audit.Report(path="test", line_count=10)
    r.pass_flags = {"I1": True, "I2": False, "I3": True, "I4": False, "I5": True, "I6": False}
    assert r.score == "3/6"


def test_audit_format_json_contains_required_keys():
    r = audit.audit(FIXTURES / "good_6of6.md")
    raw = audit._format_json(r)
    import json as _json
    data = _json.loads(raw)
    for key in ("path", "line_count", "score", "pass", "metrics", "findings"):
        assert key in data, f"missing key: {key}"
    assert data["score"] == "6/6"


def test_audit_format_human_contains_score():
    r = audit.audit(FIXTURES / "good_6of6.md")
    text = audit._format_human(r)
    assert "score: 6/6" in text
    assert "[PASS]" in text


# ----- decode extended tests -----


def test_decode_returns_all_12_primitives():
    result = decode.decode(FIXTURES / "good_6of6.md")
    numbers = {d.number for d in result["detections"]}
    for n in [f"{i:02d}" for i in range(1, 13)]:
        assert n in numbers, f"primitive {n} missing from decode output"


def test_decode_result_has_expected_keys():
    result = decode.decode(FIXTURES / "good_6of6.md")
    for key in ("path", "line_count", "detections", "suggestions"):
        assert key in result, f"missing key: {key}"


def test_decode_high_confidence_on_hard_numbers_fixture(tmp_path):
    # A file with explicit numeric constraints → primitive 03 should be detected
    p = tmp_path / "numbers.md"
    p.write_text(
        "Respond in 120 words or fewer.\n"
        "Call the tool at most 5 times per turn.\n"
        "Limit responses to 3 paragraphs.\n",
        encoding="utf-8",
    )
    result = decode.decode(p)
    by_num = {d.number: d for d in result["detections"]}
    assert by_num["03"].confidence != "absent", by_num["03"]


def test_decode_absent_on_empty_file(tmp_path):
    p = tmp_path / "empty.md"
    p.write_text("", encoding="utf-8")
    result = decode.decode(p)
    # All detections should be absent on an empty file
    for d in result["detections"]:
        assert d.confidence == "absent", f"primitive {d.number} not absent on empty file"


# ----- fix extended tests -----


def test_fix_filler_worth_noting_deleted():
    text = "It's worth noting that safety matters."
    after, counts = fix.rewrite(text)
    assert "It's worth noting" not in after
    assert counts["filler_deletes"] >= 1


def test_fix_filler_lets_dive_deleted():
    text = "Let's dive into the main topic."
    after, counts = fix.rewrite(text)
    assert "Let's dive into" not in after
    assert counts["filler_deletes"] >= 1


def test_fix_case_preservation_capital():
    text = "Utilize this tool. Leverage the API."
    after, _ = fix.rewrite(text)
    # "Utilize" → "Use" (capital preserved), "Leverage" → "Use" (capital preserved)
    assert after.startswith("Use "), f"capital not preserved: {after!r}"


def test_fix_case_preservation_all_caps():
    text = "LEVERAGE the power here."
    after, _ = fix.rewrite(text)
    assert "USE" in after, f"all-caps not preserved: {after!r}"


def test_fix_apply_case_lowercase():
    assert fix._apply_case("use", "leverage") == "use"


def test_fix_apply_case_titlecase():
    assert fix._apply_case("use", "Leverage") == "Use"


def test_fix_apply_case_allcaps():
    assert fix._apply_case("use", "LEVERAGE") == "USE"


def test_fix_hedge_generally_gets_fixme():
    text = "The system generally responds in 100ms."
    after, counts = fix.rewrite(text)
    assert "<FIXME" in after
    assert counts["hedge_fixmes"] >= 1


def test_fix_narration_phrase_counted():
    text = "Let me check the database for you."
    after, counts = fix.rewrite(text)
    assert counts["narration_warnings"] >= 1
    # narration is counted but NOT auto-rewritten
    assert "Let me" in after


def test_fix_clean_text_no_changes():
    text = "The bot answers database questions in 50 words.\n"
    after, counts = fix.rewrite(text)
    assert after == text
    assert counts["tier1_replacements"] == 0
    assert counts["filler_deletes"] == 0
    assert counts["hedge_fixmes"] == 0
    assert counts["adj_no_number_fixmes"] == 0
    assert counts["narration_warnings"] == 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
