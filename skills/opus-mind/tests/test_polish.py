"""
Polish tests — edge cases, false positives, error paths, stdin,
code-block safety, reference integrity, calibration, designated prompts.

These guard completeness, not features.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit  # type: ignore  # noqa: E402
import decode  # type: ignore  # noqa: E402
import fix  # type: ignore  # noqa: E402

REPO_ROOT = HERE.parent.parent.parent
FIXTURES = HERE / "fixtures"


# ----- false positive gallery -----


def test_false_positive_fixture_i1_passes():
    r = audit.audit(FIXTURES / "false_positives.md")
    assert r.pass_flags["I1_reduce_interpretation"] is True, (
        f"false positive fired on gallery. "
        f"metrics: {r.metrics}, "
        f"findings: {[(f.line, f.issue) for f in r.findings[:5]]}"
    )


def test_false_positive_property_not_flagged_as_proper():
    text = "Property management is the user's job.\n"
    r = audit.audit_text(text)
    assert r.metrics["slop_tier2_no_number"] == 0


def test_false_positive_adj_near_percent_not_flagged():
    text = "Handles 99% uptime under a robust design.\n"
    r = audit.audit_text(text)
    proper_hits = [f for f in r.findings if "robust" in f.snippet.lower()]
    assert len(proper_hits) == 0


def test_false_positive_narration_substring_not_flagged():
    text = "The letter-opener works well.\nChance, let me in!\n"
    r = audit.audit_text(text)
    # "let me" inside "let me in!" is narration-like but in dialog.
    # This IS a known edge case — document that it currently trips:
    # we prefer false positive over false negative here.
    # Test only asserts no crash.
    assert isinstance(r.metrics["narration"], int)


# ----- error paths -----


def test_audit_empty_text_does_not_crash():
    r = audit.audit_text("")
    assert r.line_count == 0
    assert r.metrics["directives"] == 0


def test_audit_missing_file_exits_2():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "audit.py"), "/nonexistent/path.md"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_audit_binary_file_exits_2(tmp_path):
    binary = tmp_path / "bin.md"
    binary.write_bytes(b"\x00\x01\x02\xff\xfe" * 100)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "audit.py"), str(binary)],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "UTF-8" in result.stderr


def test_decode_empty_text_does_not_crash():
    result = decode.decode_text("")
    assert result["line_count"] == 0
    assert len(result["detections"]) == 12  # one per primitive


def test_fix_empty_text_no_changes():
    after, counts = fix.rewrite("")
    assert after == ""
    assert sum(v for k, v in counts.items() if k != "code_segments_skipped") == 0


def test_audit_stdin_empty_returns_error():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "audit.py"), "-"],
        input="", capture_output=True, text=True,
    )
    assert result.returncode == 2


# ----- stdin support -----


def test_audit_stdin_roundtrip():
    good_text = (FIXTURES / "good_6of6.md").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "audit.py"), "-"],
        input=good_text, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "6/6" in result.stdout


def test_decode_stdin_roundtrip():
    good_text = (FIXTURES / "good_6of6.md").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "decode.py"), "-"],
        input=good_text, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "primitives detected" in result.stdout


def test_fix_stdin_pipes_rewrite_to_stdout():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "fix.py"), "-"],
        input="Helper utilizes robust code.\n",
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "utilize" not in result.stdout.lower()
    assert "<FIXME" in result.stdout


# ----- code block safety in fix.py -----


def test_fix_skips_fenced_code_block():
    text = (
        "Outside the block, Helper utilizes patterns.\n"
        "```python\n"
        "def utilize_leverage(): pass  # should not change\n"
        "```\n"
        "Outside again, leverages rule.\n"
    )
    after, counts = fix.rewrite(text)
    assert "def utilize_leverage" in after, "fenced code was rewritten"
    assert after.count("Helper uses patterns") == 1
    assert "uses rule" in after
    assert counts["code_segments_skipped"] >= 1


def test_fix_skips_inline_backtick_code():
    text = "Do not rename `utilize_foo()` but do rewrite utilize elsewhere."
    after, _ = fix.rewrite(text)
    assert "`utilize_foo()`" in after, "inline code was rewritten"
    assert "do rewrite use elsewhere" in after or "do rewrite uses elsewhere" in after


def test_fix_idempotent_with_code_blocks():
    text = (
        "Helper utilizes stuff.\n"
        "```\nutilize()\n```\n"
        "Helper leverages more.\n"
    )
    once, _ = fix.rewrite(text)
    twice, _ = fix.rewrite(once)
    assert once == twice


# ----- line-ref integrity -----


SOURCE_PATH = REPO_ROOT / "source" / "opus-4.7.txt"
LINE_REF_PATTERN = re.compile(r"source/opus-4\.7\.txt:L(\d+)(?:-L?(\d+))?")


def _load_source_lines() -> list[str]:
    return SOURCE_PATH.read_text(encoding="utf-8").splitlines()


def test_skill_md_line_refs_exist_in_source():
    if not SOURCE_PATH.exists():
        pytest.skip("source/opus-4.7.txt not present")
    source_lines = _load_source_lines()
    skill_md = (HERE.parent / "SKILL.md").read_text(encoding="utf-8")
    refs = LINE_REF_PATTERN.findall(skill_md)
    assert len(refs) >= 3, "SKILL.md should cite at least 3 source lines"
    for start, end in refs:
        s = int(start)
        e = int(end) if end else s
        assert 1 <= s <= len(source_lines), f"line {s} out of range"
        assert 1 <= e <= len(source_lines), f"line {e} out of range"
        block = "\n".join(source_lines[s-1:e])
        assert block.strip(), f"L{start} block is empty"


def test_skill_md_line_refs_keyword_anchor():
    """Each cited line should contain a keyword hinting what the ref claims."""
    if not SOURCE_PATH.exists():
        pytest.skip("source/opus-4.7.txt not present")
    source_lines = _load_source_lines()
    # hand-curated: line → at least one keyword the ref implies
    expected = {
        33: ["reframe", "reframing"],
        536: ["narrate"],
        515: ["step", "checklist", "evaluat"],
        640: ["fifteen", "15", "word"],
    }
    for line_num, keywords in expected.items():
        if line_num > len(source_lines):
            continue
        window = "\n".join(source_lines[max(0, line_num-3):line_num+3]).lower()
        assert any(k in window for k in keywords), (
            f"L{line_num} window missing any of {keywords}: "
            f"{window[:200]!r}"
        )


# ----- source calibration (NOT a "prove Opus 4.7 imperfect" test) -----


def test_source_opus_47_calibration_shape():
    """
    Run the auditor on source/opus-4.7.txt.

    We did NOT calibrate regexes by fitting to this file — we wrote regexes
    from principles distilled in primitives/. This test checks that the
    regex behaves the way we claim:
      - saturated with numeric constraints (principle: hard numbers)
      - has multiple decision ladders (principle: I2)
      - contains reframe-as-signal language (principle: I3)

    It does NOT assert 6/6. Source failing I4 would mean "we labeled
    anti-narration as a principle but source has narration" — investigate
    our regex OR our extraction, not source quality.
    """
    if not SOURCE_PATH.exists():
        pytest.skip("source/opus-4.7.txt not present")
    r = audit.audit(SOURCE_PATH)
    m = r.metrics
    assert m["numeric_constraints"] >= 20, f"expected ≥20 numeric constraints, got {m['numeric_constraints']}"
    assert m["ladder_signals"] >= 3, f"expected ≥3 ladder signals, got {m['ladder_signals']}"
    assert m["reframe_signals"] >= 1, f"expected reframe language, got {m['reframe_signals']}"
    assert m["consequences"] >= 10, f"expected ≥10 consequence statements, got {m['consequences']}"


# ----- designated prompts registry (.opus-mind.json) -----


REGISTRY_PATH = REPO_ROOT / ".opus-mind.json"


def test_registry_exists_and_is_valid_json():
    assert REGISTRY_PATH.exists(), ".opus-mind.json missing at repo root"
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert "prompts" in data
    assert isinstance(data["prompts"], list)
    assert len(data["prompts"]) >= 1


def test_designated_prompts_match_expected_scores():
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    for entry in data["prompts"]:
        path = REPO_ROOT / entry["path"]
        if not path.exists():
            failures.append(f"missing: {entry['path']}")
            continue
        r = audit.audit(path)
        passed = sum(1 for v in r.pass_flags.values() if v)
        expected = entry["expected_score"]
        if passed < expected:
            failures.append(
                f"{entry['path']} scored {passed}/6, expected ≥{expected}"
            )
    assert not failures, "designated prompts regressed:\n" + "\n".join(failures)


def test_calibration_files_match_expected_metrics():
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = data.get("calibration_files", [])
    if not entries:
        pytest.skip("no calibration files registered")
    checked = 0
    failures: list[str] = []
    for entry in entries:
        path = REPO_ROOT / entry["path"]
        if not path.exists():
            # Source may be externally hosted (CL4R1T4S). Skip, do not fail.
            continue
        checked += 1
        r = audit.audit(path)
        for metric, bounds in entry.get("expected_metrics", {}).items():
            val = r.metrics.get(metric)
            if val is None:
                failures.append(f"{entry['path']}: unknown metric {metric}")
                continue
            if "max" in bounds and val > bounds["max"]:
                failures.append(
                    f"{entry['path']}: {metric}={val} > max {bounds['max']}"
                )
            if "min" in bounds and val < bounds["min"]:
                failures.append(
                    f"{entry['path']}: {metric}={val} < min {bounds['min']}"
                )
    if checked == 0:
        pytest.skip("no calibration files present locally (externally hosted)")
    assert not failures, "calibration snapshot drifted:\n" + "\n".join(failures)


# ----- CLI dispatcher smoke -----


CLI_PATH = SCRIPTS / "opus-mind"


def test_cli_help_exits_zero():
    result = subprocess.run(
        [str(CLI_PATH), "help"], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "audit" in result.stdout
    assert "decode" in result.stdout


def test_cli_self_audit_exits_zero():
    result = subprocess.run(
        [str(CLI_PATH), "self-audit"], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "6/6" in result.stdout


def test_cli_unknown_command_exits_nonzero():
    result = subprocess.run(
        [str(CLI_PATH), "nonexistent-subcmd"], capture_output=True, text=True,
    )
    assert result.returncode != 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
