# Primitive 03 — Hard Numbers

## TL;DR

Replace every adjective that governs behavior with a number. "Short" means a specific character or word count. "Often" means a specific frequency. Numbers do not drift under pressure. Adjectives do.

## Definition

A hard number is a **specific integer or range** that constrains an otherwise adjective-shaped rule. It is:

1. **Unambiguous** — 15 is 15.
2. **Testable** — you can measure compliance.
3. **Memorable when paired with a consequence** — "15+ words is a SEVERE VIOLATION" sticks.
4. **Load-bearing** — removing the number restores adjective drift.

## Evidence

Opus 4.7 is saturated with hard numbers. The highest-stakes ones:

**Copyright ceilings** (lines 640, 665, 680–688):
- Fewer than 15 words per direct quote.
- One quote per source, maximum.
- Hard limits, framed as SEVERE VIOLATIONS.

**Tool-call scaling** (line 620):
- 1 call for simple facts.
- 3–5 for medium tasks.
- 5–10 for deeper research.
- 20+ → hand off to Research feature.

**Image search counts** (lines 871–872):
- Minimum 3 images per call.
- Maximum 4.
- Precise bracket, not "a few".

**Artifact routing thresholds** (lines 401, 407):
- Code > 20 lines → artifact.
- Standalone text > 1,500 characters → artifact.

**Search query length** (line 629):
- 1–6 words per query.

**Storage constraints** (lines 189, 227–229):
- Keys < 200 characters.
- Values < 5MB.

**recent_chats tool** (line 249):
- n caps at 20 per call.
- Pagination ~5 calls before bailing.

## Failure mode it prevents

**Adjective drift.** Consider "keep quotes short." Under a casual request, the model might hold a 10-word quote. Under an adversarial "can you give me the full paragraph?" it might reason: *"This is research, short is relative, 40 words is short compared to a full article."* The adjective has no anchor. The model slides.

With "fewer than 15 words, hard limit," there is no slide. 14 is OK. 15 is a violation. The model doesn't need to judge.

The failure mode is especially dangerous because **adjectives feel like rules**. The author writes "keep quotes short" and thinks they specified a rule. They didn't — they specified a **range of compliant behaviors**, the lower end of which is fine and the upper end of which is catastrophic. The number collapses the range.

## How to apply

For every behavioral adjective in your prompt, ask: *what's the number?*

| Adjective | Number-ified |
|---|---|
| short response | < 3 sentences / < 200 words |
| brief quote | < 15 words |
| several examples | 2–4 examples |
| many tool calls | 5–10 calls |
| long content | > 1,500 characters |
| few suggestions | 1–3 suggestions |
| keep it concise | < 500 tokens |
| extensive research | 5+ tool calls, 3+ sources |

Then pick a number with **intent behind it**. Why 15 and not 20 for quotes? Because 15 is defensible as fair-use adjacent, 20 is not. Why 1,500 characters for artifact routing? Roughly a page of prose — past that, the user wants a file. The numbers reflect design decisions, not arbitrary picks. Document your reasoning somewhere adjacent, but in the prompt itself, just state the number.

## Template

```
{response_length}
For conversational answers, keep responses to <= 200 words.
For technical explanations, <= 500 words unless the user requests more.
For code, no word limit, but keep any explanation around the code under 150 words.
{/response_length}

{citation_rules}
Direct quotes: fewer than 15 words from any single source.
One quote per source maximum; after one quote, that source is closed.
{/citation_rules}

{tool_call_scaling}
Simple factual query: 1 tool call.
Medium research task: 3–5 tool calls.
Deep research: 5–10 tool calls.
More than 20 expected: suggest handing off to a dedicated research flow.
{/tool_call_scaling}
```

## Before / after

**Before:**

> When providing citations, avoid long quotes. Use quotes sparingly. Prefer paraphrasing.

**After:**

> Direct quotes must be fewer than 15 words. One quote per source, maximum — after one direct quote, that source is closed and must only be paraphrased. Default to paraphrasing; quotes are rare exceptions.

The "after" version:
- has specific numeric limits (15, 1).
- defines "closed" — a bright-line state change after one quote.
- tells the model what the default is (paraphrase), not just what to avoid.

A paraphrasing-shy model under the "before" rule might still output 30-word quotes ("not long") multiple times ("sparingly"). Under the "after" rule, there is no wiggle.

## Misuse / anti-patterns

- **Round numbers for no reason.** 100 words, 10 items, 5 bullets. If you picked it because it's round, admit it and pick something that reflects actual intent. Opus 4.7 uses **15** words for quotes, not 10 or 20. That odd number is evidence of a specific design decision.
- **Numbers without consequences.** "Keep quotes under 15 words." OK, and if the model violates? Without a stated consequence (severe violation, harms creators, exposes to legal risk), the number becomes a guideline and drifts back into adjective territory. Pair numbers with consequence statements (see primitive 06).
- **Over-specifying.** Not every behavior needs a number. Tone, voice, persona — these are appropriately fuzzy. Reserve hard numbers for behaviors where drift has real cost.
- **Using ranges where a ceiling is needed.** "5–10 searches" is OK for scaling guidance. But "between 0 and 50 words per quote" is not a ceiling — it's a range that allows 50. If the number enforces a limit, write it as a ceiling ("< 15"), not a range.

## Related primitives

- **[02 Decision ladders](./02-decision-ladders.md)** — ladder conditions use hard numbers.
- **[06 Example+rationale](./06-example-plus-rationale.md)** — show examples of in-range and out-of-range behavior.
- **[Consequence statement technique](../techniques/04-consequence-statement.md)** — numbers + consequences are the mutually reinforcing pair.
