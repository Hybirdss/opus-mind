"""
Golden-fixture regression tests for scripts/audit.py.

Layout:
  tests/fixtures/good/*.md  — each must score 6/6.
  tests/fixtures/bad/*.md   — each must fail exactly one invariant (inferred
                              from the filename prefix: iN-*.md → IN).

Naming contract for bad/: filename starts with "i<N>-" where <N> is 1–6.
That invariant must fail; every other invariant must pass.

Run:
    python3 -m pytest tests/test_fixtures.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPTS = REPO / "skills" / "opus-mind" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit  # type: ignore  # noqa: E402


INVARIANT_KEYS = {
    "1": "I1_reduce_interpretation",
    "2": "I2_no_rule_conflicts",
    "3": "I3_motivated_reasoning",
    "4": "I4_anti_narration",
    "5": "I5_example_rationale",
    "6": "I6_failure_modes_explicit",
}


GOOD_FIXTURES = sorted((HERE / "fixtures" / "good").glob("*.md"))
BAD_FIXTURES = sorted((HERE / "fixtures" / "bad").glob("*.md"))


@pytest.mark.parametrize("path", GOOD_FIXTURES, ids=lambda p: p.name)
def test_good_scores_six_of_six(path: Path) -> None:
    report = audit.audit(path)
    failing = [k for k, v in report.pass_flags.items() if not v]
    assert not failing, (
        f"{path.name} regressed: {report.score}, failing: {failing}"
    )


@pytest.mark.parametrize("path", BAD_FIXTURES, ids=lambda p: p.name)
def test_bad_fails_exactly_one_expected_invariant(path: Path) -> None:
    prefix = path.name.split("-", 1)[0]          # "i1", "i2", etc.
    digit = prefix[1:]                           # "1", "2", ...
    expected = INVARIANT_KEYS.get(digit)
    assert expected, f"{path.name}: filename does not encode invariant"

    report = audit.audit(path)
    failing = [k for k, v in report.pass_flags.items() if not v]

    assert failing == [expected], (
        f"{path.name}: expected exactly [{expected}] to fail, "
        f"got {failing}"
    )


def test_all_good_and_bad_fixtures_exist() -> None:
    assert len(GOOD_FIXTURES) >= 5, "need at least 5 good fixtures"
    assert len(BAD_FIXTURES) >= 12, "need at least 12 bad fixtures"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
