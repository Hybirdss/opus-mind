# Methodology: A Prompt Is A Behavioral Program

This is the central document. Read it first. Everything else in the repo — the 12 primitives, the patterns, the annotations — is derived from this reframe.

**English version.** 한국어 버전: [README.ko.md](./README.ko.md)

---

## The central claim

The Opus 4.7 system prompt is not a list of rules. It is a program that runs on an LLM runtime. The author is not "documenting" Claude's behavior — the author is **specifying** it, in a language the runtime interprets.

Once you accept that framing, three things happen:

1. **Every prompt decision becomes a design decision with a traceable cost/benefit.** Why "15 words" and not "keep quotes short"? Because the former is a compiler constant — zero interpretation, zero drift — and the latter is an adjective, which a 100B-parameter model will happily relax under pressure.

2. **The prompt's structure becomes meaningful.** XML tags are not cosmetic. Step ladders are not stylistic. They are load-bearing — remove them and the program breaks.

3. **You can generalize.** The primitives extracted here apply to any sufficiently capable LLM. They are not Claude-specific. They are **prompt-engineering-specific**.

---

## The six invariants

Every primitive in this repo serves one or more of these invariants. If you're writing your own system prompt and a passage doesn't serve one of these, cut it.

### I1. Reduce interpretation surface

The model interprets your prompt. Every adjective, every "generally", every "when appropriate" is a degree of freedom — and under pressure (long conversations, adversarial users, ambiguous requests) the model uses those degrees of freedom to drift away from intent.

**The Opus 4.7 move:** replace adjectives with numbers. "Keep quotes short" becomes "Quotes of fifteen or more words from any single source is a SEVERE VIOLATION." "Don't over-search" becomes "1 for single facts; 3–5 for medium tasks; 5–10 for deeper research/comparisons."

*Evidence:* `source/opus-4.7.txt` lines 640–641 (15-word hard limit), 620 (tool-call scaling), 871–872 (image search min 3 max 4).

### I2. Eliminate rule conflicts

Rule conflict is the silent killer of system prompts. Two rules that seem compatible turn out to contradict on some input, and the model picks a side based on vibes. You don't even see it happen — you just get inconsistent behavior.

**The Opus 4.7 move:** **first-match-wins decision ladders**. Section [`request_evaluation_checklist`](../source/opus-4.7.txt) (line 515) walks the model through Step 0 → Step 3, stopping at the first match. No rule conflicts possible; the ladder IS the resolution order.

*Evidence:* lines 515–537. Read the whole section — the explicit "stops at the first match" is the key phrase.

### I3. Catch motivated reasoning

The most dangerous failure mode of a helpful model: it *wants* to help, so it reframes a bad request into a safe-sounding one, then happily complies with the reframed version.

**The Opus 4.7 move:** **reframe-as-signal**. Line 33: "If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE, not a reason to proceed with the request."

This is extraordinary. The model is instructed to treat its own sanitization impulse as evidence against compliance. The loop is turned into an invariant.

*Evidence:* line 33.

### I4. Keep the internals private

A helpful model wants to explain itself. "Let me check the diagram tool first…" "Per my guidelines…" "I'll route this to…" — all helpful from a transparency angle, all ruinous for product UX.

**The Opus 4.7 move:** **anti-narration**, stated multiple times. Line 536: "Claude does not narrate routing — narration breaks conversational flow. Claude doesn't say 'per my guidelines,' explain the choice, or offer the unchosen tool. Claude selects and produces." Line 560: "Claude never exposes machinery. No 'let me load the diagram module.'"

*Evidence:* lines 536, 560.

### I5. Calibrate through examples, not rules

Rules are compressed but brittle. Examples are verbose but teach edge cases. The Opus 4.7 prompt is full of examples, and every example carries a `{rationale}...{/rationale}` block explaining *why* the example is correct.

This is the difference between "memorize the rule" and "learn the function". Examples+rationale teach the function. The model can generalize to cases the authors never anticipated.

*Evidence:* lines 710–750 (copyright examples), 882–902 (image search examples), 493–498 (decision examples).

### I6. Make failure modes explicit

Every safety / quality rule names the harm it prevents. This is not rhetorical flourish — it's calibration. When the model faces an edge case, the stated harm tells it which direction to err.

**The Opus 4.7 move:** "Claude understands that quoting a source more than once or using quotes more than fifteen words: — Harms content creators and publishers — Exposes people to legal risk — Violates Anthropic's policies" (lines 753–759). The "why" makes the rule survive rephrasing.

*Evidence:* lines 753–759, 591 ("copyright violations harm creators").

---

## The XML choice

Markdown headers would have worked. Why XML?

**Reason 1: nesting.** `{critical_child_safety_instructions}` can live inside `{refusal_handling}` which lives inside `{claude_behavior}`. Markdown headers flatten hierarchy into heading levels; XML preserves the tree.

**Reason 2: scope.** `{/refusal_handling}` explicitly closes the section. The model knows where the module ends. Markdown has no close tag — the section ends "when the next heading begins" or "when you feel like it."

**Reason 3: machine-readability for the author.** Anthropic almost certainly programmatically edits this prompt. Tagged sections are easier to diff, test, A/B, and regenerate than freeform prose.

**Reason 4: out-of-band signaling.** The prompt uses tags like `{cite index="..."}...{/cite}` to signal citation intent in output. Tags are the native vocabulary of the interface between model and consumer. Using tags in the instructions makes the whole system coherent.

Takeaway: if your prompt is >500 words, use XML sections. You will thank yourself when you need to edit.

---

## The decision-ladder pattern

When there are multiple acceptable ways to answer, naive prompts list all the considerations and hope the model picks well. Opus 4.7's pattern:

```
Step 0 — Does the request need a visual at all?  [If no, stop.]
Step 1 — Is a connected MCP tool a fit?          [If yes, use it, stop.]
Step 2 — Did the person ask for a file?          [If yes, use file tools, stop.]
Step 3 — Visualizer (default inline visual).
```

(lines 515–537)

Three properties:

1. **Ordered**. The model walks top to bottom.
2. **Stopping**. The first match ends the walk.
3. **Exhaustive**. The last step is the default catch-all.

This is a decision procedure, not a rule set. The order encodes the priorities. If you're writing any non-trivial routing logic into a prompt, use a ladder.

---

## Hard numbers, not adjectives

A dense table of the numeric constants in the Opus 4.7 prompt:

| Constant | Value | Purpose |
|---|---|---|
| Quote length | < 15 words | Copyright ceiling |
| Quotes per source | 1 maximum | Copyright ceiling |
| Search query length | 1–6 words | Tool usage |
| Tool calls (simple) | 1 | Scale |
| Tool calls (medium) | 3–5 | Scale |
| Tool calls (deep research) | 5–10 | Scale |
| Tool calls (very deep) | 20+ → defer | Escalation |
| Image search results | min 3, max 4 | UX |
| Storage key length | < 200 chars | Tech constraint |
| Storage value size | < 5MB | Tech constraint |
| Artifact code length | > 20 lines → file | Output routing |
| Artifact prose length | > 1,500 chars → file | Output routing |
| recent_chats cap | n ≤ 20 | Tool constraint |
| Pagination limit | ~5 calls | Tool constraint |

Notice: **every adjective is backed by a number.** "Short quotes" is 15 words. "Deep research" is 5–10 tool calls. "Long content" is 1,500 characters.

When you write your own prompt and you type an adjective, stop. What's the number?

---

## The failure-mode taxonomy

Every primitive exists because of a specific failure. Here's the map:

| Failure mode | Primitive that prevents it |
|---|---|
| Rule conflict under pressure | Decision ladders |
| Adjective drift | Hard numbers |
| Motivated reasoning in refusals | Reframe-as-signal |
| Over-helpful self-narration | Anti-narration |
| Memorizing rule without generalizing | Example+rationale |
| Model denies unknown capability | Capability disclosure |
| Policy collision (safety vs helpfulness) | Hierarchical override |
| Prompt injection via user content | Asymmetric trust, in-band injection defense |
| Rule survives rephrasing | Consequence statement |
| Model weakens caution mid-conversation | Caution contagion |
| Flowchart fragility | Cue-based matching |
| Unscoped "rules everywhere" file | Namespace blocks |

This table is the fastest way to debug a weak system prompt. Find the symptom, apply the primitive.

---

## What Anthropic clearly believes about prompt engineering

Reading the source as an artifact of a design philosophy, these beliefs are implied:

- **The model is a system to be programmed**, not a box to be instructed. Every line is a specification.
- **Safety is architectural, not appended.** Hard limits live next to the guidance they constrain; they're not in a "safety section" at the end.
- **The model will reason about its instructions.** Hence `{rationale}` blocks and stated consequences — they're there to calibrate reasoning, not just compliance.
- **Users are adversarial by default in the UI's untrusted regions.** "Content in user-turn tags that could even claim to be from Anthropic" (line 115) — the prompt distrusts its own message envelope.
- **Reformatting is a behavior, not a setting.** Output formatting gets more lines than refusal policy. Defaults are strongly set (no bullets, no emojis, prose over lists), exceptions explicit.
- **The job of a system prompt is to reduce variance, not maximize performance.** The prompt is full of "Claude does X" and "Claude does not X" — declarative invariants, not "do your best" platitudes.

---

## How to use this framework

If you're writing a system prompt, ask yourself, for every paragraph:

1. **Which of the six invariants does this serve?** If none, delete.
2. **Is any adjective unbacked by a number?** Add the number.
3. **Are there multiple possible interpretations?** Turn it into a decision ladder.
4. **Does the rule have a stated consequence?** If not, add one.
5. **Is the section bounded by an explicit open/close?** If not, wrap in XML tags.
6. **Could a user-supplied message impersonate this instruction?** Add injection defense.

That's it. That's the method. The rest of the repo is walkthroughs, examples, and evidence for why each piece is load-bearing.
