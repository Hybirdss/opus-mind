# Opus 4.7, Decoded

Claude's own system prompt, reverse-engineered into tools that audit yours.

```
$ opus-mind audit CLAUDE.md
score: 6/11
  [FAIL] I1_reduce_interpretation
  [FAIL] I2_no_rule_conflicts
  [FAIL] I6_failure_modes_explicit
  [FAIL] I8_default_exception
  [FAIL] I9_self_check

  -- [I1] hedge_density 0.42 > 0.25 (11 hedges / 26 directives)
  -- [I2] 26 directives, 0 ladders        fix → primitives/02-decision-ladders.md
  -- [I6] 0 consequences, need ≥ 2        fix → techniques/04-consequence-statement.md
```

```
$ opus-mind plan CLAUDE.md
domain signals: has_tools, is_long, has_refusals
TODO — missing required primitives:
  [ ] I2_no_rule_conflicts  → 02 decision-ladders   (fix: fix.py --add ladder)
  [ ] I6_failure_modes_explicit  → 04 consequence   (fix: fix.py --add consequences)
  [ ] I8_default_exception  → 04 default+exception  (fix: fix.py --add defaults)
  [ ] I9_self_check         → 07 self-check        (fix: fix.py --add self-check)

$ opus-mind fix CLAUDE.md --add ladder,consequences,defaults,self-check --apply
  injected: ladder, consequences, defaults, self-check

$ opus-mind audit CLAUDE.md
score: 10/11
```

```
$ opus-mind decode your-prompt.md
[  high] 01 namespace-blocks       8 balanced blocks (L4-L18, L22-L41, ...)
[  high] 02 decision-ladders       3 steps, 1 stop-clause (L24)
[  high] 03 hard-numbers           6 numeric constraints
[absent] 09 reframe-as-signal      0 clauses  ← missing
[absent] 11 capability-disclosure  0 clauses  ← missing
```

Four things here:

1. **12 reusable primitives** extracted from the 1,408-line leaked Claude Opus 4.7 system prompt — the highest-quality production prompt engineering in public view.
2. **11 structural invariants** that detect whether a prompt practises those primitives. Regex + density + shape, no hardcoded style lists, no LLM calls, zero API cost.
3. **Four-command loop — `audit` → `plan` → `fix --add` → `audit`.** Score 0-11, get a TODO of missing primitives, inject structural skeletons for the gaps, re-score.
4. **A pre-commit hook** that blocks a commit when `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or any `**/SKILL.md` drops below a threshold. Self-enforcing across your repo.

This repo is dogfooded. Every prompt-like file here passes the same audit that gates your commits.

**한국어 버전:** [README.ko.md](./README.ko.md) · **Primer:** [methodology/README.md](./methodology/README.md) · **Install in 30 seconds:** [below](#30-second-quick-start)

---

## 30-second quick start

```bash
# clone and try it on one of your prompts
git clone https://github.com/<user>/opus-4-7-decoded
cd opus-4-7-decoded

# audit — score any prompt against 6 invariants
python3 skills/opus-mind/scripts/audit.py path/to/your/CLAUDE.md

# decode — label which of the 12 primitives the prompt uses
python3 skills/opus-mind/scripts/decode.py path/to/your/CLAUDE.md

# rewrite — apply deterministic fixes (slop, adj-without-number)
python3 skills/opus-mind/scripts/fix.py path/to/your/CLAUDE.md --in-place

# gate your commits — install as pre-commit hook
bash skills/opus-mind/scripts/install-hook.sh
```

Or use the unified CLI: `bash skills/opus-mind/scripts/opus-mind audit <file>`.

**Works on any prompt-like file.** The tools are format-agnostic — they score the shape, not the topic. Cursor rules, Claude Code skills, GPTs instructions, system-prompt markdown — all accepted.

---

## The three tools

### `audit.py` — score against 6 invariants

Every prompt gets a 0-6 score. Each invariant is a regex + threshold, not a vibe check. The six:

| # | Invariant | What it checks |
|---|---|---|
| I1 | Reduce interpretation surface | Zero Tier-1 slop words, zero adj-without-number, ≤ 2 hedges |
| I2 | Eliminate rule conflicts | Decision ladder present when directives ≥ 6 |
| I3 | Catch motivated reasoning | Reframe-as-signal clause when refusal topics appear |
| I4 | Keep internals private | Zero narration phrases ("Let me", "I'll analyze") |
| I5 | Calibrate through examples | Every example carries a rationale |
| I6 | Make failure modes explicit | Consequence statements scale with directive count |

[Full methodology →](./methodology/README.md)

### `decode.py` — reverse-label the 12 primitives

Point it at any system prompt. Get back a table showing which of the 12 reusable primitives the prompt implements, where (line ranges), and with what confidence. `absent` entries are your checklist of what's missing.

This is the inverse of `audit`. Audit tells you what's broken; decode tells you what's there.

### `fix.py` — deterministic rewrite

Tier-1 slop words get replaced with plain equivalents. Adjectives without numbers get `<FIXME>` markers so you see exactly where to hard-number. Idempotent: running it twice is the same as running it once. No LLM involved, no surprises.

---

## The pre-commit hook

```bash
bash skills/opus-mind/scripts/install-hook.sh                 # threshold 5 (default)
bash skills/opus-mind/scripts/install-hook.sh --threshold 6   # strict mode
```

From now on, any commit that stages a file matching `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `**/SKILL.md`, or `system-prompt*.md` runs `audit.py` first. Scores below threshold block the commit:

```
$ git commit -m "tweak CLAUDE.md"
[opus-mind] FAIL CLAUDE.md — score: 4/6 (need >= 5)

commit blocked. fix the failing files or bypass with: git commit --no-verify
```

Install in any other repo too — the hook auto-discovers `audit.py` from either the repo's own `skills/opus-mind/scripts/` or from `$HOME/.opus-mind/audit.py` if you vendor it.

---

## The 12 primitives

Each has its own file in [`primitives/`](./primitives/) with evidence (line refs), failure mode, how to apply, before/after examples, misuse cases.

| # | Primitive | One-line rule |
|---|---|---|
| 01 | [Namespace blocks](./primitives/01-namespace-blocks.md) | XML section tags as scoped modules, markdown headers are not enough |
| 02 | [Decision ladders](./primitives/02-decision-ladders.md) | `Step 0 → N`, first-match-wins, no rule conflicts |
| 03 | [Hard numbers](./primitives/03-hard-numbers.md) | "15 words" beats "keep quotes short" every time |
| 04 | [Default + exception](./primitives/04-default-plus-exception.md) | Strong default stated first, explicit opt-in list, no third path |
| 05 | [Cue-based matching](./primitives/05-cue-based-matching.md) | Teach linguistic signals, not a flowchart |
| 06 | [Example + rationale](./primitives/06-example-plus-rationale.md) | Every example carries its own "why" |
| 07 | [Self-check assertions](./primitives/07-self-check-assertions.md) | Runtime checklist before emit |
| 08 | [Anti-narration](./primitives/08-anti-narration.md) | Hide internal machinery from the user |
| 09 | [Reframe-as-signal](./primitives/09-reframe-as-signal.md) | Softening the request IS the refusal trigger |
| 10 | [Asymmetric trust](./primitives/10-asymmetric-trust.md) | Different claims, different verification bars |
| 11 | [Capability disclosure](./primitives/11-capability-disclosure.md) | Tell the model what it doesn't know |
| 12 | [Hierarchical override](./primitives/12-hierarchical-override.md) | Safety > user request > helpfulness, explicit priority |

Seven additional compositional patterns live in [`techniques/`](./techniques/) (force-tool-call, paraphrase-with-numeric-limits, caution-contagion, consequence-statement, injection-defense-in-band, negative-space, category-match).

---

## Dogfooding

Every claim in this README is backed by tests, fixtures, or both.

```
$ python3 -m pytest tests/ skills/opus-mind/tests/ -q
96 passed, 4 skipped
```

- **The Opus 4.7 source itself scores 6/6.** `tests/test_dogfood.py` fetches the CL4R1T4S mirror on every run and asserts `score == 6/6`. If the regex ever drifts away from the source, the dogfood gate breaks first. This is non-negotiable: if the auditor doesn't pass the document it was derived from, the auditor is wrong.
- The skill itself (`skills/opus-mind/SKILL.md`) scores 6/6. Regression-tested on every pytest run.
- 5 golden-good fixtures in [`tests/fixtures/good/`](./tests/fixtures/good/) stay at 6/6.
- 13 golden-bad fixtures in [`tests/fixtures/bad/`](./tests/fixtures/bad/) each fail exactly one known invariant.
- 2 stylebook fixtures in [`tests/fixtures/stylebook/`](./tests/fixtures/stylebook/) verify that opt-in `--stylebook` mode surfaces the author's anti-slop list without polluting the primary score.
- The pre-commit hook is installed on this repo's `.git/hooks/pre-commit`. Commits that would regress the analysis fail locally before push.

### External prompt scores (snapshot)

Under the pure-Opus-4.7 auditor (11 invariants):

| Source | Score | Chief gaps |
|---|---|---|
| Claude Opus 4.7 (CL4R1T4S) | **11/11** | — (the canon, non-negotiable) |
| OpenAI Codex | 7/11 | I2 ladder, I8 default+exception, I9 self-check, I10 tier labels |
| Cursor 2.0 | 6/11 | I1 numbers, I2 ladder, I6 consequence, I8 default, I9 self-check |
| ChatGPT-5 (Aug 2025) | 4/11 | I1, I2, I3, I5, I6, I9, I11 |

These are findings, not verdicts. A 6/11 score means the prompt is not written in the 12-primitive style — it does not mean the product is bad. All four prompts fetched from the public CL4R1T4S archive; scores reproducible via `opus-mind audit`.

## Pure Opus 4.7 grounding — 11 invariants

Every signal set in `audit.py` is traceable to specific lines of the CL4R1T4S mirror. The 11 invariants cover the 12 primitives (I12 capability-disclosure is advisory-only in `plan`, not gated in `audit`, because it requires product-specific vocabulary):

| # | Primitive | What's checked | Source evidence |
|---|---|---|---|
| I1 | 03 hard-numbers | hedge_density ≤ 0.25, number_density ≥ 0.10 | L664 (15-word limit), L620 (tool-call scaling) |
| I2 | 02 decision-ladders | Step N tokens, "stop at the first match" | L515–L537 (request_evaluation_checklist) |
| I3 | 09 reframe-as-signal | reframe clause when refusal content present | L33 |
| I4 | 08 anti-narration | zero forbidden preambles | L536, L560 |
| I5 | 06 example + rationale | every example has rationale | L710–L750 |
| I6 | technique 04 | consequence count ≥ directives/10 | L753–L759 |
| I7 | 01 namespace-blocks | every `{foo}` has `{/foo}` | structural, whole doc |
| I8 | 04 default + exception | "default" + "unless/except/only when" co-occur | L25, L57–68 |
| I9 | 07 self-check | self-check block when prompt is long | L698–L707 |
| I10 | pattern: tier-labels | ALLCAPS multi-word token when high-stakes | L640 "SEVERE VIOLATION", L657 "NON-NEGOTIABLE", L678 "ABSOLUTE LIMITS" |
| I11 | 12 hierarchical-override | Tier N tokens OR X > Y > Z chain OR "takes precedence" | L657 |

Every detector is **structural** where possible (XML balance, numeric density, ALLCAPS shape, Tier tokens). The few that require vocabulary (reframe, consequence, refusal-topic, narration) use small, source-cited lists. The author's personal anti-slop list (`delve`, `utilize`, `leverage`...) is **not** part of the primary score — the Opus 4.7 source itself uses several of those words. Those preferences live in [`stylebook.py`](./skills/opus-mind/scripts/stylebook.py), opt-in via `audit.py --stylebook`.

### The loop: audit → plan → fix

```
opus-mind audit  CLAUDE.md                 # score 11 invariants, show failures
opus-mind plan   CLAUDE.md                 # list MISSING required primitives for your domain
opus-mind fix    CLAUDE.md --add <names>   # inject structural skeletons for the missing ones
opus-mind audit  CLAUDE.md                 # re-score: watch it climb
```

Valid `--add` values: `ladder`, `reframe-guard`, `consequences`, `tier-labels`, `self-check`, `defaults`. Each injects a minimal, Opus 4.7-grounded scaffold where you fill in the domain-specific words.

---

## Why this combination is unusual

Most prompt-engineering resources pick one lane. Books and blog posts teach patterns without giving you a tool. Skill repos give you tools without grounding the rules in evidence. Linters give you tools and rules but no theory of why they matter.

This repo ships all four layers, anchored to a single source document:

- **Evidence** — every rule cites lines in the leaked Opus 4.7 source (mirrored at [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)).
- **Theory** — [methodology/README.md](./methodology/README.md) states the 6 invariants, 4 architectural patterns, and why the primitives generalize beyond Claude.
- **Tools** — `audit`, `decode`, `fix`, `draft` — deterministic, no LLM calls, reproducible.
- **Enforcement** — pre-commit hook that turns the rules into a CI gate.

The decode mode is the differentiator: no other public resource takes an arbitrary prompt and labels which of the 12 established primitives it implements. That is the same operation as the repo's title — "decoded."

---

## Repo map

```
opus-4-7-decoded/
├── README.md                       this file
├── methodology/                    the framework: "a prompt is a program"
├── primitives/                     12 reusable building blocks
├── techniques/                     7 composition patterns
├── patterns/                       5 architectural patterns
├── annotations/                    1,408-line source walk, section by section
├── templates/                      fill-in-the-blanks skeleton + worked example
├── examples/                       before/after rewrites
├── evidence/                       line-reference index for every claim
├── source/                         pointer to CL4R1T4S (no hosted copy)
├── skills/opus-mind/               Claude Code skill — same primitives, loadable
│   ├── SKILL.md                    skill entry point (6/6 self-audit)
│   ├── scripts/                    audit.py, decode.py, fix.py, draft.py, install-hook.sh
│   ├── references/                 symlinks to primitives/, techniques/, etc.
│   └── assets/                     symlinks to templates
└── tests/
    ├── fixtures/good/              5 × 6/6 prompts
    ├── fixtures/bad/               12 × fail-exactly-one prompts
    └── test_fixtures.py            regression gate
```

---

## How to use this repo

| If you want… | Go here |
|---|---|
| The mental model | [methodology/README.md](./methodology/README.md) → primitives → patterns |
| To ship a prompt today | [templates/system-prompt-skeleton.md](./templates/system-prompt-skeleton.md) |
| To audit your existing `CLAUDE.md` | `python3 skills/opus-mind/scripts/audit.py CLAUDE.md` |
| To understand a specific Opus 4.7 section | [annotations/](./annotations/) |
| To verify every claim against source | [evidence/line-refs.md](./evidence/line-refs.md) |
| To install as a Claude Code skill | Copy `skills/opus-mind/` into your project — `SKILL.md` handles discovery |
| To gate your repo's prompt files | `bash skills/opus-mind/scripts/install-hook.sh` |

---

## What this repo is NOT

- **Not a jailbreak guide.** Every primitive is defensive — makes models harder to derail, not easier.
- **Not a Claude-only cheatsheet.** The primitives target prompt-engineering failure modes, not Claude-specific behavior. They apply to GPT, Gemini, any sufficiently capable LLM.
- **Not a summary.** A summary loses the constraint shapes (why 15 and not 20? why XML and not markdown headers? why "Step 0" not "First"?). Those shapes ARE the insight.

---

## Attribution and disclaimers

**Source file not hosted here.** The 1,408-line Opus 4.7 system prompt lives in the [CL4R1T4S mirror](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt), maintained by [@elder-plinius](https://github.com/elder-plinius). Raw URL, version pin, and rationale: [source/README.md](./source/README.md).

**Not affiliated with Anthropic.** This repo is independent third-party analysis. Nothing here is endorsed, partnered, or reviewed by Anthropic. All interpretation errors are the author's.

**Analysis posture.** Anthropic has not published this prompt. Every quotation is bounded by fair-use principles for research and critical commentary, with line references back to CL4R1T4S so readers can verify context directly.

**DMCA / takedown.** If you represent a rights-holder and believe the fair-use reasoning is incorrect for a specific passage, open an issue or email the maintainer — same-day response. The analysis framework (primitives, techniques, tools) is independent work and out of scope; only source quotations and close paraphrases are in scope.

**MIT license.** The analysis, framework, primitives, tools, and tests in this repo are original work, MIT-licensed — fork, extend, or argue with any of it.

---

## Meta-note: who built this

The reverse engineering in this repo was performed by **Claude Opus 4.7** — the same model whose system prompt is being analyzed. That is not a self-dealing conflict; it is closer to a programmer reading the decompiled binary of the compiler that compiled them. The model has no privileged access to its own system prompt at runtime — it only sees what users show it — so the analysis is derived from the leaked artifact and from behavioral observation, not from introspection. Human direction, framing, and editorial judgment guided the effort throughout; the model did the detail writing and the tool implementation.

Artifacts you can verify independently:
- Every line reference resolves to the CL4R1T4S source.
- Every `audit.py` rule is a regex plus a threshold that you can read.
- Every fixture in `tests/fixtures/` is a 20-40 line markdown file you can inspect.
- The `decode.py` output is a table you can diff against the primitive definitions.

If the self-analysis angle disqualifies the work for your use case, fair enough. Otherwise, the evidence chain is intact end-to-end.

---

## Contributing

Evidence-first contributions welcome.

Three things specifically wanted:

1. **Corroborating evidence from other leaked prompts** — do the same primitives appear in GPT / Gemini / Grok? Where do they diverge?
2. **Failure-mode case studies** — "I applied primitive X and it broke because Y" is gold.
3. **Adversarial fixtures** — prompts that game `audit.py`'s regex but are actually slop, or pass the eye test but regex-fail. These drive the scorer toward robustness.

Evidence over opinion. Line refs over vibes.
