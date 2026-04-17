"""
Iron-Law tests for the skill-native orchestration layer.

These tests lock the contracts SKILL.md depends on:

    1. audit.py --json emits a stable schema with verdict / structural_health /
       thin_reason / placeholder_count / pass / findings.
    2. THIN verdict fires on empty or one-line inputs regardless of pass flags.
    3. Placeholder remnants (<FIXME> / <TODO>) prevent GOOD verdict.
    4. Every primitive doc referenced by SKILL.md carries a ## TL;DR section
       that the skill loads to quote back at the user.
    5. No Python helper makes an API call.
    6. boost.py --json emits a schema with coverage + per-slot evidence.

Each test is the skill's memory of what it relies on. Breaking one means
SKILL.md will silently misbehave in production.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCRIPTS = SKILL_ROOT / "scripts"
REPO_ROOT = SKILL_ROOT.parent.parent

sys.path.insert(0, str(SCRIPTS))

import audit  # type: ignore  # noqa: E402
import boost  # type: ignore  # noqa: E402


# ---------------------------------------------------------------------------
# Contract 1 — audit JSON schema stability
# ---------------------------------------------------------------------------


REQUIRED_AUDIT_JSON_KEYS = {
    "schema_version", "path", "line_count", "score", "structural_health",
    "verdict", "thin_reason", "placeholder_count", "pass", "metrics",
    "findings",
}


def _audit_json(text: str) -> dict:
    r = audit.audit_text(text)
    return json.loads(audit._format_json(r))


def test_audit_json_has_all_required_keys():
    j = _audit_json("The assistant must respond. Do not lie.\n")
    missing = REQUIRED_AUDIT_JSON_KEYS - set(j.keys())
    assert not missing, f"audit JSON missing keys: {missing}"


def test_audit_verdict_is_one_of_four():
    j = _audit_json("The assistant must respond. Do not lie.\n")
    assert j["verdict"] in {"THIN", "POOR", "BORDERLINE", "GOOD"}


def test_audit_findings_are_json_serializable():
    j = _audit_json(
        "The assistant must respond.\nNever lie.\nAlways cite sources.\n"
    )
    assert isinstance(j["findings"], list)
    for f in j["findings"]:
        assert set(f.keys()) == {
            "invariant", "line", "snippet", "issue", "fix_pointer",
        }


# ---------------------------------------------------------------------------
# Contract 2 — thin-content gate
# ---------------------------------------------------------------------------


def test_empty_file_yields_thin_verdict():
    j = _audit_json("")
    assert j["verdict"] == "THIN"
    assert j["thin_reason"] is not None
    assert "too thin" in j["thin_reason"].lower()


def test_one_line_prompt_is_thin():
    j = _audit_json("# A single-line prompt\n")
    assert j["verdict"] == "THIN"


def test_non_thin_requires_three_directives_or_ten_lines():
    # 3 directives on 3 lines — below the 10-line bar but at the directive bar.
    text = "You must respond.\nDo not lie.\nAlways cite.\n"
    j = _audit_json(text)
    assert j["verdict"] != "THIN", (
        f"expected non-THIN for ≥3 directives, got {j['verdict']}"
    )


# ---------------------------------------------------------------------------
# Contract 3 — placeholder penalty
# ---------------------------------------------------------------------------


def test_placeholders_prevent_good_verdict():
    # Use a known-good system-prompt fixture (not SKILL.md — that's a
    # different genre). The good/ fixtures are designed to pass every
    # invariant; injecting a placeholder should block GOOD.
    good_fixture = REPO_ROOT / "tests" / "fixtures" / "good" / "05-full-featured.md"
    good_prompt = good_fixture.read_text(encoding="utf-8")
    clean = _audit_json(good_prompt)
    assert clean["placeholder_count"] == 0
    assert clean["verdict"] == "GOOD", (
        f"fixture {good_fixture.name} should verdict GOOD; got "
        f"{clean['verdict']}. failing invariants: "
        f"{[k for k, v in clean['pass'].items() if not v]}"
    )

    # Injecting a <FIXME> should knock the verdict out of GOOD.
    dirty = _audit_json(good_prompt + "\n<FIXME: fill this in>\n")
    assert dirty["placeholder_count"] >= 1
    assert dirty["verdict"] != "GOOD", (
        f"placeholder should block GOOD; got {dirty['verdict']}"
    )


def test_placeholder_count_detects_common_markers():
    text = (
        "The bot must respond in 50 words.\n"
        "Do not lie.\n"
        "Always cite.\n"
        "<TODO: add refusal clause>\n"
        "<YOUR REFUSAL POLICY HERE>\n"
        "<FIXME: define tier 1>\n"
    )
    j = _audit_json(text)
    assert j["placeholder_count"] >= 3, j["placeholder_count"]


@pytest.mark.parametrize("placeholder", [
    "<FIXME: fill in>",
    "<TODO: add details>",
    "<YOUR REFUSAL POLICY>",
    "[TODO: refine]",
    "[FIXME]",
    "[TBD]",
    "TBD",
    "???",
    "tk tk",
    "XXX",
])
def test_placeholder_detected_across_conventions(placeholder):
    """XML, bracket, and bare-marker placeholder conventions all count."""
    text = (
        "The assistant must respond in 100 words. "
        "Do not fabricate facts. Always cite sources.\n\n"
        f"Missing section: {placeholder}\n"
    )
    j = _audit_json(text)
    assert j["placeholder_count"] >= 1, (
        f"failed to detect placeholder {placeholder!r} — "
        f"count={j['placeholder_count']}"
    )
    assert j["verdict"] != "GOOD", (
        f"placeholder {placeholder!r} should prevent GOOD verdict"
    )


def test_placeholder_ignored_in_backticks():
    """Quote-guard: placeholder shapes inside backticks are examples, not
    unfilled content. Docs can mention <FIXME> / [TODO] / XXX freely."""
    text = (
        "The assistant must respond in 100 words.\n"
        "Do not fabricate facts. Always cite sources.\n"
        "Docs reference `<FIXME>` and `[TODO]` and `XXX` as example markers.\n"
    )
    j = _audit_json(text)
    assert j["placeholder_count"] == 0, (
        f"backticked mentions should not count as placeholders; "
        f"got {j['placeholder_count']}"
    )


# ---------------------------------------------------------------------------
# Contract 4 — every referenced primitive doc carries a loadable TL;DR
# ---------------------------------------------------------------------------


PRIMITIVES_DIR = SKILL_ROOT / "references" / "primitives"
TECHNIQUES_DIR = SKILL_ROOT / "references" / "techniques"
TLDR_HEADER = re.compile(r"^##\s+TL;DR\s*$", re.IGNORECASE | re.MULTILINE)


@pytest.mark.parametrize("doc", sorted(PRIMITIVES_DIR.glob("*.md")))
def test_every_primitive_has_tldr_section(doc: Path):
    text = doc.read_text(encoding="utf-8")
    assert TLDR_HEADER.search(text), (
        f"{doc.name} has no ## TL;DR section — SKILL.md cannot quote it"
    )


@pytest.mark.parametrize(
    "doc",
    [p for p in sorted(TECHNIQUES_DIR.glob("*.md")) if p.name != "README.md"],
)
def test_every_technique_has_tldr_section(doc: Path):
    text = doc.read_text(encoding="utf-8")
    assert TLDR_HEADER.search(text), (
        f"{doc.name} has no ## TL;DR section — SKILL.md cannot quote it"
    )


# ---------------------------------------------------------------------------
# Contract 5 — no API call anywhere in the skill tree
# ---------------------------------------------------------------------------


def _all_skill_text_files() -> list[Path]:
    roots = [SKILL_ROOT / "scripts", SKILL_ROOT / "SKILL.md"]
    files: list[Path] = []
    for root in roots:
        if root.is_dir():
            for ext in (".py", ".sh"):
                files.extend(root.rglob(f"*{ext}"))
        elif root.is_file():
            files.append(root)
    return files


FORBIDDEN_API_PATTERNS = [
    r"anthropic\.Anthropic\s*\(",
    r"client\.messages\.create\s*\(",
    r"os\.environ\[[\"']ANTHROPIC_API_KEY[\"']\]",
]


def test_no_python_helper_calls_anthropic_api():
    hits: list[tuple[Path, str]] = []
    compiled = [re.compile(p) for p in FORBIDDEN_API_PATTERNS]
    for path in _all_skill_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in compiled:
            if pat.search(text):
                hits.append((path, pat.pattern))
    assert not hits, (
        f"API-call code leaked back in: {hits}. "
        f"Synthesis is the surrounding LLM's job, not the helper's."
    )


# ---------------------------------------------------------------------------
# Contract 6 — boost JSON schema stability
# ---------------------------------------------------------------------------


REQUIRED_BOOST_CHECK_KEYS = {"source", "coverage", "filled_count", "slots"}


def test_boost_check_json_schema():
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "boost.py"), "check",
         "write a blog post", "--json"],
        capture_output=True, text=True, timeout=15,
    )
    assert out.returncode in (0, 1), out.stderr
    j = json.loads(out.stdout)
    missing = REQUIRED_BOOST_CHECK_KEYS - set(j.keys())
    assert not missing, f"boost check JSON missing keys: {missing}"
    # 10 slots — B1-B7 specification layer, B8-B10 reasoning layer.
    assert set(j["slots"].keys()) == {f"B{i}" for i in range(1, 11)}


def test_boost_ask_ranks_empty_slots_by_impact():
    # ask emits questions only for empty slots. For a completely vague
    # prompt, every slot except possibly B1 is empty. The skill pairs
    # each question with an impact hint — we just check structure here.
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "boost.py"), "ask",
         "help me", "--json"],
        capture_output=True, text=True, timeout=15,
    )
    assert out.returncode in (0, 1), out.stderr
    questions = json.loads(out.stdout)
    assert isinstance(questions, list)
    assert len(questions) >= 3, (
        f"vague prompt should have ≥3 empty slots, got {len(questions)}"
    )
    for q in questions:
        assert "slot" in q and "question" in q and "label" in q


def test_boost_expand_emits_prompt_never_api_response():
    # expand output should be the composition prompt TEMPLATE, not a
    # rewritten blog post. The skill relies on this contract to know
    # that synthesis is still pending.
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "boost.py"), "expand",
         "write a blog post", "--length", "500 words"],
        capture_output=True, text=True, timeout=15,
    )
    assert out.returncode == 0, out.stderr
    body = out.stdout
    # Composition prompt signature — we look for the instruction frame,
    # not for a polished answer.
    assert "Rewrite the prompt" in body or "rewrite the prompt" in body.lower()
    assert "<<<" in body, "expand output should wrap the original in <<< >>>"


# ---------------------------------------------------------------------------
# Contract 7 — SKILL.md frontmatter shape (industry standard)
# ---------------------------------------------------------------------------


def _skill_frontmatter() -> str:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    assert m, "SKILL.md missing YAML frontmatter"
    return m.group(1)


def test_skill_has_name_field():
    assert re.search(r"^name:\s*opus-mind\s*$", _skill_frontmatter(), re.MULTILINE)


def test_skill_has_description_starting_with_use_when():
    fm = _skill_frontmatter()
    # description may span multiple lines — collect everything until the
    # next top-level key.
    m = re.search(
        r"^description:\s*(.+?)(?=^\S|\Z)",
        fm, re.DOTALL | re.MULTILINE,
    )
    assert m, "SKILL.md has no description field"
    desc = m.group(1).strip().strip('"').strip("'")
    assert desc.lower().startswith("use when"), (
        f"description should open with 'Use when ...', got: {desc[:80]!r}"
    )


def test_skill_has_allowed_tools_field():
    fm = _skill_frontmatter()
    assert "allowed-tools" in fm, (
        "SKILL.md frontmatter must declare allowed-tools for platform safety"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
