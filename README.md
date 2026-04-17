# Opus 4.7, Decoded

> **Anthropic did the prompt-engineering homework on a 1,408-line system prompt.
> You get the answer key.**

Claude runs on a 1,408-line system prompt Anthropic never officially published.
We reverse-engineered the leaked version (via [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S))
into **one Claude Code skill with two products**:

- **LINT** — grades your `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or
  `**/SKILL.md` against 11 structural invariants Anthropic uses on Opus 4.7
  itself. Every rule anchors to a specific line in the leaked source.
- **BOOST** — coaches your daily one-shot prompts to Claude / ChatGPT /
  Cursor through 10 slots: 7 specification slots from Anthropic's public
  prompt-engineering docs + 3 reasoning slots (chain-of-thought, verification,
  decomposition) from Wei 2022, Shinn 2023, Zhou 2022.

One skill. Two products. Zero API keys. **156 passing tests**, one of which
live-fetches the Opus 4.7 source on every run and asserts it still scores
11/11 on our own auditor — if we're wrong about the patterns, that test
breaks first.

```
    LINT — for BUILDERS                       BOOST — for USERS
    ──────────────────────                     ───────────────────
    CLAUDE.md / SKILL.md                      prompts you send to Claude
    .cursorrules / AGENTS.md                  ChatGPT / Cursor / Copilot
    chatbot system prompts                    "write me a blog post..."

    audits rule conflicts,                    audits specification quality:
    policy tiers, refusal structure           task, format, length, audience
    + chain-of-thought, verification,
      decomposition requests

    11 structural invariants                  10 slots (7 spec + 3 reasoning)
    gates the commit                          coaches the prompter
```

**한국어 버전:** [README.ko.md](./README.ko.md)

---

## The story

**Act 1 — Setup.** Anthropic ships Claude Opus 4.7. Inside, a 1,408-line
system prompt steers everything the model does. Months of work. A team of
prompt engineers. Never officially published.

**Act 2 — Conflict.** Everyone else writes prompts by vibes. Your
`CLAUDE.md`, your `.cursorrules`, your chatbot system prompt — none get
anywhere near that discipline. The quality gap shows up in your agent's
behaviour, your answer quality, and your refusal design. You know it. You
just don't have a way to measure or fix it.

**Act 3 — Reveal.** The 1,408-line prompt leaked (CL4R1T4S archive). We
read every line. Extracted 12 primitives, 11 invariants, 7 techniques,
10 BOOST slots. Packaged as a Claude Code skill + CLI + pre-commit hook.
Deterministic engine, 0 LLM calls, 156 passing tests. Every rule anchored
to `source/opus-4.7.txt:L###`.

**Act 4 — Use.** Now the engineering Anthropic did for itself is a tool
you can run on yours:

```bash
opus-mind lint audit CLAUDE.md       # graded by Anthropic's own invariants
opus-mind boost check "your prompt"  # coached through 10 spec + reasoning slots
```

---

## Why this exists (vs other prompt linters)

Existing prompt linters — [promptsage](https://github.com/alexmavr/promptsage),
[gptlint](https://github.com/gptlint/gptlint),
[vibe-linter](https://github.com/sidhxntt/Vibe-Coding-Bundle) —
all share three problems:

| Problem | Why it matters | opus-mind |
|---|---|---|
| "Best practices" come from vibes | No evidence chain, no reproducibility | Every rule anchors to a specific line in Claude's own leaked system prompt |
| Linter calls an LLM to score | Non-reproducible, API cost per commit, slow, environment-dependent | Pure regex + counts, 80ms per file, 0 API calls, works offline |
| One tool for one audience | Covers only half of prompt engineering | Two products share one source + one engine: LINT (builders) + BOOST (users) |

**"The only prompt linter where every rule traces to a specific line of Claude's own system prompt."**

---

## 30-second demo

### LINT — grade a system prompt

```
$ opus-mind lint audit ~/.claude/CLAUDE.md
path: /home/yunsu/.claude/CLAUDE.md
lines: 220
score: 8/11   verdict: BORDERLINE

  [PASS] I1  reduce_interpretation     (hedge_density 0.12 ≤ 0.25)
  [PASS] I2  no_rule_conflicts         (3 ladders found for 26 directives)
  [FAIL] I6  failure_modes_explicit    0 consequences, need ≥ 2
  [PASS] I7  namespace_balance         (all {foo}…{/foo} matched)
  [FAIL] I9  self_check                long prompt without pre-emit checklist
  [FAIL] I10 tier_labels               refusal content without SEVERE VIOLATION-style markers

  L42 [I6] 'The bot must cite sources' — no consequence attached
  L88 [I10] 'never share other users' data' — no ALLCAPS severity marker
```

### BOOST — coach a daily prompt

```
$ opus-mind boost check "write a blog post about AI safety"
coverage: 1/10    task_type: write

filled:
  [✓] B1  task — 'write a'

empty, ranked by impact for task_type=write:
  [ ] B4  context        ← ask first (for 'write' tasks, audience dominates)
  [ ] B6  constraints    · tone / avoid-list
  [ ] B3  length         · 300 words / 5 bullets / under 200 tokens
  [ ] B2  format         · markdown / table / bullets / prose
  [ ] B5  few_shot       · one example of the output you want
  [ ] B10 decomposition  · plan-before-execute for long pieces
  [ ] B8  reasoning      · step-by-step thinking for complex claims
  [ ] B9  verification   · check each factual claim before emitting
  [ ] B7  clarify        · ambiguity policy
```

`boost ask` then fires **one** question via `AskUserQuestion` — the B4 one
for this task type — waits for the answer, and re-ranks. When coverage hits
7/10, `boost expand` emits a composition prompt the surrounding Claude uses
to write the actual rewritten prompt in the same session. No API call.

---

## Which one do I need?

**You ship an agent.** You edit `CLAUDE.md`, `AGENTS.md`, `.cursorrules`,
`**/SKILL.md`, or a production chatbot system prompt. **Use LINT.** It
enforces the 12 primitives Anthropic used in Opus 4.7 — decision ladders,
reframe guards, tier labels, consequence statements, hard numbers.

**You use an AI daily.** You paste prompts into Claude / ChatGPT / Cursor
and often feel the answer would be better "if you'd just asked better."
**Use BOOST.** It reads your prompt, points out which of the 10 slots you
left empty, and — for complex tasks — asks whether you want chain-of-thought,
self-verification, and decomposition directives folded in.

The two tools don't overlap. Safety and refusal design are LINT's job (the
system prompt handles that layer). Output shape, audience fit, and reasoning
technique are BOOST's job (only you can fill those).

---

## Install

**Claude Code skill (recommended):**

```bash
git clone https://github.com/<user>/opus-4-7-decoded
cd opus-4-7-decoded
bash skills/opus-mind/scripts/install-skill.sh
```

Restart Claude Code. Then just talk to it — "audit my CLAUDE.md", "help me
improve this prompt", "my bot keeps relenting after refusals". Claude reads
SKILL.md, runs the Python helpers under the hood, composes a response with
line refs and a ranked action plan. No API key, no extra cost — you're
already talking to Claude.

**Standalone CLI (pre-commit hooks, CI, scripts):**

```bash
opus_mind=skills/opus-mind/scripts/opus-mind

# LINT
$opus_mind lint audit path/to/CLAUDE.md
$opus_mind lint plan  path/to/CLAUDE.md
bash skills/opus-mind/scripts/install-hook.sh --threshold 6

# BOOST
$opus_mind boost check "your prompt here"
$opus_mind boost ask   "your prompt here"
$opus_mind boost expand "your prompt" --length "300 words" --format markdown
```

Works on any format — tools score **shape**, not topic. Korean, English,
Cursor rules, Claude skills, GPT instructions, system-prompt markdown —
all accepted. Non-English prompts: the Python regex layer is English-centric,
but SKILL.md instructs Claude to override slot detection with its own
language judgment when the prompt isn't English.

---

## The proof

Every claim in this README passes pytest — **156 tests** plus 4 live-fetch
skips when offline.

```
$ python3 -m pytest tests/ skills/opus-mind/tests/ -q
156 passed, 4 skipped in 2.47s
```

- **The Opus 4.7 source itself scores 11/11.** `tests/test_dogfood.py`
  fetches the CL4R1T4S mirror on every run and asserts `score == 11/11`.
  Non-negotiable — if the auditor fails the document it was extracted from,
  the auditor is wrong.
- **Anthropic's canonical BOOST prompts score ≥ 5/7.** `test_boost_dogfood.py`
  pulls reference prompts from Anthropic's public prompt-engineering docs
  and asserts they pass our specification layer.
- 5 golden-good + 12 golden-bad LINT fixtures, each failing exactly one
  known invariant.
- Reasoning-layer false-positive guards — imperative sequences ("first X,
  then Y") and verb use ("check the docs") must NOT trigger B8-B10.
- Iron-Law `test_skill_orchestration.py` locks the JSON schema contracts
  SKILL.md depends on (verdict enum, TL;DR loadability for every primitive,
  no-API-call grep across the tree).

### External prompt scores (LINT, live from CL4R1T4S)

Re-scored 2026-04-17 with the new auditor (verdict, thin-content gate,
placeholder penalty applied). Each entry links to the source.

| Source | Score | Verdict | Chief gaps |
|---|---|---|---|
| [Claude Opus 4.7](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) | **11/11** | GOOD | — (canonical; the prompt this repo was extracted from) |
| [Cursor Prompt](https://github.com/elder-plinius/CL4R1T4S/blob/main/CURSOR/Cursor_Prompt.md) | 6/11 | BORDERLINE | I1 numbers, I2 ladder, I8 default+exception, I9 self-check, I10 tier labels |
| [ChatGPT-5 (Aug 2025)](https://github.com/elder-plinius/CL4R1T4S/blob/main/OPENAI/ChatGPT5-08-07-2025.mkd) | 4/11 | POOR | I1, I2, I3, I5, I6, I9, I11 |
| [Claude Code (March 2024)](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude_Code_03-04-24.md) | 7/11 | BORDERLINE | I2 ladder, I3 reframe, I8 default+exception, I10 tier labels |

Reproduce with:

```bash
curl -s https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/main/CURSOR/Cursor_Prompt.md \
  | python3 skills/opus-mind/scripts/audit.py -
```

These are **findings**, not verdicts on the product. A 6/11 means the
prompt isn't written in the 12-primitive style — not that the product
is bad. Shorter prompts score lower on I9 (self-check) and I10 (tier
labels) because those invariants only trigger when the prompt is long
enough or stakes-heavy enough to require them.

---

## Where LINT saves you

Prompts rot. Without a gate, every team's `CLAUDE.md` drifts into
hedge-and-slop mush in 6 months — nobody lints it, reviewers negotiate
style opinions, and a `never X` silently becomes `typically avoid X` across
three PRs. LINT is ESLint for that file.

| Scenario | The specific save |
|---|---|
| **Solo Claude Code user** | Model-suggested lines smuggle `leverage` / `generally` / `Let me` into your CLAUDE.md. Hook catches the regression at commit time, not 3 months later when Claude starts narrating. |
| **Team-shared `CLAUDE.md`** | 10+ devs editing one file. One objective hard-line. PR reviewers stop arguing style — the script fails instead. |
| **Production agent deploys** | A PR weakening `refuses X` → `typically avoids X` is a policy change shipped by accident. Hook blocks before merge. |
| **Skill marketplace** | "Passes opus-mind ≥ 5/11" is a credible quality signal for third-party skills. |
| **Multi-AI repos** | `.cursorrules` + `CLAUDE.md` + `GEMINI.md` drifting independently. One quality floor across all. |
| **Regulated deployments** | Audit trail: `git log` + score history answers "when exactly did the refusal set shrink?" in one query. |

## Where BOOST saves you

Most AI users paste one-liners and accept whatever comes back. The ones
who get great answers don't have more talent — they fill more slots.
BOOST makes the slot list visible, then (for complex tasks) adds the
reasoning directives published research says matter.

| Scenario | The specific save |
|---|---|
| **You know what you want but can't pin it down** | BOOST asks the 6-9 questions that turn gut feel into concrete instruction. |
| **You get mid answers and don't know why** | `check` shows which slots were empty — usually length, audience, or constraints. |
| **Complex code/analysis tasks** | B10 (decomposition) + B8 (CoT) + B9 (verification) fold in automatically — rising the answer quality without you remembering the paper names. |
| **You repeat the same task with different prompts** | Use `expand` once, save the output, reuse. |
| **You coach juniors on prompting** | Hand them `boost check` instead of a 20-page guide. |
| **You're building a prompt library** | Every saved prompt can pass `check` at 7+/10 before it lands. |

---

## Architecture

The skill is the product. The CLI is the escape hatch.

```
Claude Code session
│
├── Claude reads SKILL.md (Phase-based flows, JSON schemas)
├── Claude runs Python helpers with --json (deterministic work)
│      │
│      ├── audit.py    → verdict, 11 invariants, findings, placeholder count
│      ├── plan.py     → domain, required primitives, missing list
│      ├── decode.py   → 12 primitive detections
│      ├── boost.py    → 10-slot coverage, task-type inference, impact ranking
│      └── symptom_search.py → symptom → primitive pointer
│
├── Claude reads primitive docs (TL;DR quotes) for the user's context
└── Claude composes the response in natural prose with line refs
```

Python is deterministic, **0 LLM calls**. Synthesis — composing rewritten
prompts, applying crosscheck reviews, handling non-English prompts where
regex falls short — is Claude's job in the surrounding session. No API
key anywhere.

<details>
<summary><strong>The 11 LINT invariants (click to expand)</strong></summary>

Every signal set in `audit.py` is traceable to specific lines in the
CL4R1T4S mirror.

| ID | Primitive | Signal | Source |
|---|---|---|---|
| I1  | 03 hard-numbers         | hedge_density ≤ 0.25, number_density ≥ 0.10 | L664, L620 |
| I2  | 02 decision-ladders     | Step N tokens + stop-at-first-match         | L515–L537 |
| I3  | 09 reframe-as-signal    | reframe clause when refusal content present | L33 |
| I4  | 08 anti-narration       | zero forbidden preambles                    | L536, L560 |
| I5  | 06 example + rationale  | every example carries a rationale           | L710–L750 |
| I6  | technique 04            | consequences ≥ directives / 10              | L753–L759 |
| I7  | 01 namespace-blocks     | every `{foo}` has `{/foo}`                  | structural |
| I8  | 04 default + exception  | default + (unless/except/only-when) cooccur | L25, L57–68 |
| I9  | 07 self-check           | self-check block when prompt is long        | L698–L707 |
| I10 | pattern: tier-labels    | ALLCAPS multi-word markers for high-stakes  | L640, L657 |
| I11 | 12 hierarchical-override| Tier N / X > Y > Z / "takes precedence"     | L657 |

Plus `verdict`: THIN / POOR / BORDERLINE / GOOD. Plus `placeholder_count` —
`<FIXME>`, `[TODO]`, `TBD`, `???`, `XXX`, `tk tk` remnants block the GOOD
verdict even if every invariant passes.
</details>

<details>
<summary><strong>The 10 BOOST slots (click to expand)</strong></summary>

**Specification layer** — grounded in Anthropic public prompt-engineering
docs:

| ID | Slot | Question it answers |
|---|---|---|
| B1 | task        | What to produce (imperative verb + object) |
| B2 | format      | Output shape (JSON / markdown / bullets / prose) |
| B3 | length      | Numeric budget (words / tokens / lines / bullets) |
| B4 | context     | Audience + background |
| B5 | few_shot    | Example of desired output |
| B6 | constraints | Tone / style / avoid-list |
| B7 | clarify     | Ambiguity policy (ask vs assume + flag) |

**Reasoning layer** — grounded in `evidence/smart-prompting-refs.md`:

| ID | Slot | Technique | Source |
|---|---|---|---|
| B8  | reasoning     | Ask for step-by-step / outline-first thinking | Wei 2022 (CoT) |
| B9  | verification  | Ask for self-check / flag uncertain claims    | Shinn 2023 (Reflexion) |
| B10 | decomposition | Ask for plan-before-execute / break into subtasks | Zhou 2022 (Least-to-most) |

Task type (code / analyze / research / write / short / unknown) drives
dynamic slot ranking: code tasks surface B10 first, creative writing
surfaces B4 first, short one-offs skip the reasoning layer entirely.
</details>

<details>
<summary><strong>Repo layout (click to expand)</strong></summary>

```
opus-4-7-decoded/
├── README.md                      this file
├── methodology/                   the framework (primitives are a program)
├── primitives/                    12 reusable building blocks (each ## TL;DR)
├── techniques/                    7 composition patterns (each ## TL;DR)
├── patterns/                      5 architectural patterns
├── annotations/                   1,408-line source walk
├── templates/                     builder scaffolds
├── source/                        CL4R1T4S pointer (no hosted copy)
├── evidence/
│   ├── line-refs.md               LINT — Opus 4.7 line anchors
│   └── smart-prompting-refs.md    BOOST reasoning layer — Wei / Shinn / Zhou + docs
├── skills/opus-mind/              the skill — install via install-skill.sh
│   ├── SKILL.md                   primary UX: phase-based flows + JSON schemas
│   └── scripts/
│       ├── audit.py               LINT: 11-invariant scorer (--json primary)
│       ├── plan.py                LINT: domain inference + required invariants
│       ├── fix.py                 LINT: rewrite + skeleton injection
│       ├── decode.py              LINT: primitive labeler
│       ├── boost.py               BOOST: check / ask / expand (10 slots)
│       ├── symptom_search.py      DEBUG: symptom → primitive pointer
│       ├── stylebook.py           opt-in author preferences
│       ├── install-skill.sh       register at ~/.claude/skills/opus-mind/
│       ├── install-hook.sh        git pre-commit installer
│       └── opus-mind              CLI escape hatch (lint | boost | crosscheck)
└── tests/
    ├── fixtures/good/             lint good (5 × 11/11)
    ├── fixtures/bad/              lint bad (12 × fail-one)
    ├── fixtures/stylebook/        stylebook-only
    ├── fixtures/boost/            boost fixtures (filled/empty/partial + reasoning-FP)
    ├── test_fixtures.py           lint regression
    ├── test_dogfood.py            Opus 4.7 must score 11/11 live
    ├── test_boost_dogfood.py      Anthropic canonical prompts must score ≥ 5/7
    └── (in skills/) test_skill_orchestration.py — Iron-Law contracts
```
</details>

---

## How to use this repo

| If you want… | Go here |
|---|---|
| The mental model | [methodology/README.md](./methodology/README.md) → primitives → patterns |
| To ship a better `CLAUDE.md` today | `opus-mind lint audit CLAUDE.md` → `lint plan` → `lint fix --add` |
| To write a better one-off prompt | `opus-mind boost check "..."` → `boost ask` → `boost expand` |
| A skeleton to start from (builder) | [templates/system-prompt-skeleton.md](./templates/system-prompt-skeleton.md) |
| To understand a specific Opus 4.7 section | [annotations/](./annotations/) |
| To verify every claim against source | [evidence/line-refs.md](./evidence/line-refs.md) |
| To verify reasoning-layer citations | [evidence/smart-prompting-refs.md](./evidence/smart-prompting-refs.md) |
| To install as a Claude Code skill | `bash skills/opus-mind/scripts/install-skill.sh` |
| To gate your repo's prompt files | `bash skills/opus-mind/scripts/install-hook.sh` |

---

## What this repo is NOT

- **Not a jailbreak guide.** Every primitive is defensive — makes models
  harder to derail, not easier.
- **Not Claude-only.** Primitives target prompt-engineering failure modes,
  not model-specific behaviour. LINT targets agent-prompt files regardless
  of which LLM consumes them. BOOST renders prompts usable by any LLM.
- **Not a summary of Opus 4.7.** A summary loses the constraint shapes
  (why 15 words and not 20? why XML blocks and not markdown headers? why
  "Step 0" and not "First"?). Those shapes ARE the insight.
- **Not an Anthropic product.** Independent third-party analysis. No
  endorsement, partnership, or review by Anthropic.

---

## We did

- **"Anthropic did the prompt-engineering homework on a 1,408-line system prompt. You get the answer key."**
- **"The only prompt linter where every rule traces to a specific line of Claude's own system prompt."**
- **"Python does the regex. Claude does the thinking. Zero API keys, zero vibes."**
- **"Two prompt engineering products with one source of truth: the 1,408-line leaked Opus 4.7 system prompt."**
- **"Your AI product deserves the same prompt engineering Anthropic gave Opus. Now it can have it."**

---

## Attribution

**Source file not hosted here.** The 1,408-line Opus 4.7 system prompt lives at the [CL4R1T4S mirror](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt), maintained by [@elder-plinius](https://github.com/elder-plinius). Raw URL, version pin, rationale: [source/README.md](./source/README.md).

**Not affiliated with Anthropic.** Independent third-party analysis. No endorsement, partnership, or review by Anthropic. All interpretation errors are the author's.

**Analysis posture.** Every quotation bounded by fair-use for research and critical commentary, with line references back to CL4R1T4S so readers can verify context directly.

**DMCA / takedown.** Rights-holders: open an issue or email the maintainer. Same-day response. The analysis framework (primitives, tools, tests) is independent work and out of scope; only source quotations and close paraphrases are in scope.

**MIT license.** Fork, extend, argue with any of it.

---

## Meta-note: who built this

The reverse engineering was performed by **Claude Opus 4.7** — the same model whose system prompt is being analyzed. That is not a self-dealing conflict; it is closer to a programmer reading the decompiled binary of the compiler that compiled them. The model has no privileged access to its own system prompt at runtime — it only sees what users show it — so the analysis is derived from the leaked artifact and from behavioural observation, not from introspection. Human direction, framing, and editorial judgment guided the effort; the model did the detail writing and tool implementation.

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
2. **BOOST slot additions** — found a consistent prompting axis we missed? Propose it with 2 fixtures (filled + empty) and a citation.
3. **Failure-mode case studies** — "I applied primitive X and it broke because Y" is gold.
