---
name: opus-mind
description: Use when the user edits CLAUDE.md / AGENTS.md / .cursorrules / GEMINI.md / **/SKILL.md or any chatbot system prompt (LINT), OR when the user wants to tighten a vague one-shot prompt before sending it to an LLM (BOOST). Fires on audit/score/review/fix requests, on symptoms like refuse-relent, narration leak, rule conflict, and on "help me improve this prompt" messages.
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion]
argument-hint: "[path to prompt file, inline prompt text, or '-' for stdin]"
---

# opus-mind

Two products, one skill. **LINT** audits production system prompts
against 11 structural invariants reverse-engineered from the leaked
Claude Opus 4.7 system prompt. **BOOST** coaches a user's single
request against 10 slots — 7 for specification quality and 3 for
reasoning quality (chain-of-thought, verification, decomposition).

Python helpers are deterministic (regex, counts, string templates).
Synthesis — composing rewrites, applying semantic review, judging
domain context — is done by you, the Claude running this session.
No API key, no extra cost, no shell-out.

## When to use

- User edits or audits: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`,
  `GEMINI.md`, `**/SKILL.md`, `system-prompt*.md`, or a chatbot
  system prompt → **LINT**.
- User pastes a vague one-shot request meant for Claude / ChatGPT /
  Cursor and wants it concrete → **BOOST**.
- User describes a symptom — refuse-relent, narration leak, rule
  conflict, adjective drift, jailbreak, injection, tool-call drift
  → **LINT Debug**.

## When NOT to use

- The target file has fewer than 3 directives or fewer than 10 lines.
  Run audit anyway and quote the `THIN` verdict back at the user
  verbatim; do not invent coverage.
- The user wants a generic "make this better" with no file, no
  pasted text, and no repo context. Ask for the concrete prompt
  first.
- The request is about Claude's own safety policy (e.g. "why did
  Claude refuse X?"). Point to Anthropic docs. This skill is about
  prompt structure, not safety interpretation.

## Routing — first-match-wins, stop at match

1. Input is a file path ending in `.md` / `.cursorrules`, or an
   inline system prompt (contains `{role}`, `Tier N`, `refuse`,
   `decline`, or directive-heavy content) → **Flow A: LINT**.
2. Input is a short natural-language request ("write me X", "help
   with Y", a one-liner the user plans to send to an assistant)
   → **Flow B: BOOST**.
3. Input is a symptom only — no file, no prompt to rewrite, just
   "my bot keeps doing X" → **Flow C: Debug**.

Do not mix flows in a single turn. Pick one, finish it, stop.

## Data contracts (JSON you will parse)

Every Python helper supports `--json`. The skill treats these
schemas as the source of truth — keys are stable, additions safe,
removals or renames require a schema version bump.

### `audit.py --json <path>`

```json
{
  "schema_version": "1.0",
  "path": "CLAUDE.md",
  "line_count": 220,
  "score": "8/11",
  "structural_health": "8/11",
  "verdict": "BORDERLINE",
  "thin_reason": null,
  "placeholder_count": 0,
  "pass": { "I1_reduce_interpretation": true, "I2_no_rule_conflicts": false, "..." : "..." },
  "metrics": { "hedges": 2, "directives": 26, "...": "..." },
  "findings": [
    { "invariant": "I2", "line": 0, "snippet": "", "issue": "26 directives, 0 ladders", "fix_pointer": "references/primitives/02-decision-ladders.md" }
  ]
}
```

Key fields to read: `verdict` (THIN / POOR / BORDERLINE / GOOD),
`pass` (per-invariant boolean map), `findings` (per-violation
details with line refs), `placeholder_count` (skeleton markers
left unfilled).

### `plan.py --json <path>`

```json
{
  "path": "CLAUDE.md",
  "score": "8/11",
  "domain": { "has_tools": true, "has_refusals": true, "is_long": true },
  "required_invariants": ["I1_...", "I2_...", "..."],
  "missing_required": ["I2_no_rule_conflicts", "I9_self_check"],
  "passing_required": ["I1_...", "..."],
  "primitive_detections": { "01": "high", "02": "absent", "..." : "..." }
}
```

`missing_required` is what you rank for improvement.

### `boost.py check --json <prompt>`

```json
{
  "source": "<inline>",
  "coverage": "1/10",
  "filled_count": 1,
  "slots": {
    "B1":  { "label": "task",          "filled": true,  "evidence": ["write a"] },
    "B2":  { "label": "format",        "filled": false, "evidence": [] },
    "B3":  { "label": "length",        "filled": false, "evidence": [] },
    "B4":  { "label": "context",       "filled": false, "evidence": [] },
    "B5":  { "label": "few_shot",      "filled": false, "evidence": [] },
    "B6":  { "label": "constraints",   "filled": false, "evidence": [] },
    "B7":  { "label": "clarify",       "filled": false, "evidence": [] },
    "B8":  { "label": "reasoning",     "filled": false, "evidence": [] },
    "B9":  { "label": "verification",  "filled": false, "evidence": [] },
    "B10": { "label": "decomposition", "filled": false, "evidence": [] }
  }
}
```

Slots split into two layers:
- **Specification** (B1-B7): what Claude should produce and for whom.
  Grounded in Anthropic public prompt-engineering docs.
- **Reasoning** (B8-B10): how Claude should think. Grounded in
  `evidence/smart-prompting-refs.md` (Wei 2022 CoT, Shinn 2023
  Reflexion, Zhou 2022 Least-to-most, Anthropic "Let Claude think").

### `decode.py --json <path>` and `symptom_search.py --json <query>`

Both emit detection lists you quote by line range and confidence.

## Flow A — LINT

### Phase 1: Gather

Run the deterministic pass:

```bash
python3 "$SKILL_DIR/scripts/audit.py" --json "<path>"
python3 "$SKILL_DIR/scripts/plan.py"  --json "<path>"
```

If the file lives inside a repo, use Read/Grep to skim sibling
context (`README.md`, `package.json`, `AGENTS.md`) — only enough
to infer the project's role (agent, chatbot, code assistant,
support bot). You are not auditing those files.

### Phase 2: Synthesize

1. Parse both JSON payloads.
2. If `verdict == "THIN"`, stop and tell the user the file is
   too thin to audit — quote the `thin_reason` field.
3. Rank the top findings by:
   - Required for this domain (present in `plan.missing_required`)
   - Severity (I1 `hedge_density > 0.25`, I4 narration > 0,
     I6 consequences < directives/10 are heavier than soft gaps)
   - Fixability via `fix --add` first, manual rewording second
4. Pick the **top 3** failing invariants. For each:
   - Read the primitive doc at `references/primitives/NN-*.md`
     or technique doc at `references/techniques/NN-*.md`
   - Extract the `## TL;DR` section (≤ 2 sentences)
5. Note any `placeholder_count > 0` — the author injected
   skeletons but did not fill them.

### Phase 3: Respond in prose

Lead with the verdict, then 3 findings with line refs, then one
concrete next action. Do not dump raw JSON. Example shape:

```
Your CLAUDE.md scores 6/11 (BORDERLINE). Three things move the verdict:

1. I2 decision-ladders — 26 directives, no "Step N → ..." ladder.
   Primitive 02: routing written as ordered steps with first-match-wins,
   not as an unordered list. Fix: `opus-mind lint fix CLAUDE.md --add ladder`.

2. I6 consequences at L42 — ...

3. I1 hedges at L88 — ...

Next: run the fix above, then `opus-mind lint report CLAUDE.md` to
re-verify. Expected lift: BORDERLINE → GOOD.
```

### Phase 4: Offer the fix, wait for consent

If the user agrees, run:

```bash
python3 "$SKILL_DIR/scripts/fix.py" "<path>" --add "<keys>" --apply
```

Then re-run Phase 1-3 so the user sees the score delta in the
same reply. Warn them: `fix --add` injects skeletons with
`<FIXME>` markers. They need to fill the markers with
domain-specific wording before commit, or the verdict stays
below GOOD (placeholder penalty).

### Phase 5 — Crosscheck (on request)

When the user asks for a semantic review beyond regex:

```bash
python3 "$SKILL_DIR/scripts/audit.py" --crosscheck "<path>"
```

The script prints a structured review prompt. Read it. Apply it
as a second reviewer in your next reply: list false positives
the regex caught wrongly, additional findings (rule conflicts,
consequence mismatches) regex missed, per-invariant severity
deltas. No API call. You are the second reviewer.

## Flow B — BOOST

### Phase 1: Check

```bash
python3 "$SKILL_DIR/scripts/boost.py" check --json "<prompt>"
```

Parse the coverage (`filled_count / 10`) and empty slots. The JSON
payload also carries:

- `task_type`: one of `code` / `analyze` / `research` / `write` /
  `short` / `unknown` — inferred from the prompt's verbs and nouns.
- `impact_order`: the 10 slots pre-ranked for this task type.
  Code tasks surface B10 first; analysis surfaces B8; creative
  writing surfaces B4; short one-offs surface B2 and skip the
  reasoning layer entirely.

### Phase 2: Ask — one question at a time, in `impact_order`

Do not dump all empty slots as a list. Walk `impact_order` from
the JSON, pick the FIRST empty slot, ask ONE question using
`AskUserQuestion` (Claude Code) / `request_user_input` (Codex)
/ `ask_user` (Gemini). Wait for the answer. Re-run `check` (or
merge the answer mentally), then walk `impact_order` again for
the next empty slot. Stop when coverage ≥ 7/10 or the user
signals done.

Task-type examples for reference (the JSON already hands you
the right order; this table is a sanity-check):

| task_type | top-3 slots to ask about first |
|---|---|
| code     | B10 decomposition → B8 reasoning → B9 verification |
| analyze  | B8 reasoning → B9 verification → B4 context |
| research | B9 verification → B8 reasoning → B4 context |
| write    | B4 context → B6 constraints → B3 length |
| short    | B2 format → B3 length → B6 constraints |
| unknown  | B3 length → B4 context → B2 format |

For B8-B10, suggest yes by default on **complex/multi-step/
reasoning-heavy** tasks (code, analysis, research). Skip them on
**short one-offs** (a tweet, a quick rename, a format conversion)
— reasoning overhead hurts there and the JSON ranking already
pushes them to the end for `task_type == "short"`.

### Phase 2b — Non-English prompt adaptation

The Python regex layer is English-centric. If the user's prompt
is in a non-English language (Korean, Japanese, Spanish, etc.),
the deterministic `filled` flags WILL underreport — a Korean
prompt that says "단계별로 생각해봐" is real chain-of-thought
framing but B8's English regex will not catch it.

In that case, YOU (the Claude driving this session) override
the regex with your own language judgment:

1. Read the user's prompt in their native language.
2. For each slot, ask yourself the slot's underlying question
   (see `QUESTION_TEMPLATES` in `boost.py`) in the user's language.
3. Mark `filled` yourself when the prompt genuinely answers that
   question, regardless of what the regex said.
4. In your reply, note which slots you judged filled beyond the
   regex — transparency matters.

Example — Korean prompt: "AI 안전에 대한 500단어 블로그 글 써줘.
ML 엔지니어 대상. 단계별로 생각하고 각 주장을 검증해줘."

Regex likely marks B1, B3 filled (English-friendly tokens leaked
through) but misses B4 ("ML 엔지니어 대상"), B8 ("단계별로 생각"),
B9 ("각 주장을 검증"). You mark all five filled and ask remaining
questions in Korean.

### Phase 3: Compose

```bash
python3 "$SKILL_DIR/scripts/boost.py" expand "<prompt>" \
  --length "<answer>" --format "<answer>" --context "<answer>" ...
```

The script prints a composition prompt (NOT an API response).
Read the template. Compose the rewritten user prompt as your
next reply, following the rules in the emitted template:
imperative verb + object, fold each answer in once, no
hedging, no preamble.

### Phase 4: Show the diff

After emitting the rewrite, summarize:

```
Original (9 words, 1/7): "write me a blog post"
Rewritten (67 words, 7/7): [your composition]
Added: length, audience, format, tone, constraints
```

Offer one more iteration if the user wants to tune a slot.

## Flow C — Debug by symptom

### Phase 1: Match

```bash
python3 "$SKILL_DIR/scripts/symptom_search.py" "<symptom>" --json
```

### Phase 2: Teach

Read the matched primitive or technique doc. Quote the
TL;DR. Explain in 2 sentences: what the failure mode is,
why it happens, which primitive prevents it.

### Phase 3: Bridge to LINT

If the user has a file where the symptom is firing, offer
to run Flow A against it.

## Platform adaptation

- Blocking question tool:
  `AskUserQuestion` (Claude Code) / `request_user_input` (Codex) / `ask_user` (Gemini)
- Content search:
  `Grep` + `Glob` (Claude Code) / `rg` (Codex) / `search_files` (Gemini)
- File read / edit: platform-native — never shell out for these
- LLM synthesis: **never** shell out. The surrounding platform
  already runs a model.

## Common mistakes

- **Dumping raw `audit --json` output.** The skill's value is
  prose synthesis with line refs. JSON is input, not output.
- **Asking all empty boost slots at once.** One question at a
  time, ranked by impact. Users abandon 6-question menus.
- **Requesting an `ANTHROPIC_API_KEY`.** You are the LLM. Compose
  in-chat. The architecture block forbids external calls.
- **Scoring `SKILL.md` with `audit.py --self`.** Wrong genre.
  `audit.py` targets system prompts; `SKILL.md` is instructions
  for Claude. Different ruleset, different evaluator.
- **Starting with `fix --add` before showing the report.** Users
  need to see why a change is recommended before approving it.

## How to invoke

Natural-language triggers that fire this skill:

- "audit my CLAUDE.md" → Flow A
- "score this SKILL.md" → Flow A
- "is this `.cursorrules` any good?" → Flow A
- "my bot refuses then gives in two turns later" → Flow C
- "help me turn 'write a blog post' into a real prompt" → Flow B
- "I want this better — here's my prompt: [...]" → Flow B
- "why does Claude keep narrating tool calls in my chatbot?" → Flow C → Flow A

## The 11 structural invariants (LINT)

Source refs are line numbers in the leaked Opus 4.7 system prompt
(CL4R1T4S mirror). Every check is regex + count with an explicit
threshold — no vibe grading.

| ID | Primitive | Signal | Source |
|---|---|---|---|
| I1  | 03 hard-numbers            | hedge_density ≤ 0.25, number_density ≥ 0.10 | L664, L620 |
| I2  | 02 decision-ladders        | Step N tokens + stop-at-first-match         | L515–L537 |
| I3  | 09 reframe-as-signal       | reframe clause when refusal content present | L33 |
| I4  | 08 anti-narration          | zero forbidden preambles                    | L536, L560 |
| I5  | 06 example + rationale     | every example carries a rationale           | L710–L750 |
| I6  | technique 04               | consequences ≥ directives / 10              | L753–L759 |
| I7  | 01 namespace-blocks        | every `{foo}` has `{/foo}`                  | structural |
| I8  | 04 default + exception     | default + (unless/except/only-when) cooccur | L25, L57–68 |
| I9  | 07 self-check              | self-check block when prompt is long        | L698–L707 |
| I10 | pattern: tier-labels       | ALLCAPS multi-word markers for high-stakes  | L640, L657 |
| I11 | 12 hierarchical-override   | Tier N / X > Y > Z / "takes precedence"     | L657 |

The `plan.py` domain inference (`has_tools`, `has_refusals`,
`is_long`, `has_examples`, `has_conflicts`) decides which
invariants are **required** for a given file. Always required:
I1, I2, I4, I6, I7, I8.

## The 10 BOOST slots

**Specification layer** — grounded in Anthropic public prompt-engineering docs:

| ID | Slot | Answers the question |
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
| B8  | reasoning     | ask for step-by-step / outline-first thinking | Wei 2022 (CoT) |
| B9  | verification  | ask for self-check / flag uncertain claims    | Shinn 2023 (Reflexion) |
| B10 | decomposition | ask for plan-before-execute / break into subtasks | Zhou 2022 (Least-to-most) |

None of these overlap with the system prompt. They are the
slots only the user can fill — specification shapes what Claude
produces, reasoning shapes how Claude thinks.

## Evidence and attribution

Every recommendation anchors to `source/opus-4.7.txt:L###` or
a primitive/technique file in `references/`. Source not hosted
here — see [`source/README.md`](../../source/README.md) for the
CL4R1T4S pointer. This skill is independent third-party analysis,
not endorsed by Anthropic.
