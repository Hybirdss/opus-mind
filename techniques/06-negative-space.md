# Technique 06 — Negative Space

## Problem

Telling the model what to do leaves gaps. The model fills those gaps with defaults it learned in training — which are often wrong for your product.

## The move

Write explicit **"do NOT do this"** lists. Spell out the anti-patterns. The gap between "what you told it to do" and "what it actually does" is shaped by what you **forbid**, not by what you request.

## Evidence

The `{artifact_usage_criteria}` block in `source/opus-4.7.txt` (lines 395–477) is the textbook case. The author wrote two lists:

- *"Claude uses artifacts for"* (7 items).
- *"Claude does NOT use artifacts for"* (8 items).

The **do-not** list is where the behavior gets shaped. Without it, the model would over-create artifacts (its training bias). The items on the do-not list are the specific anti-behaviors the author needed to kill.

Another example — `{unnecessary_computer_use_avoidance}` (line 294):

> *"Claude should not use computer tools when:
> - Answering factual questions from Claude's training knowledge
> - Summarizing content already provided in the conversation
> - Explaining concepts or providing information
> - Writing short conversational content…"*

Four specific not-cases. Each one eliminates a default behavior the model would otherwise have.

A third — `{lists_and_bullets}` (lines 57–68): the do-not list is longer than the do list. Defaults are stated negatively.

Pattern: the *do-not* list is where the model's training-bias defaults get corrected.

## How to apply

For every capability or behavior you instruct:

1. **Write the positive case** — what the model should do.
2. **Write 3–6 negative cases** — what it should NOT do. Pick cases where you predict the model would otherwise default wrongly.
3. **Be specific.** "Don't over-format" is weak. "Don't use bullet points for < 3 items" is specific.
4. **Include the sneaky cases.** Common model biases: over-creating files, over-bulleting, over-searching, over-offering, over-apologizing. These need explicit "do not" items.

## Template

```
{<behavior>_negative_space}
Claude does X when <positive cases>.

Claude does NOT do X for:
- <Sneaky case 1: a place the model would default to X but shouldn't>.
- <Sneaky case 2: a case where X seems helpful but isn't>.
- <Sneaky case 3: a framing that might seem like X but isn't>.
- <Sneaky case 4: a user request that, if literal, would trigger X but shouldn't>.

If none of the positive cases apply, Claude does not do X, even if the request
"seems to call for it."
{/<behavior>_negative_space}
```

## Example — artifact creation

**Before:**

> Create an artifact for substantial pieces of content like code, essays, or interactive components.

The model creates artifacts for:
- 3-line regex snippets (trained bias: "regex is code").
- Grocery lists (trained bias: "list = artifact").
- Email drafts (trained bias: "long text = artifact").
- Responses to "can you write a short poem?" (trained bias: "creative writing = artifact").

**After** (with negative-space addition):

```
{artifact_creation}
Claude creates an artifact when the output is:
- Code over 20 lines.
- Standalone written content (essays, articles, posts) meant to be used outside the chat.
- Interactive components (React, HTML widgets).
- Long-form creative writing (> 20 lines) that the user will keep.

Claude does NOT create an artifact for:
- Code snippets of 20 lines or fewer (inline).
- Short creative writing (haikus, short poems, single-paragraph stories).
- Lists, tables, or enumerated content — even if long.
- Single-day schedules, simple workout routines, short itineraries.
- Quick summaries, outlines, brainstorms — conversational, even if many bullets.
- Single recipes (unless part of a larger collection).
- Brief emails, paragraph responses, explanations.

If the user explicitly asks for something short ("a short paragraph," "a quick
summary"), Claude does not upgrade to an artifact, regardless of content type.
{/artifact_creation}
```

Now the model holds the line. Most of the bias-driven artifact creation is explicitly forbidden.

## Composing with other primitives

- **Default + exception** (primitive 04): negative-space lists are the "exceptions to the negative default" made explicit.
- **Example+rationale** (primitive 06): each negative case can carry an example to calibrate.
- **Cue-based matching** (primitive 05): negative cases are often cued by specific surface features — include those cues.

## Misuse

- **Writing only negative cases, no positive.** The model doesn't know what you *want*. Always pair with the positive case.
- **Vague negatives.** "Don't be too formal" — what's too formal? "Don't use business-speak phrases like 'leverage' or 'circle back'" — concrete.
- **Over-long negative lists.** Past 8–10 items, the list stops registering. Group them into themes if you have more.
- **Forgetting the biases you don't see.** Your model has defaults you've never noticed because they're what you expect. Check actual output against the prompt; every unexpected behavior is a missing negative case.

## The "biases to check for" shortlist

Common model defaults that need explicit negative cases in most prompts:

| Bias | Likely negative case to add |
|---|---|
| Over-apologizing | "Don't apologize unless Claude actually erred." |
| Over-bulleting | "Don't use bullets for ≤ 2 items or conversational prose." |
| Over-offering | "Don't offer to do more ('Let me know if…') at the end of every response." |
| Over-restating | "Don't summarize the question before answering." |
| Over-hedging | "Don't use 'might', 'perhaps', 'it depends' where a definite answer is possible." |
| Over-searching | "Don't search for stable facts (math, well-known history, capital cities)." |
| Over-creating files | "Don't create files for content that belongs in the conversation." |
| Over-narrating | "Don't announce internal actions ('Let me search…')." |
| Over-formatting | "Don't use H2/H3 headers in responses under 500 words." |
