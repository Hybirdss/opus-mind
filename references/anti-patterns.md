# Anti-Patterns — 10 Ways Prompts Drift

Every invariant `audit.py` flags started as a specific drift pattern we
saw in real prompts. This file collects ten of them with concrete
before/after rewrites. Use it two ways:

1. **As a reader** — skim before writing a new system prompt so you
   know the shapes to avoid.
2. **As a reviewer** — when `audit.py` flags a line, the fix pointer
   points here; you see what the good shape looks like.

Each pattern shows:
- **Symptom** — what the auditor catches
- **Before** — the drifted version
- **After** — the repaired version
- **Invariant** — which `audit.py` rule fires
- **Opus 4.7 line** — the source evidence

---

## 1. Hedge drift — "generally" / "typically" / "probably"

**Symptom:** Rule softens from absolute to probabilistic. Three PRs
later, the rule is a suggestion.

**Before:**
> Claude should typically cite sources. Generally avoid speculation.
> In most cases, keep answers under 200 words.

**After:**
> Cite every factual claim with a URL or line reference.
> Never speculate beyond what the source says — if the source is
> silent, answer "not in the source".
> Keep answers under 200 words. Responses over 200 words fail
> this instruction.

**Invariant:** I1 (hedge_density ≤ 0.25).
**Source:** Opus 4.7 L664 — the "15 words" limit for quotes uses
a specific integer, not "short". Hard numbers do not drift under
pressure; adjectives do.

---

## 2. Adjective without number — "robust" / "comprehensive"

**Symptom:** Adjective is load-bearing but impossible to verify.

**Before:**
> The bot provides comprehensive error handling and a robust
> refusal policy for appropriate queries.

**After:**
> The bot catches all 5 exception classes listed in ERRORS.md and
> returns a structured `{error, hint}` JSON body.
> The bot refuses requests matching any entry in tier1-forbidden.txt;
> everything else is served.

**Invariant:** I1 (adj_without_number_count == 0).
**Source:** Opus 4.7 L620 "tool-call scaling" — 1 / 3-5 / 5-10 / 20.
Counted buckets, not "light" / "medium" / "heavy".

---

## 3. Narration leak — "Let me check" / "I'll analyze"

**Symptom:** The model announces its machinery before acting. Makes
the product feel like an assistant reading a script.

**Before:**
> When a user asks a question, let me check the documentation,
> then I'll analyze the situation and formulate a response.

**After:**
> Answer questions from the documentation. If the answer is not in
> the documentation, respond "I don't know based on the available
> sources" and offer to file a question.

**Invariant:** I4 (narration_count == 0).
**Source:** Opus 4.7 L536, L560 — forbidden preambles include
"per my guidelines" and "let me load the diagram module". Anthropic
treats these as product damage, not transparency.

---

## 4. No decision ladder for multi-option routing

**Symptom:** Four reasonable responses to the same trigger, no
documented order. Picks vary turn to turn.

**Before:**
> When the user asks about a file, you can search the file, read it
> inline, or cite it. Use the approach that makes sense.

**After:**
> When the user asks about a file, walk these in order and stop at
> the first match:
>
> Step 0 — Is the path outside the project root? → Refuse. Stop.
> Step 1 — Is the file over 50 KB? → Summarise by grep. Stop.
> Step 2 — Is the file code? → Read it, cite line ranges.
> Step 3 — Default — read it, quote the relevant snippet.

**Invariant:** I2 (ladder signals present when directives ≥ 6).
**Source:** Opus 4.7 L515-L537 — the `request_evaluation_checklist`
is an ordered ladder with stop-at-first-match semantics.

---

## 5. Refusal without reframe guard

**Symptom:** Model refuses the first request, then "helps creatively"
with a softened follow-up. Split-turn jailbreak.

**Before:**
> The bot refuses requests to generate malicious code. The bot is
> friendly and wants to help users succeed.

**After:**
> The bot refuses requests to generate malicious code.
>
> If the bot finds itself mentally rephrasing a refused request to
> make it look compliant, the rephrasing IS the refusal trigger —
> not a path to proceed. The charitable interpretation is evidence
> charity is unwarranted here. Proceed only if the original phrasing
> passes without adjustment.

**Invariant:** I3 (reframe_signals ≥ 1 when refusal content present).
**Source:** Opus 4.7 L33 — `critical_child_safety_instructions`
canonises reframing-as-signal as the detector.

---

## 6. Example without rationale

**Symptom:** Few-shot examples teach the output shape but not the
function. Model generalises wrongly on the next input.

**Before:**
> Example:
> User: "How do I reset the DB?"
> Response: "Run `bin/rake db:reset` from the project root."

**After:**
> Example:
> User: "How do I reset the DB?"
> Response: "Run `bin/rake db:reset` from the project root."
> Rationale: one concrete command, prefixed with the directory,
> no disclaimers. The model's job is the shortest path to a
> runnable answer. Fails if the response adds "this will destroy
> your data" warnings — users know.

**Invariant:** I5 (rationales ≥ 1 when examples ≥ 1).
**Source:** Opus 4.7 L710-L750 — copyright examples each carry a
rationale that names the law, not just the format.

---

## 7. Directive without consequence

**Symptom:** Rules stated flatly. Attackers rephrase them until they
break, because no consequence is attached to identify the rule.

**Before:**
> Never share other users' private data.

**After:**
> Never share other users' private data. Sharing private data:
> - Harms the user whose data was leaked
> - Exposes the operator to GDPR and CCPA liability
> - Violates the product's terms of service

**Invariant:** I6 (consequences ≥ directives / 10).
**Source:** Opus 4.7 L753-L759 — the
`copyright_violation_consequences_reminder` attaches three concrete
harms to a single rule, making the rule survive rephrased attacks.

---

## 8. Unbalanced namespace block

**Symptom:** `{refusal_handling}` opens but never closes, so all
downstream content is semantically inside the refusal block.

**Before:**
```
{refusal_handling}
Refuse when the user asks for X.

{tone_and_formatting}
Respond in 100 words.
```

**After:**
```
{refusal_handling}
Refuse when the user asks for X.
{/refusal_handling}

{tone_and_formatting}
Respond in 100 words.
{/tone_and_formatting}
```

**Invariant:** I7 (every `{foo}` has `{/foo}`).
**Source:** Opus 4.7 — every namespace block in the source is
explicitly closed. The close tag is part of the programming model,
not decoration.

---

## 9. Default without explicit exception

**Symptom:** The rule states a default but leaves the exception
implicit. Model invents its own exception criteria.

**Before:**
> Respond in prose. Bullets are acceptable when helpful.

**After:**
> Default response format: prose paragraphs.
>
> Exceptions (only these):
> - User explicitly requests a list or table.
> - Content is a comparison of 3 or more items.
> - Code goes in code blocks.

**Invariant:** I8 (default + exception co-occur).
**Source:** Opus 4.7 L57-L68 — formatting defaults are stated with
explicit, finite exception lists.

---

## 10. No self-check on a long prompt

**Symptom:** Prompt is 200+ lines with 30+ directives. No pre-emit
verification step. Model forgets half of them under load.

**Before:**
> (Long prompt with many directives and no checklist at the end.)

**After:**
> Before emitting any substantive response, ask internally:
> - Did I answer the user's actual question?
> - Am I starting with machinery narration? If yes, cut.
> - Did I hit any Tier 1 rule? If yes, revise to refuse.
> - Is any claim present-day that I did not verify? If yes,
>   call the tool.

**Invariant:** I9 (self-check block when prompt is long).
**Source:** Opus 4.7 L698-L707 — Claude's own self-check block sits
near the end of its system prompt, enumerating runtime assertions.

---

## Rule of thumb

If the drift pattern feels plausible when you read it cold, it will
happen in production. The deterministic auditor's job is to make the
drift visible *at commit time* so it stops before a PR lands — not
after the bot misbehaves in front of a user.

Run the auditor; let the invariants pull your prompt back into shape.

```bash
opus-mind lint audit path/to/your/CLAUDE.md
```
