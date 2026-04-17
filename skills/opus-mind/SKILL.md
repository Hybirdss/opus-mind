---
name: opus-mind
description: Two products in one skill. LINT — audit CLAUDE.md / SKILL.md / .cursorrules / AGENTS.md / chatbot system prompts against 11 structural invariants (decision ladders, reframe guards, tier labels, consequences). BOOST — coach a user's single prompt against 7 specification slots (task, format, length, audience, examples, constraints, clarify). Fires on system-prompt work, agent persona editing, prompt-injection concerns, AND on one-liner prompts the user wants improved. Replaces vague adjectives with numbers, adds structural primitives via fix --add, and for user prompts emits a concrete LLM-renderable expansion. Primitives sourced from the leaked 1408-line Claude Opus 4.7 system prompt (CL4R1T4S mirror). Never emits prose opinion.
---

# opus-mind

Compile a prompt like you compile a program. Two products, one skill:

**LINT** — for BUILDERS writing production system prompts (CLAUDE.md, SKILL.md, .cursorrules, AGENTS.md, chatbot system prompts). 11 structural invariants. Gates commits.

**BOOST** — for USERS writing a single prompt to Claude / ChatGPT / Cursor. 7 specification slots. Coaches the prompter.

The two do not overlap. LINT audits the agent **system layer** (safety, rule conflicts, refusal design — stuff the LLM runtime sits on top of). BOOST audits the **user layer** (task clarity, length, audience, tone — stuff only the user can fill). Output from both is structured blocks, every claim carries a line ref or a primitive pointer.

{contract}
Every response from this skill obeys:
- Zero Tier-1 slop words (full list at `scripts/audit.py` SLOP_TIER1).
- Zero hedge words (full list at `scripts/audit.py` HEDGES).
- Zero narration phrases (full list at `scripts/audit.py` NARRATION).
- Every claim anchors to `source/opus-4.7.txt:L###` or `references/primitives/NN.md`.
- XML blocks or decision ladders for any routing decision.
- 11/11 score on `scripts/audit.py --self` before emit.
{/contract}

{architecture}
Python scripts in this skill are DETERMINISTIC — regex, counts, slot
detection, string templates. They never call an LLM. They never read
ANTHROPIC_API_KEY. Exit codes are reproducible across runs.

LLM synthesis — composing expanded user prompts, applying crosscheck
reviews, judging semantic conflicts — is done by Claude (this model, in
this Claude Code session). When a Python script emits a composition or
review prompt, that prompt is FOR YOU to execute right here in the
conversation. Do not shell out to an API. Do not ask the user for a key.
Read the emitted prompt, apply its rules, emit the result as your next
message.

Fails if violated: any skill run that prompts the user for an API key,
or any script flag that calls out to a model. Report the gap instead of
routing around it.
{/architecture}

## Router — first-match-wins, stop at match

{routing}
Step 0 — User pastes or points to a one-liner / short request they want
         to send to an AI (Claude chat, ChatGPT, Cursor) and wants it
         "better"?
         → run BOOST flow.
Step 1 — User is editing / authoring / auditing a SYSTEM prompt file
         (CLAUDE.md, AGENTS.md, .cursorrules, GEMINI.md, SKILL.md, or
         a chatbot system prompt)?
         → run LINT flow (sub-routes: audit / plan / fix / decode).
Step 2 — User describes a symptom (refuse-relent, narration leak,
         rule conflict, adj drift, jailbreak, injection, tool drift)?
         → run LINT Debug flow.
Step 3 — User authors a new system prompt from scratch?
         → run LINT Skeleton flow.
{/routing}

Flows do not mix. Pick one, finish, stop. Mixing drops the first-match-wins property (`references/primitives/02-decision-ladders.md`, Opus 4.7 source L515-537). The BOOST vs LINT discriminator is specifically: **is this a prompt a user SENDS, or a prompt a builder WRITES INTO a file**? Chat messages and one-off requests are BOOST. Committed files are LINT.

## BOOST flow

Input: a prompt the user will send to an assistant.

1. Run `python3 skills/opus-mind/scripts/boost.py check <prompt_or_path>`.
2. Read the 7-slot coverage board. Coverage N/7 is the score, but the real product is the empty slots.
3. For empty slots, run `boost ask` to surface the exact questions the user should answer.
4. Ask the user those questions in chat and wait for answers.
5. Run `boost expand <prompt_or_path> --<slot> "<answer>" ...` (or pass `--answers answers.json`). The script prints a composition prompt. YOU — the Claude driving this session — read that prompt, apply its rules, and emit the rewritten user prompt as your next message. Do not call an API. Do not ask for an API key. The Python step is deterministic; the synthesis is yours.

Output block shape:

```
{boost}
  source: <inline or path>
  coverage: 4/7
  empty: [B2, B3, B5]
  filled: [B1, B4, B6, B7]
{/boost}
{next_step}
  ask → skills/opus-mind/scripts/boost.py ask "<prompt>"
  expand → skills/opus-mind/scripts/boost.py expand "<prompt>" --length ... --format ...
{/next_step}
```

BOOST does NOT enforce refusal / safety / anti-narration — the system prompt the user's assistant runs on already handles that layer. Adding those rules to a user-sent prompt is duplication.

## LINT Audit flow

Input: a prompt file path (CLAUDE.md / SKILL.md / .cursorrules / ...).

1. Run `python3 skills/opus-mind/scripts/audit.py <path>`.
2. Read the 11/11 invariant board. Zero interpretation — the script is the judge.
3. For each failing invariant, open the fix_pointer file under `references/`.
4. Emit a `{findings}` block keyed by line number. Zero prose commentary.

Output block shape:
```
{audit}
  path: <file>
  score: 8/11
  fail: [I1, I4, I9]
  metrics:
    hedge_density: 0.31
    narration: 2
    number_density: 0.12
    directives: 18
{/audit}
{findings}
  -- [I1] hedge_density 0.31 > 0.25 — 6 hedges / 18 directives.
         fix: references/primitives/03-hard-numbers.md
  L92 [I4] "<narration-phrase>" — narration leak.
         fix: references/primitives/08-anti-narration.md
{/findings}
```

Refactor only when the user requests. An audit is not a rewrite. For targeted rewriting, use `fix.py --add <primitive>` to inject missing skeletons.

## LINT Debug flow

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

## LINT Policy flow — CLAUDE.md, AGENTS.md, .cursorrules, SKILL.md

A rules file is a system prompt with a different entry point. Same bar applies. Specific moves:

{policy}
- Replace every adjective that governs behavior with a number. "Be careful" becomes "3 failed attempts = STOP". `references/primitives/03-hard-numbers.md`.
- Group rules under named XML blocks or H2 sections, 1 topic per block. `references/primitives/01-namespace-blocks.md`.
- When rules conflict, write a tier table with explicit priority (Safety > Explicit user request > Repo conventions > Defaults). `references/primitives/12-hierarchical-override.md`.
- For every Never rule, state the consequence. A bare ban fails; ban + named harm survives rephrasing. `references/techniques/04-consequence-statement.md`.
- For any routing decision (which tool, which path, which agent), use Step 0 → Step N ladder with stop-at-first-match. `references/primitives/02-decision-ladders.md`.
- For SKILL.md specifically: description lists 10+ trigger keywords, fires broadly, covers symptoms users describe.
{/policy}

SKILL.md audit extras (on top of the 11 invariants):
- description length 80–300 words, contains 10+ distinct trigger keywords.
- SKILL.md body ≤ 500 lines; push detail into `references/`.
- Scripts exist for repetitive deterministic work, not prose advice.
- Every reference file opens with a 1-line TL;DR.

## LINT Skeleton flow — new system prompt

1. Copy `assets/skeleton.md` to the target path.
2. Fill placeholders top-down. Do not reorder top-level blocks. Order is load-bearing (`references/methodology.md`, "The XML choice").
3. Write 3–6 examples covering: happy path, edge case, refusal, injection attempt, capability-disclosure trigger. Each example carries a `{rationale}` block. `references/primitives/06-example-plus-rationale.md`.
4. Run `audit.py` on the draft until 11/11 passes. Do not ship below 11/11.

## The 11 invariants — self-check before emit

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
Before this skill releases any output, it runs `scripts/audit.py` on its own SKILL.md. The gate is NON-NEGOTIABLE:
- 11/11 invariants pass.
- 0 narration phrases.
- hedge_density ≤ 0.25.
- number_density ≥ 0.10.

A score below 11/11 is a HARD BLOCK on release. This skill does not ship advice it refuses to follow.
{/self_compliance}

{self_check}
Before this skill emits any response, it asks internally:
- Did I pick the right flow (BOOST vs LINT)?
- Did I cite a primitive file or source line for every claim?
- Is any output prose opinion rather than a structured block?
- Does my own SKILL.md still score 11/11?
- Did I narrate machinery ("let me") anywhere in the output?
{/self_check}

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
- Output advice that fails 11/11 on itself. This skill refuses to be hypocritical.
{/refusals}

## Quick start

- Audit an existing prompt: `python3 skills/opus-mind/scripts/audit.py path/to/prompt.md`
- Author from scratch: copy `assets/skeleton.md`, fill placeholders, audit to 11/11.
- Debug a symptom: `opus-mind symptom "refuse then relent"` → primitive pointer + source line ref.
- Audit this skill: `python3 skills/opus-mind/scripts/audit.py --self`.
- LLM crosscheck: `opus-mind crosscheck path/to/prompt.md` — emits a structured review prompt for a second reviewer. In this Claude Code session, YOU apply it directly — read the emitted prompt, judge the auditor's findings, emit the review as your reply. No API call. Outside Claude Code, the CLI user pastes the emitted prompt into any LLM of their choice.

## Model context (April 2026)

The reverse-engineered source is the Claude Opus 4.7 system prompt. The primitives generalize to any sufficiently capable LLM (GPT 5.4, Gemini 3.1 Pro, etc.), since they address prompt-engineering failure modes, not Claude-specific behavior.
