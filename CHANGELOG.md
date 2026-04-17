# Changelog

All notable changes to opus-mind are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [SemVer](https://semver.org/).

JSON schema changes in `audit.py --json` and `boost.py --json` bump
the minor version. Breaking changes to SKILL.md flow semantics bump
the major version.

---

## [0.1.0] — 2026-04-17

First public release.

### Added — LINT (system-prompt auditor)
- `audit.py` — 11 structural invariants (I1 hard-numbers through
  I11 hierarchical-override), each anchored to specific lines in
  the leaked Claude Opus 4.7 system prompt (via CL4R1T4S mirror).
- `plan.py` — domain inference (has_tools, has_refusals, is_long,
  has_examples, has_conflicts) + required-primitive computation.
- `fix.py` — deterministic slop rewriter + `--add` skeleton
  injection for ladder / reframe-guard / consequences / defaults /
  self-check / tier-labels.
- `decode.py` — reverse-label detection across all 12 primitives
  with confidence levels (high / medium / absent).
- `symptom_search.py` — natural-language symptom to primitive
  pointer with evidence line references.
- `install-hook.sh` — git pre-commit installer with backup /
  dry-run / uninstall safety.
- `install-skill.sh` — Claude Code skill symlink to
  `~/.claude/skills/opus-mind/` with the same safety guarantees.

### Added — BOOST (user-prompt coach)
- 10-slot coverage: B1 task / B2 format / B3 length / B4 context /
  B5 few_shot / B6 constraints / B7 clarify (specification layer)
  plus B8 reasoning / B9 verification / B10 decomposition
  (reasoning layer).
- Task-type inference (code / analyze / research / write / short /
  unknown) drives dynamic slot-impact ranking so the skill asks
  the highest-leverage empty slot first.
- `check` / `ask` / `expand` subcommands; `expand` emits a
  composition prompt only — synthesis is the surrounding LLM's job.
- Reasoning-layer false-positive guards: imperative sequences,
  `check` as a verb, and `for each <noun>` do not trigger B8-B10.

### Added — Claude Code skill surface
- `SKILL.md` rewritten to industry-standard frontmatter
  (`allowed-tools`, `argument-hint`, "Use when ..." description)
  with phase-based flows, JSON schemas documented inline, and
  explicit platform adaptation (Claude Code / Codex / Gemini).
- Language-adaptive override — the skill instructs Claude to
  supplement the English-centric regex layer with its own
  language judgment when the target prompt is non-English.

### Added — Evidence and testing
- `evidence/line-refs.md` — 225-row index of LINT claims to
  Opus 4.7 source lines.
- `evidence/smart-prompting-refs.md` — citation chain for BOOST's
  reasoning layer (Wei 2022 CoT, Shinn 2023 Reflexion, Zhou 2022
  Least-to-most, plus Anthropic public prompt-engineering docs).
- 156 passing tests. 4 skipped when offline (CL4R1T4S live-fetch
  dogfood tests).
- Iron-Law `test_skill_orchestration.py` locks JSON schema
  stability, TL;DR loadability across primitives/techniques,
  frontmatter shape, and no-API-call invariant.

### Added — Scoring quality
- `verdict` field: THIN / POOR / BORDERLINE / GOOD.
- Thin-content gate: directives < 3 AND lines < 10 → THIN,
  closes the "empty file scores 10/11" hole.
- Placeholder penalty: `<FIXME>`, `[TODO]`, `TBD`, `???`, `XXX`,
  `tk tk` remnants block the GOOD verdict. Backtick-quoted
  mentions (examples) are exempt via quote-span guard.
- `structural_health` alias for score, exposed in JSON.

### Changed
- `report.py` removed — its responsibilities moved into SKILL.md
  instructions so Claude composes the report natively rather than
  reading a pre-formatted prose dump.
- `audit.py --self` now prints an informational stderr warning
  and does not gate anything. SKILL.md is instruction prose for
  Claude Code, not a system prompt — the old "score SKILL.md 11/11
  or fail CI" gate was a genre mismatch.
- All technique files (`techniques/0N-*.md`) now carry a
  `## TL;DR` section so SKILL.md can quote them back to the user.

### Removed
- `_try_api_call` paths from `audit.py` and `boost.py`.
- `--crosscheck exec`, `--crosscheck-model`, `--mode exec`,
  `--model` flags. Synthesis is always the surrounding runtime's
  job; the helpers emit composition / review prompts only.

### Architecture
- Python helpers are deterministic: regex + counts + string
  templates. They never call an LLM and never read
  `ANTHROPIC_API_KEY`.
- The Claude Code skill is the product; the bash wrapper is
  the CLI escape hatch for pre-commit hooks, CI jobs, and users
  outside a Claude Code session.
