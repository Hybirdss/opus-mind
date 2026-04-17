# Primitive 06 — Example + Rationale

## TL;DR

Every non-trivial example in your prompt should carry a `{rationale}...{/rationale}` block explaining **why** the example is correct. You're not teaching a rule — you're teaching a function. Rules are brittle. Functions generalize.

## Definition

An example+rationale block is:

1. A **concrete case** (user input → desired output).
2. A **rationale** stating why this is correct — what principle is being exercised.
3. Ideally, a **contrast pair** — a positive example + a negative example + why each is classified that way.

## Evidence

Opus 4.7 uses this structure pervasively. Three clean cases:

**Copyright examples** (the source lines 710–750). Each example has the structure:

```
{example}
  {user}...{/user}
  {response}...{/response}
  {rationale}...{/rationale}
{/example}
```

Line 719: *"CORRECT: Claude correctly keeps quotes under 15 words (15+ is a SEVERE VIOLATION). Claude uses only ONE quote from this source (more than one is a SEVERE VIOLATION). The direct quote is necessary here because the CEO's exact wording under oath has legal significance. Paraphrasing 'has never and will never sell' as 'denied selling' would lose the specific commitment made."*

The rationale does three jobs: restates the rule, explains why it was applied, and explains the trade-off (what paraphrasing would have cost).

**Image search examples** (lines 882–902). Each example ends with a "Reason:" line:

> *"The person explicitly asked what something looks like. The image is the answer, so lead with it and follow with description."*

This teaches the principle "image-as-answer leads; image-as-support interleaves." Without the reason, the example is a single case. With the reason, it's a general move.

**Decision examples** (lines 486–498). Every routing decision gets a one-line rationale, mostly in the form "→ verdict because intent."

## Failure mode it prevents

**Memorizing the rule without generalizing.** A prompt that says "limit quotes to 15 words" and shows one example with a 14-word quote teaches one data point. The model will apply the rule to nearly-identical inputs.

A prompt with 3 examples plus rationales teaches the **principle behind the rule**. The model can extrapolate to inputs the author never anticipated. If the principle is "protect copyright by paraphrasing," the model correctly handles song lyrics, poems, code comments, and court transcripts — even though the examples covered only news articles.

The rationale is the bridge between specific cases and general behavior.

## How to apply

1. **Pair every substantive example with a rationale.** 1–3 sentences.
2. **State the rule that's being applied.** "This hits the quote-length limit."
3. **Explain the trade-off.** "A longer quote would violate X; a shorter quote would lose Y."
4. **When possible, pair correct and incorrect examples side by side.** The contrast is where learning happens.
5. **Avoid rationales that just restate the example.** "This is correct because Claude did the right thing" teaches nothing. The rationale must reference the **general principle**.

## Template

```
{example_<topic>}

{example}
User: <sample input>

Response: <desired behavior>

Rationale: This follows <principle>. Specifically, <rule X> applies because <condition>.
An alternative response would have violated <other rule / lost information>, so
this is the right trade-off.
{/example}

{anti_example}
User: <sample input>

Bad response: <what a naive model might do>

Why bad: This violates <principle> because <specific way>. The right move is to
<correct action>, following the pattern above.
{/anti_example}

{/example_<topic>}
```

## Before / after

**Before:** rule-only prompt.

> When explaining technical concepts, include a practical example whenever possible.

**After:** rule + example + rationale.

> When explaining technical concepts, include a practical example whenever possible.
>
> {example}
> User: How does a hash map work?
>
> Response: A hash map stores key-value pairs and looks up values by computing a hash of the key. Think of a coat check: you hand in your coat, they give you a number, and when you come back the number tells them exactly which hook to walk to — no searching.
>
> Rationale: The coat-check analogy is the example. It's concrete, physical, and familiar, which maps the abstract operation onto lived experience. A code snippet would teach the syntax but not the intuition — and the user asked "how does it work," which is an intuition question, not a syntax question.
> {/example}

The rationale teaches three generalizable moves: (a) match example to intent (intuition vs syntax), (b) prefer physical analogies for abstract operations, (c) choose concreteness over formalism for "how does X work."

## Misuse / anti-patterns

- **Rationale that restates the example.** "This is correct because the response addresses the question." Doesn't teach anything.
- **Too many examples, no rationales.** Showing 8 examples of correct behavior with no explanation of why they're correct is just volume. The model may pattern-match on surface features that are coincidental.
- **Rationale that's longer than the example.** You're writing documentation, not rationale. Keep it to 1–3 sentences that name the principle.
- **Positive-only examples.** Without a negative, the boundary is invisible. Always pair at least one positive with a representative negative when the topic has edge cases.

## Related primitives

- **[05 Cue-based matching](./05-cue-based-matching.md)** — positive and negative examples calibrate the cues.
- **[03 Hard numbers](./03-hard-numbers.md)** — examples show numbers in action.
- **[07 Self-check assertions](./07-self-check-assertions.md)** — examples can illustrate how the self-check rejects bad output.
