# Opus 4.7, Decoded

Claude's own system prompt, reverse-engineered into **two tools** — one for people who build prompts, one for people who write them.

```
    LINT — for BUILDERS                       BOOST — for USERS
    ──────────────────────                     ───────────────────
    CLAUDE.md / SKILL.md                      prompts you send to Claude
    .cursorrules / AGENTS.md                  ChatGPT / Cursor / Copilot
    chatbot system prompts                    "write me a blog post..."

    audits safety, rule conflicts,            audits specification quality:
    policy tiers, refusal structure           task, length, audience, tone

    11 structural invariants                  7 spec slots
    gates the commit                          coaches the prompter
```

Both share one engine (`audit.py` + `boost.py`), one source (the 1,408-line leaked Opus 4.7 system prompt via [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)), one repo.

**한국어 버전:** [README.ko.md](./README.ko.md)

---

## Which one do I need?

**You ship an agent.** You edit `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `**/SKILL.md`, or a system prompt that goes to production. **Use LINT.** It enforces the 12 primitives Anthropic used in Opus 4.7 — decision ladders, reframe guards, tier labels, consequence statements, hard numbers.

**You use an AI daily.** You paste prompts into Claude / ChatGPT / Cursor. You often feel the answer would be better "if you'd just asked better." **Use BOOST.** It reads your prompt and points out which of the 7 slots you left empty — length, audience, format, tone, examples — and offers an LLM-powered expansion to fill them.

The two tools do not overlap. Safety and refusal design are LINT's job (the system prompt already handles that layer). Output shape and audience fit are BOOST's job (only you can fill those).

---

## BOOST — 30-second demo

```
$ opus-mind boost check "write a blog post about AI safety"
coverage: 1/7

filled slots:
  [✓] B1 task — 'write a'

empty slots — missing spec:
  [ ] B2 format       · JSON / markdown / table / bullets / prose
  [ ] B3 length       · 300 words / 5 bullets / under 200 tokens
  [ ] B4 context      · who reads this? what can they be assumed to know?
  [ ] B5 few_shot     · one example of the output you want
  [ ] B6 constraints  · tone, avoid-list
  [ ] B7 clarify      · on ambiguity — ask you or assume-and-flag?
```

```
$ opus-mind boost ask "write a blog post about AI safety"
# 6 question(s) to fill the empty slots:

B2 format:
  what output format? (JSON / markdown / table / bullets / prose)
B3 length:
  what length or scope? (e.g. 300 words / 5 bullets / 3 paragraphs)
...
```

```
$ opus-mind boost expand "write a blog post about AI safety" \
    --length "800 words" \
    --format "markdown with H2 headings" \
    --context "ML engineers, not alignment specialists" \
    --constraints "conversational, skeptical, no jargon"

# ─── emitted composition prompt (truncated) ────────────────────────────
# You are helping a user rewrite a vague prompt into a concrete one.
#
# The user's original prompt was:
# <<<
# write a blog post about AI safety
# >>>
#
# They have provided answers to the missing specification slots:
# - length: 800 words
# - format: markdown with H2 headings
# - context: ML engineers, not alignment specialists
# - constraints: conversational, skeptical, no jargon
#
# Rewrite the prompt as a single, concrete, self-contained instruction ...
```

`expand` only **emits** the composition prompt — it never calls an API. Inside a Claude Code session, the current Claude reads the emitted prompt and writes the rewritten user prompt as its reply (no extra API key, no extra cost — you're already talking to Claude). Outside Claude Code, paste the emitted text into any LLM (Claude.ai, ChatGPT, Cursor) and run it there. `check` and `ask` are likewise 100% local and deterministic.

### The 7 BOOST slots

| # | Slot | What it answers | Example value |
|---|---|---|---|
| B1 | task | verb + object | "write a 500-word summary" |
| B2 | format | output shape | "JSON with keys X, Y, Z" / "markdown table" |
| B3 | length | numeric budget | "under 300 words" / "5 bullets" |
| B4 | context | audience, background | "for ML engineers who know Python" |
| B5 | few_shot | example of desired output | "like this: <sample>" |
| B6 | constraints | tone, avoid-list | "conversational, no jargon" |
| B7 | clarify | ambiguity policy | "if unclear, assume X and flag it" |

None of these overlap with the system prompt Claude runs on — they are the slots only the user can fill.

---

## LINT — 30-second demo

```
$ opus-mind lint audit CLAUDE.md
score: 6/11
  [FAIL] I1_reduce_interpretation    hedge_density 0.42 > 0.25
  [FAIL] I2_no_rule_conflicts        26 directives, 0 decision ladders
  [FAIL] I6_failure_modes_explicit   0 consequences, need ≥ 2
  [FAIL] I8_default_exception        no default+exception pairs
  [FAIL] I9_self_check               long prompt, no self-check block
```

```
$ opus-mind lint plan CLAUDE.md
domain signals: has_tools, is_long, has_refusals
TODO — missing required primitives:
  [ ] I2_no_rule_conflicts  → 02 decision-ladders   (fix --add ladder)
  [ ] I6_failure_modes_explicit  → 04 consequence   (fix --add consequences)
  [ ] I8_default_exception  → 04 default+exception  (fix --add defaults)
  [ ] I9_self_check         → 07 self-check        (fix --add self-check)
```

```
$ opus-mind lint fix CLAUDE.md --add ladder,consequences,defaults,self-check --apply
  injected: ladder, consequences, defaults, self-check

$ opus-mind lint audit CLAUDE.md
score: 10/11
```

Install the pre-commit hook and any commit that drops `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, or any `**/SKILL.md` below threshold fails locally:

```bash
bash skills/opus-mind/scripts/install-hook.sh --threshold 6
```

### The 11 LINT invariants (structural)

| # | Primitive | What's checked | Source ref |
|---|---|---|---|
| I1 | 03 hard-numbers | hedge_density ≤ 0.25, number_density ≥ 0.10 | L664, L620 |
| I2 | 02 decision-ladders | Step N tokens, "stop at the first match" | L515–L537 |
| I3 | 09 reframe-as-signal | reframe clause when refusal content present | L33 |
| I4 | 08 anti-narration | zero forbidden preambles | L536, L560 |
| I5 | 06 example + rationale | every example has rationale | L710–L750 |
| I6 | technique 04 | consequence count ≥ directives/10 | L753–L759 |
| I7 | 01 namespace-blocks | every `{foo}` has `{/foo}` | structural |
| I8 | 04 default + exception | "default" + "unless/except/only when" co-occur | L25, L57–68 |
| I9 | 07 self-check | self-check block when prompt is long | L698–L707 |
| I10 | pattern: tier-labels | ALLCAPS multi-word token when high-stakes | L640, L657 |
| I11 | 12 hierarchical-override | Tier N tokens / X > Y > Z / "takes precedence" | L657 |

Every check is structural where possible (XML balance, numeric density, ALLCAPS shape, comparison chains). The few that use vocabulary (I3, I4, I6) keep small English-only lists cited from Opus 4.7. Author's personal anti-slop list (`delve`, `utilize`, etc.) lives in [`stylebook.py`](./skills/opus-mind/scripts/stylebook.py), opt-in via `--stylebook`.

---

## The 12 primitives (shared ground truth)

Both tools draw from the same 12 reusable primitives extracted from the Opus 4.7 source. Each has its own file in [`primitives/`](./primitives/).

| # | Primitive | Used by | One-line rule |
|---|---|---|---|
| 01 | [Namespace blocks](./primitives/01-namespace-blocks.md) | lint | XML section tags as scoped modules |
| 02 | [Decision ladders](./primitives/02-decision-ladders.md) | lint | `Step 0 → N`, first-match-wins |
| 03 | [Hard numbers](./primitives/03-hard-numbers.md) | **both** | "15 words" beats "keep it short" |
| 04 | [Default + exception](./primitives/04-default-plus-exception.md) | lint | Strong default, explicit opt-in list |
| 05 | [Cue-based matching](./primitives/05-cue-based-matching.md) | — | Teach signals, not flowcharts |
| 06 | [Example + rationale](./primitives/06-example-plus-rationale.md) | **both** | Every example carries its "why" |
| 07 | [Self-check assertions](./primitives/07-self-check-assertions.md) | lint | Runtime checklist before emit |
| 08 | [Anti-narration](./primitives/08-anti-narration.md) | lint | Hide internal machinery |
| 09 | [Reframe-as-signal](./primitives/09-reframe-as-signal.md) | lint | Softening a request IS the refusal |
| 10 | [Asymmetric trust](./primitives/10-asymmetric-trust.md) | — | Different claims, different bars |
| 11 | [Capability disclosure](./primitives/11-capability-disclosure.md) | — | Tell the model what it doesn't know |
| 12 | [Hierarchical override](./primitives/12-hierarchical-override.md) | lint | Safety > user > helpfulness |

Primitives 03 and 06 appear in both tools: hard numbers (user should say "300 words", builder should say "< 15 word quotes") and examples with rationale (user's few-shot, builder's `{example}{rationale}` structure) are universal — neither audience can offload them to the other side.

Primitives 05, 10, 11 are present in the methodology docs but not gated by either tool (require semantic understanding beyond regex).

---

## 60-second install

```bash
git clone https://github.com/<user>/opus-4-7-decoded
cd opus-4-7-decoded

# LINT
opus-mind=skills/opus-mind/scripts/opus-mind
$opus-mind lint audit path/to/CLAUDE.md
$opus-mind lint plan  path/to/CLAUDE.md
bash skills/opus-mind/scripts/install-hook.sh --threshold 6

# BOOST
$opus-mind boost check "your prompt here"
$opus-mind boost ask   "your prompt here"
$opus-mind boost expand "your prompt" --length "300 words" --format markdown
```

Works on any file format — the tools score the **shape**, not the topic. Korean, English, Cursor rules, Claude skills, GPTs instructions, system-prompt markdown — all accepted.

---

## Dogfooding

Every claim in this README is backed by tests, fixtures, or both.

```
$ python3 -m pytest tests/ skills/opus-mind/tests/ -q
103 passed, 4 skipped
```

- **The Opus 4.7 source itself scores 11/11 on lint.** `tests/test_dogfood.py` fetches the CL4R1T4S mirror on every run and asserts `score == 11/11`. Non-negotiable — if the auditor fails the document it was extracted from, the auditor is wrong.
- **The skill's own `SKILL.md` scores 11/11.** Regression-tested.
- 5 golden-good + 12 golden-bad lint fixtures — each bad file fails exactly one known invariant.
- 3 boost fixtures — filled (7/7), empty (≤ 2/7), and a partial case pinning exact slot fills.
- Pre-commit hook on this repo's `.git/hooks/pre-commit`: any commit regressing a prompt file below threshold fails locally.

### External prompt scores (LINT, live from CL4R1T4S)

| Source | Score | Chief gaps |
|---|---|---|
| Claude Opus 4.7 | **11/11** | — (canonical) |
| OpenAI Codex | 7/11 | I2 ladder, I8 default, I9 self-check, I10 tier labels |
| Cursor 2.0 | 6/11 | I1 numbers, I2 ladder, I6 consequence, I8 default, I9 self-check |
| ChatGPT-5 | 4/11 | I1, I2, I3, I5, I6, I9, I11 |

These are findings, not verdicts. A 6/11 means the prompt isn't written in the 12-primitive style — not that the product is bad.

---

## Why this matters (LINT)

Prompts rot. Without a gate, every team's `CLAUDE.md` drifts into hedge-and-slop mush in 6 months — nobody lints it, reviewers negotiate style opinions, and a `never X` silently becomes `typically avoid X` across three PRs. LINT is ESLint for that file.

| Scenario | The specific save |
|---|---|
| **Solo Claude Code user** | You paste model-suggested lines into CLAUDE.md that smuggle in `leverage` / `generally` / `Let me`. The hook catches the regression at commit time, not 3 months later when Claude starts narrating. |
| **Team-shared `CLAUDE.md`** | 10+ devs editing one file. One objective hard-line, PR reviewers stop arguing style and let the script fail instead. |
| **Production agent deploys** | A PR that weakens `refuses X` → `typically avoids X` is a policy change shipped by accident. Hook blocks before merge. |
| **Claude Code skill marketplace** | "Passes opus-mind ≥ 5/11" is a credible quality signal. |
| **Multi-AI repos** | `.cursorrules` + `CLAUDE.md` + `GEMINI.md` drifting independently. One quality floor across all. |
| **Regulated deployments** | Audit trail: `git log` + score history = "when exactly did the refusal set shrink?" in one query. |

## Why this matters (BOOST)

Most AI users paste one-liners and accept whatever comes back. The ones who get great answers don't have more talent — they fill more slots. BOOST makes the slot list visible.

| Scenario | The specific save |
|---|---|
| **You know what you want but can't pin it down** | BOOST asks the 6 questions that turn your gut feel into concrete instruction. |
| **You get mid answers and don't know why** | `check` shows which of the 7 slots were empty — usually length, audience, or constraints. |
| **You repeat the same task with different prompts** | Use `expand` once, save the output, reuse. |
| **You coach juniors on prompting** | Hand them `boost check` instead of a 20-page guide. |
| **You're building a prompt library** | Every saved prompt can pass `check` at 6–7/7 before it lands. |

---

## Architecture

```
opus-4-7-decoded/
├── README.md                      this file
├── methodology/                   the framework (primitives are a program)
├── primitives/                    12 reusable building blocks
├── techniques/                    7 composition patterns
├── patterns/                      5 architectural patterns
├── annotations/                   1,408-line source walk
├── templates/                     builder scaffolds
├── source/                        CL4R1T4S pointer (no hosted copy)
├── skills/opus-mind/              the skill — import anywhere
│   ├── SKILL.md                   Claude Code entry point
│   └── scripts/
│       ├── audit.py               LINT: 11-invariant scorer
│       ├── plan.py                LINT: domain inference + TODO
│       ├── fix.py                 LINT: rewrite + skeleton injection
│       ├── decode.py              LINT: primitive labeler
│       ├── boost.py               BOOST: check / ask / expand
│       ├── stylebook.py           opt-in author preferences
│       ├── install-hook.sh        pre-commit installer
│       └── opus-mind              unified CLI (lint | boost)
└── tests/
    ├── fixtures/good/             lint good (5 × 11/11)
    ├── fixtures/bad/              lint bad (12 × fail-one)
    ├── fixtures/stylebook/        stylebook-only
    ├── fixtures/boost/            boost fixtures (filled/empty/partial)
    ├── test_fixtures.py           lint regression
    ├── test_dogfood.py            Opus 4.7 must score 11/11
    └── test_boost.py              boost regression
```

## How to use this repo

| If you want… | Go here |
|---|---|
| The mental model | [methodology/README.md](./methodology/README.md) → primitives → patterns |
| To ship a better CLAUDE.md today | `opus-mind lint audit CLAUDE.md` → `lint plan` → `lint fix --add` |
| To write a better one-off prompt | `opus-mind boost check "..."` → `boost ask` → `boost expand` |
| A skeleton to start from (builder) | [templates/system-prompt-skeleton.md](./templates/system-prompt-skeleton.md) |
| To understand a specific Opus 4.7 section | [annotations/](./annotations/) |
| To verify every claim against source | [evidence/line-refs.md](./evidence/line-refs.md) |
| To install as a Claude Code skill | Copy `skills/opus-mind/` into your project |
| To gate your repo's prompt files | `bash skills/opus-mind/scripts/install-hook.sh` |

---

## What this repo is NOT

- **Not a jailbreak guide.** Every primitive is defensive — makes models harder to derail.
- **Not Claude-only.** Primitives target prompt-engineering failure modes, not model-specific behavior. LINT targets agent-prompt files regardless of which LLM consumes them. BOOST renders prompts usable by any LLM.
- **Not a summary of Opus 4.7.** A summary loses the constraint shapes. Those shapes ARE the insight.

---

## Attribution

**Source file not hosted here.** The 1,408-line Opus 4.7 system prompt lives at the [CL4R1T4S mirror](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt), maintained by [@elder-plinius](https://github.com/elder-plinius). Raw URL, version pin, rationale: [source/README.md](./source/README.md).

**Not affiliated with Anthropic.** Independent third-party analysis. No endorsement, partnership, or review by Anthropic. All interpretation errors are the author's.

**Analysis posture.** Every quotation bounded by fair-use for research and critical commentary, with line references back to CL4R1T4S so readers can verify context directly.

**DMCA / takedown.** Rights-holders: open an issue or email the maintainer. Same-day response. Analysis framework (primitives, tools, tests) is independent work and out of scope; only source quotations and close paraphrases are in scope.

**MIT license.** Fork, extend, argue with any of it.

---

## Meta-note: who built this

The reverse engineering was performed by **Claude Opus 4.7** — the same model whose system prompt is being analyzed. That is not a self-dealing conflict; it is closer to a programmer reading the decompiled binary of the compiler that compiled them. The model has no privileged access to its own system prompt at runtime — it only sees what users show it — so the analysis is derived from the leaked artifact and from behavioral observation, not from introspection. Human direction, framing, and editorial judgment guided the effort; the model did the detail writing and tool implementation.

Artifacts you can verify independently:
- Every line reference resolves to the CL4R1T4S source.
- Every `audit.py` and `boost.py` rule is a regex plus a threshold.
- Every fixture is an inspectable markdown file.
- `decode.py` output is diffable against the primitive definitions.

---

## Contributing

Evidence-first contributions welcome.

Three things specifically wanted:

1. **Corroborating evidence from other leaked prompts** — do the same primitives appear in GPT / Gemini / Grok? Where do they diverge?
2. **BOOST slot additions** — found a consistent prompting axis we missed? Propose it with 2 fixtures (filled + empty).
3. **Failure-mode case studies** — "I applied primitive X and it broke because Y" is gold.

Evidence over opinion. Line refs over vibes.
