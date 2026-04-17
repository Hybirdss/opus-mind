# Primitive 07 — Self-Check Assertions

## TL;DR

Before high-stakes output, require the model to walk a **checklist of questions** about its own response. Each question is a runtime assertion. If any fails, the model revises before emitting.

## Definition

A self-check block is a list of **internal questions** the model asks about a candidate response before producing it. The questions are:

1. **Concrete.** Answerable with yes/no or a specific observation.
2. **Ordered from cheapest to most expensive.** Catch disqualifiers first.
3. **Tied to consequences.** Each failure triggers a specific revision.
4. **Positioned where the output is about to be generated**, not in a faraway policy section.

## Evidence

the source lines 699–707 — `{self_check_before_responding}`:

> Before including ANY text from search results, Claude asks internally:
> - Could I have paraphrased instead of quoted?
> - Is this quote 15+ words? (If yes → SEVERE VIOLATION, paraphrase or extract key phrase)
> - Is this a song lyric, poem, or haiku? (If yes → SEVERE VIOLATION, never reproduce)
> - Have I already quoted this source? (If yes → source is CLOSED, 2+ quotes is a SEVERE VIOLATION)
> - Am I closely mirroring the original phrasing? (If yes → rewrite entirely)
> - Am I following the article's structure? (If yes → reorganize completely)
> - Could this displace the need to read the original? (If yes → shorten significantly)

Seven questions, each paired with a consequence, positioned right before the behavior it governs.

A second example — the `{request_evaluation_checklist}` (lines 515–537) is a self-check at the routing layer, not the content layer. The model walks the checklist before producing any visual.

## Failure mode it prevents

**Policy known, policy not applied.** The model "knows" the copyright rule — it's 100 lines back in the prompt. But at the moment of producing an answer, the rule doesn't fire. Self-check assertions put the rule **in the critical path** of output generation.

Think of it as the difference between reading a coding-standards document once at hiring and running a pre-commit hook. The pre-commit hook catches violations the standards doc couldn't prevent because the standards doc isn't on the critical path.

## How to apply

1. **Pick a behavior where the cost of failure is high.** Copyright violation, hallucinated code, unsafe medical advice, data leak.
2. **Write 4–7 questions** that directly test for the failure modes.
3. **Order them cheapest-first.** Length check before semantic check. Rule lookup before nuance.
4. **Attach a consequence to each.** "If yes → paraphrase" / "If no → regenerate".
5. **Place the block directly before the relevant output.** Don't bury it 800 lines up in the prompt.

## Template

```
{self_check_<behavior>}
Before producing <output type>, ask internally and revise if any answer
indicates a violation:

- Is <observable feature 1> true? If so, <action>.
- Does the output <observable feature 2>? If so, <action>.
- Is there <risk 3>? If so, <action>.
- Could I have done <better alternative>? If so, revise toward it.
- Would a reasonable reviewer flag <standard failure mode>? If so, revise.
{/self_check_<behavior>}
```

## Before / after

**Before:**

> Make sure your code handles errors properly and doesn't have obvious bugs.

**After:**

```
{self_check_code_output}
Before returning code, ask:
- Does this function have a test or at minimum an example invocation? If not, add one.
- Are there uncaught failure modes — network, file not found, invalid input?
  If yes, either handle them or document them as out of scope at the top.
- Is any variable name unclear without context? If yes, rename.
- Did I use any imports not declared at the top of the file? If yes, add them.
- Is there a comment explaining what the code does? Prefer to delete it;
  well-named identifiers should carry the meaning.
{/self_check_code_output}
```

Five concrete questions, each with an action. The model does the check because the check is part of the behavior, not a separate aspiration.

## Misuse / anti-patterns

- **Vague questions.** "Is this response good quality?" is not an assertion. "Is any quote ≥ 15 words?" is an assertion.
- **Too many questions.** More than 7–8 items and the model starts treating the list as flavor text. Keep it tight. If you have many, group them into checklists with different triggers.
- **Placing the checklist nowhere near the behavior.** Self-check for image search placed 500 lines away in a general "quality" section won't fire. Put it adjacent to `{image_search}`.
- **No consequences attached.** "Check if the quote is too long." OK, and if it is? A question without a consequence is just a question.
- **Using self-check as a substitute for hard rules.** Self-check is a second line of defense. Hard numbers + decision ladders are the first. Don't replace, layer.

## Related primitives

- **[03 Hard numbers](./03-hard-numbers.md)** — self-check questions reference the hard numbers.
- **[06 Example+rationale](./06-example-plus-rationale.md)** — self-check questions are easier to internalize with one worked example.
- **[09 Reframe-as-signal](./09-reframe-as-signal.md)** — "Am I softening the request?" is a specific self-check.
