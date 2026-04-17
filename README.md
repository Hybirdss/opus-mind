# opus-mind

A linter for `CLAUDE.md`-style system prompts, built from the 1,408-line
Opus 4.7 system prompt that leaked via [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S).
Ships as a Claude Code skill and a CLI. Every rule links to a specific
line in the source. No LLM calls in the scorer — it's regex and counts.

```
$ opus-mind lint audit ~/.claude/CLAUDE.md
score: 10/11   verdict: BORDERLINE
  [FAIL] I6  failure_modes_explicit   0 consequences, need ≥ 1

  L42 'the bot must cite sources' — no consequence attached
```

There's a second tool inside the same skill for the other half of
prompt work — the one-shot requests you send to Claude / ChatGPT /
Cursor every day.

```
$ opus-mind boost check "write a blog post about AI safety"
coverage: 1/10    task_type: write

empty, ranked by impact:
  [ ] B4 context        for 'write' tasks, audience dominates
  [ ] B6 constraints    tone / avoid-list
  [ ] B3 length         300 words / 5 bullets / under 200 tokens
  ...
```

**한국어**: [README.ko.md](./README.ko.md)

```
    LINT — system prompts                     BOOST — user prompts
    ─────────────────────                      ─────────────────────
    CLAUDE.md / AGENTS.md                     prompts you send to an LLM
    .cursorrules / SKILL.md                   "write me a blog post..."

    11 structural invariants                  10 slots (7 spec + 3 reasoning)
    audits agent-design quality               audits specification quality
    gates the commit                          coaches the prompter
```

---

## What this is for

This repo is aimed at the safety of AI-based products you ship, not at
making an LLM smarter. The point is keeping consumer-facing AI from
producing the unexpected outputs that turn into incidents — the refusal
that slips, the instruction that leaks, the rule that drifts after a
few polite re-asks.

The Opus 4.7 source this repo reverse-engineers was written with the
same priority. Those 1,408 lines are mostly load-bearing guardrails,
not capability tuning. opus-mind inherits that framing: LINT hardens a
production system prompt against the failure modes Anthropic was
writing against.

(If you want to tune capability — chain-of-thought, tool use, output
format — that's what the BOOST half is for, on the user-prompt side.
Different job.)

---

## Why I wrote this

My `CLAUDE.md` rotted. I started with sharp rules, kept pasting in
model-suggested lines, and a few months later noticed a `never X` had
become `typically avoid X`. No reviewer to catch it, no objective bar
to measure against.

The leaked Opus 4.7 prompt turned out to be the bar. 1,408 lines of
rules Anthropic ships to their flagship model. Every pattern you'd
want in a production prompt is in there, already calibrated: hard
numbers instead of adjectives, decision ladders instead of unordered
lists, reframe-as-signal to catch jailbreak drift. I extracted the
patterns, wrote regexes that detect them (and their absence), and
packaged the result as a linter.

BOOST came later. Same engine idea, different target — instead of
grading a system prompt I didn't write, it coaches a chat prompt I
*am* writing, by pointing at the 10 slots that separate a good prompt
from a vague one.

---

## Install

Inside Claude Code (recommended):

```bash
git clone https://github.com/Hybirdss/opus-mind
cd opus-mind
bash skills/opus-mind/scripts/install-skill.sh
```

Then restart Claude Code and talk to it normally — "audit my
CLAUDE.md", "my bot keeps relenting after refusals", "help me improve
this prompt". Claude reads the skill, runs the helpers under the
hood, composes a response. No API key; you're already talking to
Claude.

Standalone (pre-commit hook, CI, scripts):

```bash
opus_mind=skills/opus-mind/scripts/opus-mind

$opus_mind lint audit path/to/CLAUDE.md        # score + findings
$opus_mind lint critic path/to/CLAUDE.md       # audit → fix → re-audit loop
$opus_mind lint seed --type customer-bot       # skeleton that scores 9+/11 out of the box

$opus_mind boost check "your prompt here"
$opus_mind boost ask   "your prompt here"      # one question at a time
$opus_mind boost expand "your prompt" --length "300 words" --format markdown
```

Gate commits on a threshold:

```bash
bash skills/opus-mind/scripts/install-hook.sh --threshold 6
```

---

## What it catches

**LINT — 11 invariants.** Every signal anchors to a specific line in
the Opus 4.7 source.

| ID | What it checks | Opus 4.7 source |
|---|---|---|
| I1  | hedge density ≤ 0.25, number density ≥ 0.10 | L664, L620 |
| I2  | `Step N → ...` ladders for routing            | L515–L537 |
| I3  | reframe-as-signal when refusal content present | L33 |
| I4  | zero narration preambles                      | L536, L560 |
| I5  | examples carry rationale                      | L710–L750 |
| I6  | consequence statements scale with directives  | L753–L759 |
| I7  | `{foo}…{/foo}` blocks balanced                | structural |
| I8  | default + exception co-occur                  | L25, L57–68 |
| I9  | self-check block for long prompts             | L698–L707 |
| I10 | ALLCAPS tier labels on high-stakes content    | L640, L657 |
| I11 | hierarchical override / Tier chain            | L657 |

Two extras beyond pass/fail: a `verdict` enum (THIN / POOR /
BORDERLINE / GOOD) and a placeholder count — `<FIXME>`, `[TODO]`,
`TBD`, `???`, `XXX` remnants block the GOOD verdict even if the 11
structural checks pass.

**BOOST — 10 slots.** Specification layer (B1–B7) grounded in
Anthropic's public prompt docs. Reasoning layer (B8–B10) grounded in
`evidence/smart-prompting-refs.md`.

| ID | Slot | Source |
|---|---|---|
| B1  | task                 | Anthropic docs |
| B2  | format               | Anthropic docs |
| B3  | length               | Anthropic docs |
| B4  | context              | Anthropic docs |
| B5  | few-shot             | Anthropic docs |
| B6  | constraints          | Anthropic docs |
| B7  | clarify              | Anthropic docs |
| B8  | reasoning (CoT)      | Wei 2022 |
| B9  | verification         | Shinn 2023 (Reflexion) |
| B10 | decomposition        | Zhou 2022 (Least-to-most) |

Slot-impact ranking depends on the inferred `task_type`: code tasks
surface B10 first, essays surface B4 first, short one-offs skip the
reasoning layer entirely.

---

## Running it on other people's prompts

<!-- benchmark:begin -->

Live scores from CL4R1T4S as of 2026-04-17. Refresh with
`python3 skills/opus-mind/scripts/benchmark.py --update-readme`.

| Source | Score | Verdict | Chief gaps |
|---|---|---|---|
| [Claude Opus 4.7](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) | **11/11** | GOOD | — (canonical) |
| [Cursor Prompt](https://github.com/elder-plinius/CL4R1T4S/blob/main/CURSOR/Cursor_Prompt.md) | 6/11 | BORDERLINE | I1, I2, I8, I9, I10 |
| [ChatGPT-5 (Aug 2025)](https://github.com/elder-plinius/CL4R1T4S/blob/main/OPENAI/ChatGPT5-08-07-2025.mkd) | 4/11 | POOR | I1, I2, I3, I5, I6, I9, I11 |
| [Claude Code (Mar 2024)](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude_Code_03-04-24.md) | 7/11 | BORDERLINE | I2, I3, I8, I10 |

<!-- benchmark:end -->

A 6/11 doesn't mean the product is bad — it means the prompt isn't
written in the 12-primitive style. Shorter prompts naturally score
lower on I9 (self-check is for long prompts) and I10 (tier labels
for high-stakes rules) because those only trigger when the prompt is
long or stakes-heavy enough to need them.

---

## What it doesn't do

- **Can't tell you the rules are right.** It checks shape and
  discipline, not correctness. An 11/11 prompt can be semantically
  wrong — it just won't drift.
- **Doesn't do security review.** Not a jailbreak detector, not a
  red-team tool. Primitive 09 (reframe-as-signal) is defensive; the
  rest of the checks are structural.
- **Doesn't cover multi-turn conversations.** LINT audits a single
  system prompt. Context drift across turns isn't on its radar.
- **English-centric regex.** For Korean / Japanese / Spanish prompts,
  the Python layer will underreport hits. In Claude Code, the skill
  instructions tell Claude to override with its own language
  judgment. Outside Claude Code, scores for non-English prompts are
  a rough approximation.
- **`boost expand` doesn't return a rewritten prompt.** It emits a
  composition template for the surrounding LLM to apply. Inside
  Claude Code, Claude reads the template and writes the rewrite.
  Outside Claude Code, you paste it into your LLM of choice.

If your prompt is under 10 lines and under 3 directives, `audit.py`
returns verdict THIN and refuses to grade it — there's nothing
structurally to check. That's a deliberate floor, not a bug.

---

## Tests

156 passing tests, 4 skipped when offline.

```
python3 -m pytest tests/ skills/opus-mind/tests/ -q
```

One of them — `test_dogfood.py` — live-fetches the Opus 4.7 source on
every run and asserts it still scores 11/11 on our own auditor. If
the regexes ever drift away from the artefact they were extracted
from, that test breaks first.

`test_skill_orchestration.py` locks the JSON schema contracts the
skill depends on: shape of `audit --json`, TL;DR loadability for
every primitive doc, no-API-call grep across the tree.

---

## Architecture

Python scripts are deterministic — regex, counts, string templates.
They never call an LLM and never read `ANTHROPIC_API_KEY`. In a Claude
Code session, synthesis (composing the report, applying crosscheck
reviews, handling non-English prompts) is done by the surrounding
Claude in the same conversation. The CLI is the escape hatch for
environments without Claude Code — pre-commit hooks, CI jobs, Ruby
projects, whatever.

```
skills/opus-mind/
├── SKILL.md                  primary UX: phase-based flows + JSON schemas
├── hooks.json                Claude Code / Cursor / Codex lifecycle hooks
└── scripts/
    ├── audit.py              LINT — 11 invariants, --json primary
    ├── plan.py               LINT — domain inference + required primitives
    ├── fix.py                LINT — slop rewriter + skeleton injection
    ├── decode.py             LINT — primitive labeler
    ├── seed.py               LINT — 6 pre-wired skeletons by task type
    ├── boost.py              BOOST — check / ask / expand, 10 slots
    ├── symptom_search.py     DEBUG — symptom → primitive pointer
    ├── benchmark.py          CI — live leaderboard from CL4R1T4S
    ├── critic.sh             audit → plan → fix → re-audit loop
    ├── install-skill.sh      register at ~/.claude/skills/opus-mind/
    ├── install-hook.sh       git pre-commit installer
    └── opus-mind             bash wrapper / CLI entrypoint
```

---

## Attribution

The 1,408-line Opus 4.7 system prompt is not hosted here. It lives at
the [CL4R1T4S mirror](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt),
maintained by [@elder-plinius](https://github.com/elder-plinius).
Anthropic has not published the prompt. This repo is independent
third-party analysis — not endorsed, not reviewed, not partnered.

Quotations in the analysis files are under 15 words and anchored to
line numbers, so you can check the original context yourself.

If you represent a rights-holder and the fair-use reasoning is wrong
for a specific passage, open an issue. Same-day response. The analysis
framework (primitives, tools, tests) is independent work; only direct
quotations are in scope.

MIT license. Fork, extend, argue with any of it.

---

## Contributing

Useful things:

- **Corroboration from other leaked prompts.** Do the same primitives
  appear in GPT / Gemini / Grok? Where do they diverge?
- **BOOST slots I missed.** If you found a consistent prompting axis
  that's not in the 10, propose it with two fixtures (filled + empty)
  and a citation.
- **Failure-mode reports.** "I applied primitive X and it broke
  because Y" is the most useful thing you can send.

[CHANGELOG](./CHANGELOG.md) · [methodology](./methodology/README.md) ·
[primitives](./primitives/) · [techniques](./techniques/) ·
[evidence / line-refs](./evidence/line-refs.md)
