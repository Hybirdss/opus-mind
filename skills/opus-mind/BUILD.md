# opus-mind Build Log

How this skill was constructed. One-pass build, April 2026, with self-audit gating.

## Goal

Compile the repo's prompt-engineering knowledge into a Claude Code skill that does 4 jobs:

1. Author new system prompts from scratch.
2. Debug failing prompts (refuse-relent, narration leak, rule conflict).
3. Audit and refactor CLAUDE.md / AGENTS.md / .cursorrules / SKILL.md.
4. Score existing prompts against the 6 invariants.

Constraint: prompt engineering content comes only from this repo. Structural conventions borrow from external skill repos.

## Reference repos surveyed

| Repo | Borrowed pattern |
|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | SKILL.md + YAML frontmatter, progressive disclosure (3 levels), `references/` + `scripts/` + `assets/` split |
| [anthropics/skills/skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | Pushy description, domain organization via references, ≤500 line body, imperative form |
| [obra/superpowers](https://github.com/obra/superpowers) | Category split (testing/debugging/collab/meta), sequential workflow with skill check before task |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Gap found: zero dedicated prompt-engineering meta-skills — confirms market whitespace |

Zero prompt engineering content copied from any of these. All primitives, techniques, and methodology are local (`primitives/`, `techniques/`, `methodology/`).

## Architecture decisions

**Single hub over multi-skill pack.** Considered 4-skill pack (spec/audit/debug/refactor) but chose 1 SKILL.md router based on skill-creator's `cloud-deploy` pattern. Reasoning: 4 triggers, 1 progressive-disclosure tree, zero duplication.

**Symlinks over copies.** `references/primitives`, `references/techniques`, etc. symlink to repo root. Edits to primitive files auto-propagate. Distribution can resolve symlinks at package time.

**Deterministic scorer over LLM grader.** `audit.py` uses regex + counts, not LLM calls. 0 API cost, 0 latency, reproducible output. Fuzzy judgment belongs in downstream LLM consumption of the script output.

**6-invariant gate on the skill's own SKILL.md.** Forcing function: skill refuses release if it scores <6/6 on itself. Prevents hypocrisy (can't ship anti-slop advice written in slop).

## Build sequence

### Step 1 — Directory + symlinks

```
mkdir -p skills/opus-mind/{references,assets,scripts}
ln -s ../../../primitives references/primitives
ln -s ../../../techniques references/techniques
ln -s ../../../methodology/README.md references/methodology.md
ln -s ../../../evidence/line-refs.md references/line-refs.md
ln -s ../../../annotations references/annotations
ln -s ../../../templates/system-prompt-skeleton.md assets/skeleton.md
ln -s ../../../templates/example-customer-support.md assets/example-customer-support.md
```

### Step 2 — `scripts/audit.py` (400 lines)

Deterministic scorer. Six invariant checks, each a regex + threshold:

| Invariant | Check | Threshold |
|---|---|---|
| I1 reduce interpretation | SLOP_TIER1 + SLOP_TIER2_NO_NUMBER + HEDGES counts | 0 + 0 + ≤2 |
| I2 no rule conflicts | LADDER_SIGNALS present when directives ≥ 6 | ≥1 if needed |
| I3 motivated reasoning | REFRAME_SIGNALS present when refusal content exists | ≥1 if refusal |
| I4 anti-narration | NARRATION phrase count | 0 |
| I5 example + rationale | rationale count when examples exist | ≥1 if examples |
| I6 failure modes explicit | consequence statements | ≥ directives/10 |

Plus structural metrics: XML block balance, number_density (numeric constraints / directive sentences), directive count.

CLI modes: `<path>` for a file, `--json` for machine output, `--self` to audit this skill's own SKILL.md. Exit code 0 on 6/6, 1 otherwise.

### Step 3 — Draft 1 of SKILL.md

First draft scored **4/6** on itself:
- I1 FAIL: 9 Tier-1 slop hits, 4 adj-without-number hits, 5 hedges
- I4 FAIL: 5 narration hits

Root cause: the draft inlined the blacklist (`No Tier-1 slop words (delve, utilize, leverage, ...)`) as example text. The auditor correctly flagged every blacklist word. The document was quoting the disease it prevents.

### Step 4 — Draft 2, self-compliance gate passes

Moves applied:

1. Moved blacklist contents out of SKILL.md into `scripts/audit.py` as SLOP_TIER1 / HEDGES / NARRATION constants. SKILL.md now points: "full list at `scripts/audit.py`".
2. Replaced example findings that contained literal slop with placeholder tokens: `"<adjective>"`, `"<narration-phrase>"`.
3. Rewrote "No machinery narration" to "zero machinery narration phrases" — avoids quoting banned phrases.
4. Removed hedge words from contract summary by removing the literal list.

Draft 2 score: **6/6**.

```
invariants:
  [PASS] I1_reduce_interpretation
  [PASS] I2_no_rule_conflicts
  [PASS] I3_motivated_reasoning
  [PASS] I4_anti_narration
  [PASS] I5_example_rationale
  [PASS] I6_failure_modes_explicit

metrics:
  slop_tier1: 0
  hedges: 0
  narration: 0
  ladder_signals: 9
  reframe_signals: 8
  consequences: 23
  directives: 15
```

### Step 5 — Regression test on repo's own templates

- `templates/system-prompt-skeleton.md` → **5/6**. I4 fails (3 narration hits in instructional prose, not in the skeleton body).
- `templates/example-customer-support.md` → **3/6**. I1 fails (6 Tier-1 slop), I3 fails (refusal content without reframe-as-signal), I4 fails (3 narration).

Both findings are real. Our own example prompt has 6 Tier-1 slop words — a concrete follow-up task.

## Files (v3 — B-tier)

```
skills/opus-mind/
├── SKILL.md                          218 lines, 6/6 self-audit
├── BUILD.md                          this file
├── scripts/
│   ├── audit.py                      deterministic scorer + --crosscheck LLM mode
│   ├── decode.py                     inverse audit — label which primitives are present
│   ├── fix.py                        deterministic slop rewriter with <FIXME> markers
│   ├── draft.py                      interactive skeleton builder with audit gate
│   ├── symptom_search.py             symptom → source evidence + primitive pointer
│   ├── install-hook.sh               git pre-commit hook installer
│   └── opus-mind                     single-entry CLI dispatcher
├── tests/
│   ├── conftest.py                   pytest path wiring
│   ├── test_audit.py                 13 regression tests
│   └── fixtures/
│       ├── good_6of6.md              known-good 6/6 prompt
│       ├── bad_slop.md               I1 failure fixture
│       ├── bad_narration.md          I4 failure fixture
│       ├── bad_no_ladder.md          I2 failure fixture
│       ├── bad_refusal_no_reframe.md I3 failure fixture
│       └── bad_no_consequence.md     I6 failure fixture
├── references/                       symlinks to primitives, techniques, methodology, line-refs, annotations
└── assets/                           symlinks to skeleton.md, example-customer-support.md
```

## v2 extensions (S-tier + A-tier build)

### decode.py — reverse audit

Inverse of audit.py. For each of the 12 primitives, detects presence + line ranges + confidence (high / medium / low / absent). Plus topic-aware suggestions ("file has refusal content but no reframe-as-signal clause — read primitives/09").

Detector regexes cover: XML block pairs, Step ladders + stop clauses, numeric constraints, default+exception pairs, cue phrases, rationale markers, self-check phrases, anti-narration clauses, reframe signals, asymmetric-trust clauses, capability-disclosure clauses, priority-hierarchy clauses.

### fix.py — deterministic rewriter

Three replacement strategies:
1. TIER1_REPLACEMENTS — 50+ 1-to-1 mappings (utilize → use, leverage → use, robust stays but gets adj-without-number treatment).
2. FILLER_DELETES — regex deletions for AI filler phrases.
3. ADJ_NO_NUMBER_FIXMES — adj not near a number → `<FIXME: name the metric>` marker. Idempotent (marker does not contain the adj).

Modes: `--dry-run` (default, diff to stdout), `--apply` (write back), `-o <path>` (write elsewhere).

### draft.py — interactive skeleton builder

12-question Q&A fills the skeleton template. Accepts `--answers answers.json` for non-interactive use. After writing, auto-runs `audit.py` on the draft. Tested: generated draft scores 6/6.

### opus-mind CLI

Single shell entry. Subcommands: audit, decode, fix, draft, self-audit, help.

### install-hook.sh — git pre-commit

Installs `.git/hooks/pre-commit` in the current repo. On commit, scans staged CLAUDE.md / AGENTS.md / .cursorrules / GEMINI.md / SKILL.md / system-prompt*.md. Blocks commit if any file scores below threshold (default 5/6). Override: `git commit --no-verify`.

### tests/ — pytest regression

13 tests across audit, decode, fix. Covers:
- good fixture scores 6/6
- each bad fixture fails the expected invariant
- SKILL.md itself still scores 6/6 (no self-regression)
- decode correctly flags present vs absent primitives
- fix is idempotent and preserves adj-near-number

All 13 pass.

## Debug notes from v2 build

- Broken symlink incident: during v2 build, `scripts/` got flipped from a real dir to a `../../../scripts` broken symlink (root cause unknown). Recovered by removing the symlink and moving the scripts back into the skill tree.
- Regex false positive: first version of stem-match (`\w{0,4}`) caught `property` as `proper` + `ty`. Split SLOP_TIER1 / SLOP_TIER2 into STEM (inflects) and EXACT (no inflection) groups. Fixed 1 pytest failure.
- NUMBER_NEARBY regex: trailing `\b` failed on `%` because `%` is non-word and trailing space is also non-word (no boundary). Added explicit `\d+\s*%` alternative.
- Idempotency bug in fix.py: FIXME marker containing the adj word would match on second pass. Rewrote all ADJ_NO_NUMBER_FIXMES to drop the adj from the marker.

## Verification summary (v2)

| Check | Result |
|---|---|
| Self-audit 6/6 | PASS |
| Detects real issues in our own templates | PASS (skeleton 5/6, customer-support 3/6) |
| pytest regression | 13/13 PASS |
| Skill body ≤ 500 lines | PASS (218) |
| Zero Tier-1 slop in SKILL.md | PASS |
| Zero narration in SKILL.md | PASS |
| Progressive disclosure via symlinks | PASS |
| Deterministic scoring (no LLM calls) | PASS |
| decode CLI exits 0 and lists 12 primitives | PASS |
| fix idempotent on repeated passes | PASS |
| draft + answers.json produces 6/6 draft | PASS |
| opus-mind CLI dispatches all subcommands | PASS |
| install-hook.sh bash syntax valid | PASS |

## v3 extensions (B-tier build)

### symptom_search.py — symptom → source evidence

Two-layer lookup:
1. Hand-curated SYMPTOM_TABLE maps 14 canonical symptom phrases (with aliases) to primitive + technique file pointers. Alias matching: substring hit OR full-token-subset hit OR 2+ token overlap.
2. Full-text index of `evidence/line-refs.md` (212 rows parsed as markdown tables). Token-overlap scoring with a concept-field bonus.

Output block: symptom table hits (canonical + aliases + read-paths) plus top-N evidence rows (source line ref + paraphrase + tokens matched).

### audit.py --crosscheck prompt|exec

Adds LLM-assisted second reviewer mode:
- `--crosscheck prompt` builds a structured prompt containing the 6 invariants, deterministic findings, target prompt excerpt (≤12000 chars), and a primitive vocabulary reference. Output: paste-ready for any LLM.
- `--crosscheck exec` attempts to call the Anthropic API via the `anthropic` SDK using model `claude-opus-4-7` (April 2026). Falls back to printing the prompt + exit code 2 when `ANTHROPIC_API_KEY` is missing or the SDK is not installed.
- `--crosscheck-model` flag overrides the default model (e.g. `claude-sonnet-4-6`).

The crosscheck prompt asks the LLM for JSON with four keys: `false_positives`, `additional_findings`, `severity_delta`, `overall_verdict`. This keeps the output machine-parseable and composable with audit JSON.

### CLI extensions

Added to `opus-mind` dispatcher:
- `opus-mind symptom "<query>"` → symptom_search.py
- `opus-mind crosscheck <path> [--exec]` → audit.py --crosscheck

### pytest additions

5 new tests (18 total, all pass):
- `test_symptom_search_refuse_relent_hits_caution_contagion`
- `test_symptom_search_injection_hits_asymmetric_trust`
- `test_symptom_search_returns_evidence_rows` (verifies index size > 50)
- `test_symptom_search_nonsense_query_returns_nothing_but_no_crash`
- `test_crosscheck_prompt_contains_invariants_and_findings`

## Verification summary (v3)

| Check | Result |
|---|---|
| Self-audit 6/6 | PASS |
| pytest regression | 18/18 PASS |
| symptom → primitive lookup | PASS (caution-contagion, asymmetric-trust) |
| symptom search indexes 212 evidence rows | PASS |
| crosscheck prompt builds from fixture | PASS (93 lines output) |
| crosscheck --exec graceful fallback without API key | PASS |
| opus-mind CLI dispatches symptom + crosscheck | PASS |

## v4 — completeness pass (no new features)

### Scope correction

Polish pass caught a conceptual bug: the skill was treating `.md` as synonymous
with "prompt". Actually most `.md` files in this repo are **docs about prompts**
(primitives/, techniques/, annotations/, README, BUILD). Auditing those would
produce meaningless noise — "this primitive file mentions 'utilize' as a bad
example" is not a finding.

Fix: promoted a single source of truth for what IS a prompt. `.opus-mind.json`
at the repo root lists 3 designated prompt files and 1 calibration file.
Auditor iterates over this list, not over every .md.

Additional correction: dropped the idea that "audit source/opus-4.7.txt proves
Opus 4.7 is imperfect." It doesn't — we extracted the principles from source.
If source fails a check, it means (a) our regex is miscalibrated, or (b) we
over-generalized a principle. Source audit is reframed as a **calibration
snapshot**, not a judgment test. Expected-metrics live in
`.opus-mind.json:calibration_files[]`.

### stdin support

audit.py / decode.py / fix.py all accept `-` as path to read from stdin.
fix.py pipes rewritten text to stdout when reading stdin. Verbose counts go
to stderr so piping stays clean.

```
cat my-prompt.txt | opus-mind audit -
jq -r .system config/agent.yaml | opus-mind audit -
```

Breaks the `.md` assumption — the tool now works on any text regardless of
how it was extracted.

### Regex tightening

Removed `proper` and `reasonable` from SLOP_TIER2_EXACT. Too many legitimate
English uses ("proper noun", "reasonable doubt") caused false positives.
Prefer false negative on ambiguous words.

Expanded NUMBER_CONSTRAINT to cover `%`, `per hour`, `requests`, `iterations`,
`attempts`, `retries`, `users`, `pages`, `rows`, `dollars`. Previous regex
missed `"500 requests per hour"` as a numeric constraint, causing
`"robust load balancer"` nearby to be flagged.

Applied identical regex to audit.py, decode.py, and fix.py (single shape).

### Code-block safety in fix.py

fix.py now parses fenced code blocks (```...```) and inline code (\`...\`)
before rewriting. Code segments are skipped. Sample code in docs (e.g., a
`README.md` showing `utilize_foo()`) no longer gets rewritten. Counter
`code_segments_skipped` tracks skips.

### Install-hook UX

install-hook.sh gained:
- Existing hook detection: backs up non-opus-mind hooks to
  `pre-commit.backup-<timestamp>`.
- `--dry-run` flag prints the hook content without installing.
- `--uninstall` flag restores the most recent backup, or removes
  the opus-mind hook if no backup exists.
- `--threshold N` validated to 1-6.
- Bypass instructions (`git commit --no-verify`) inline in the hook.
- Hook itself reads `.opus-mind.json:prompts[]` for file list, with
  pattern fallback (CLAUDE.md / AGENTS.md / .cursorrules / SKILL.md).

### Tests added (test_polish.py, 26 cases)

| Group | Cases |
|---|---|
| False-positive gallery | 3 (property/proper disambiguation, % boundary, narration substring) |
| Error paths | 6 (empty text, missing file, binary file, empty stdin, fix no-op, decode empty) |
| stdin roundtrip | 3 (audit / decode / fix via `-`) |
| Code-block safety | 3 (fenced skip, inline skip, idempotent with code blocks) |
| Line-ref integrity | 2 (skill.md refs exist in source, keyword anchors match) |
| Calibration snapshot | 1 (source/opus-4.7.txt metrics match bounds when present) |
| Designated prompts | 3 (registry valid, scores match expected, calibration gates) |
| CLI dispatcher | 3 (help, self-audit, unknown subcmd) |

Line-ref and calibration tests skip gracefully when `source/opus-4.7.txt` is
not in the checkout (CL4R1T4S-hosted, not committed).

### GitHub Actions CI

`.github/workflows/opus-mind.yml` runs on push/PR that touches the skill or
its source files. Matrix over Python 3.11 / 3.12 / 3.13. Steps:
1. pytest
2. self-audit must score 6/6
3. all `.opus-mind.json:prompts[]` must meet `expected_score`
4. install-hook.sh bash syntax
5. CLI help exits zero

## Verification summary (v4)

| Check | Result |
|---|---|
| Self-audit 6/6 | PASS |
| pytest | 75 passed, 4 skipped (source absent) |
| Designated prompts match registry | PASS (6/6, 5/6, 3/6) |
| Regex false positives eliminated | PASS (proper/reasonable dropped, % + per-hour added) |
| fix.py skips code blocks | PASS |
| stdin pipelines work (audit / decode / fix) | PASS |
| install-hook.sh backup / uninstall / dry-run | PASS |
| CI workflow valid YAML | PASS |

## Model context

Built April 2026. Primary reverse-engineering target: Claude Opus 4.7 system prompt (1408 lines, CL4R1T4S mirror). Primitives generalize to GPT 5.4, Gemini 3.1 Pro, and any sufficiently capable LLM — they address prompt-engineering failure modes, not model-specific behavior.
