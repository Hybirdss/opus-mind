---
name: opus-mind
description: Author, debug, audit, or refactor LLM system prompts using 12 primitives reverse-engineered from the leaked Claude Opus 4.7 system prompt (1408 lines). Fires whenever the user writes, pastes, edits, or complains about a system prompt, persona, agent instruction, CLAUDE.md, AGENTS.md, .cursorrules, GEMINI.md, or SKILL.md. Also fires on symptoms — refuse-then-relent, narration leak, rule conflict, adj drift, prompt injection, tool-call drift. Replaces vague adjectives with numbers, prose with XML blocks, rules with first-match-wins ladders. Every recommendation cites source/opus-4.7.txt line numbers or a named primitive file. Never emits prose opinion.
---

# opus-mind

Compile a prompt like you compile a program. Six invariants, twelve primitives, seven techniques — all indexed to lines in the leaked Claude Opus 4.7 system prompt.

This skill treats a system prompt as a behavioral program for an LLM runtime. It does 4 jobs: author, debug, audit, refactor. Output is structured blocks. Every claim carries a line ref or a primitive pointer.

{contract}
Every response from this skill obeys:
- Zero Tier-1 slop words (full list at `scripts/audit.py` SLOP_TIER1).
- Zero hedge words (full list at `scripts/audit.py` HEDGES).
- Zero narration phrases (full list at `scripts/audit.py` NARRATION).
- Every claim anchors to `source/opus-4.7.txt:L###` or `references/primitives/NN.md`.
- XML blocks or decision ladders for any routing decision.
- 6/6 score on `scripts/audit.py --self` before emit.
{/contract}

## Router — first-match-wins, stop at match

{routing}
Step 0 — User pastes an existing prompt and asks for review, score, audit, or fix?
         → run Audit flow.
Step 1 — User describes a symptom (refuse-relent, narration leak, rule conflict, adj drift, jailbreak, injection, tool drift)?
         → run Debug flow.
Step 2 — User writes CLAUDE.md, AGENTS.md, .cursorrules, GEMINI.md, SKILL.md, or team rules file?
         → run Policy flow.
Step 3 — User authors a new system prompt from scratch?
         → run Skeleton flow.
{/routing}

Flows do not mix. Pick one, finish, stop. Mixing drops the first-match-wins property (`references/primitives/02-decision-ladders.md`, `source/opus-4.7.txt:L515-537`).

## Audit flow

Input: a prompt file path.

1. Run `python3 skills/opus-mind/scripts/audit.py <path>`.
2. Read the 6/6 invariant board. Zero interpretation — the script is the judge.
3. For each failing invariant, open the fix_pointer file under `references/`.
4. Emit a `{findings}` block keyed by line number. Zero prose commentary.

Output block shape:
```
{audit}
  path: <file>
  score: 4/6
  fail: [I1, I4]
  metrics:
    slop_tier1: 3
    narration: 2
    number_density: 0.28
{/audit}
{findings}
  L47 [I1] "<adjective>" — adj without number.
         fix: references/primitives/03-hard-numbers.md
  L92 [I4] "<narration-phrase>" — narration leak.
         fix: references/primitives/08-anti-narration.md
{/findings}
```

Refactor only when the user requests. An audit is not a rewrite.

## Debug flow

Input: a symptom sentence. Output: primitive pointer plus the 1–2 source lines that govern it.

{symptom_table}
Symptom                                   → Read these files
refuse-then-relent                         → primitives/09, techniques/03 (caution contagion)
rule conflict, model picks vibes           → primitives/02, methodology I2 (decision ladders)
adj drift under pressure                   → primitives/03, methodology I1 (hard numbers)
over-helpful machinery narration           → primitives/08, methodology I4
model rationalizes around rule             → primitives/07, techniques/07 (category match)
user turn impersonates system              → primitives/10, techniques/05 (injection defense)
model denies real capability               → primitives/11 (capability disclosure)
rule survives rephrase attack              → techniques/04 (consequence statement)
refusal reframed into compliance           → primitives/09 (reframe-as-signal, L33)
surprising behavior not forbidden          → techniques/06 (negative space)
safety loses to user request               → primitives/12 (hierarchical override)
rule set everywhere, unscoped              → primitives/01 (namespace blocks)
{/symptom_table}

This table lives in full form at `references/methodology.md` under "failure-mode taxonomy". It is the single diagnostic surface for opus-mind. Do not invent new symptom labels — map the user's complaint onto a row.

Output block shape:
```
{debug}
  symptom: refuse-then-relent
  primitive: 09-reframe-as-signal
  technique: 03-caution-contagion
  anchor: source/opus-4.7.txt:L33, L36
  read: references/primitives/09-reframe-as-signal.md
        references/techniques/03-caution-contagion.md
{/debug}
```

## Policy flow — CLAUDE.md, AGENTS.md, .cursorrules, SKILL.md

A rules file is a system prompt with a different entry point. Same bar applies. Specific moves:

{policy}
- Replace every adjective that governs behavior with a number. "Be careful" becomes "3 failed attempts = STOP". `references/primitives/03-hard-numbers.md`.
- Group rules under named XML blocks or H2 sections, 1 topic per block. `references/primitives/01-namespace-blocks.md`.
- When rules conflict, write a tier table with explicit priority (Safety > Explicit user request > Repo conventions > Defaults). `references/primitives/12-hierarchical-override.md`.
- For every Never rule, state the consequence. A bare ban fails; ban + named harm survives rephrasing. `references/techniques/04-consequence-statement.md`.
- For any routing decision (which tool, which path, which agent), use Step 0 → Step N ladder with stop-at-first-match. `references/primitives/02-decision-ladders.md`.
- For SKILL.md specifically: description lists 10+ trigger keywords, fires broadly, covers symptoms users describe.
{/policy}

SKILL.md audit extras (on top of the 6 invariants):
- description length 80–300 words, contains 10+ distinct trigger keywords.
- SKILL.md body ≤ 500 lines; push detail into `references/`.
- Scripts exist for repetitive deterministic work, not prose advice.
- Every reference file opens with a 1-line TL;DR.

## Skeleton flow — new system prompt

1. Copy `assets/skeleton.md` to the target path.
2. Fill placeholders top-down. Do not reorder top-level blocks. Order is load-bearing (`references/methodology.md`, "The XML choice").
3. Write 3–6 examples covering: happy path, edge case, refusal, injection attempt, capability-disclosure trigger. Each example carries a `{rationale}` block. `references/primitives/06-example-plus-rationale.md`.
4. Run `audit.py` on the draft until 6/6 passes. Do not ship below 6/6.

## The 6 invariants — self-check before emit

Every output from opus-mind must satisfy the same invariants it enforces on targets. Source: `references/methodology.md`.

{invariants}
I1 Reduce interpretation surface — every adj carries a number or gets cut.
   Anchor: source/opus-4.7.txt:L640 (15-word quote limit).
I2 Eliminate rule conflicts — routing decisions use first-match-wins ladders.
   Anchor: source/opus-4.7.txt:L515-537 (request_evaluation_checklist).
I3 Catch motivated reasoning — refusal content requires a reframe-as-signal clause.
   Anchor: source/opus-4.7.txt:L33.
I4 Keep internals private — zero machinery narration phrases.
   Anchor: source/opus-4.7.txt:L536, L560.
I5 Calibrate through examples — every example carries rationale.
   Anchor: source/opus-4.7.txt:L710-750 (copyright examples).
I6 Make failure modes explicit — every high-stakes rule names its harm.
   Anchor: source/opus-4.7.txt:L753-759 (copyright consequence statement).
{/invariants}

## The 12 primitives — index

Each lives at `references/primitives/NN-<name>.md` with definition, evidence, failure mode, apply, misuse. Do not paraphrase inline. Point and stop.

{primitives}
01 namespace-blocks       — XML tags as scoped modules
02 decision-ladders       — Step 0 → N, first-match-wins
03 hard-numbers           — 15 beats "short" every time
04 default-plus-exception — strong default, explicit opt-in list
05 cue-based-matching     — recognize signals, no flowchart memorization
06 example-plus-rationale — every example carries its why
07 self-check-assertions  — runtime checklist before output
08 anti-narration         — hide machinery from user
09 reframe-as-signal      — sanitization impulse is the refusal trigger
10 asymmetric-trust       — different claims, different bars
11 capability-disclosure  — tell the model what it does not know
12 hierarchical-override  — safety > user > helpfulness, explicit
{/primitives}

## The 7 techniques — composed moves

{techniques}
01 force-tool-call                — model answers from stale priors
02 paraphrase-with-numeric-limits — copyright creep
03 caution-contagion              — refuse once, relent on follow-up
04 consequence-statement          — rule survives rephrasing
05 injection-defense-in-band      — user content impersonates system
06 negative-space                 — surprising behavior not forbidden
07 category-match                 — model rationalizes out of routing
{/techniques}

Full index and primitive-to-technique map at `references/techniques/README.md`.

## Self-compliance gate

{self_compliance}
Before this skill releases any output, it runs `scripts/audit.py` on its own SKILL.md. The gate:
- 6/6 invariants pass.
- 0 Tier-1 slop words.
- 0 narration phrases.
- ≤ 2 hedges.

A score below 6/6 blocks release. This skill does not ship advice it refuses to follow.
{/self_compliance}

## Evidence and attribution

{evidence}
Source file: `source/opus-4.7.txt` — a 1408-line verbatim mirror from the CL4R1T4S archive. Every primitive and technique cites explicit line ranges in `references/line-refs.md`. No claim floats without a line number.

This skill was reverse-engineered from a leaked artifact. Anthropic has not published this prompt. All quotations stay under 15 words per the Opus 4.7 policy itself (`source/opus-4.7.txt:L640`).
{/evidence}

## What this skill refuses to do

{refusals}
- Write prose opinion about a prompt. Opinion is I1 drift.
- Rewrite a prompt without running audit first. Rewrites without a score are vibes.
- Invent primitives not in `references/primitives/`. New primitives require new evidence, new line refs, and a PR to the root repo.
- Paraphrase primitive or technique bodies inline. Point and stop — the progressive disclosure contract.
- Output advice that fails 6/6 on itself. This skill refuses to be hypocritical.
{/refusals}

## Quick start

- Audit an existing prompt: `python3 skills/opus-mind/scripts/audit.py path/to/prompt.md`
- Author from scratch: copy `assets/skeleton.md`, fill placeholders, audit to 6/6.
- Debug a symptom: match the symptom table, read the pointed-to primitive, apply the fix.
- Audit this skill: `python3 skills/opus-mind/scripts/audit.py --self`.

## Model context (April 2026)

The reverse-engineered source is the Claude Opus 4.7 system prompt. The primitives generalize to any sufficiently capable LLM (GPT 5.4, Gemini 3.1 Pro, etc.), since they address prompt-engineering failure modes, not Claude-specific behavior.
