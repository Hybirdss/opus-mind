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

## Files (v2)

```
skills/opus-mind/
├── SKILL.md                          218 lines, 6/6 self-audit
├── BUILD.md                          this file
├── scripts/
│   ├── audit.py                      deterministic scorer (6 invariants)
│   ├── decode.py                     inverse audit — label which primitives are present
│   ├── fix.py                        deterministic slop rewriter with <FIXME> markers
│   ├── draft.py                      interactive skeleton builder with audit gate
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

## Model context

Built April 2026. Primary reverse-engineering target: Claude Opus 4.7 system prompt (1408 lines, CL4R1T4S mirror). Primitives generalize to GPT 5.4, Gemini 3.1 Pro, and any sufficiently capable LLM — they address prompt-engineering failure modes, not model-specific behavior.
