# Primitive 04 — Default + Exception

## TL;DR

Set the default aggressively. Then list exceptions explicitly. A strong default with a short exception list beats a weak default with long caveats every time.

## Definition

A default-plus-exception block has three parts:

1. **A default behavior** stated strongly, often using "always" / "never" / "only".
2. **An exception list**, explicit and bounded.
3. **No implicit third path** — if a situation doesn't match the exceptions, the default wins.

## Evidence

The formatting policy is the clearest example. Lines 57–68 in `source/opus-4.7.txt`:

> Default: **no bullets, no headers, no lists, no bold emphasis**, prose in paragraphs.
> Exceptions: (a) the person explicitly asks for a list, (b) the response is multifaceted enough that bullets are essential.
> No implicit third path: "relatively technical content" is not an exception — the default still applies.

Emoji policy (line 79): *"Claude does not use emojis unless the person in the conversation asks it to or if the person's message immediately prior contains an emoji."* Two exceptions, bounded.

Curse-word policy (line 83): *"Claude never curses unless the person asks Claude to curse or curses a lot themselves."* Same pattern.

Web search policy (lines 600–615) flips the polarity: the *default* is search-before-answer for any present-day factual question; the exceptions are listed (stable facts, well-known people, historical events).

Compare to the refusal policy (line 25): *"Claude defaults to helping. Claude only declines a request when helping would create a concrete, specific risk of serious harm."* Default-first, exceptions narrow.

## Failure mode it prevents

**Weak-default drift.** If you write "use bullets when appropriate," the model makes a lot of output "appropriate" for bullets. Pretty soon every response is bulletized.

If you write "prose by default, bullets only when the user asks or the content is genuinely multifaceted," the model has to cross a bar to use bullets. The default holds.

The deeper reason this works: **LLMs treat rules as biases, not gates.** A "use bullets when appropriate" rule biases toward bullets. A "no bullets except in these two cases" rule biases against bullets. Same information content, opposite effect on behavior.

## How to apply

1. **Choose the default you want 90%+ of the time.** If you want prose, default is prose.
2. **State the default strongly.** "Always", "by default", "the response is prose". No "generally" or "usually".
3. **List exceptions by concrete condition**, not by vibe. "The user asks for a list" is concrete. "The content benefits from structure" is vibe.
4. **Cap the exception list.** Three exceptions max. If you have five, your default isn't actually the default — redesign.
5. **Close the door on a third path.** Add a sentence that says: "If none of the exceptions apply, the default applies." This kills "well, I thought this was a fourth case" reasoning.

## Template

```
{formatting_default}
Claude writes in prose paragraphs by default — no bullets, no headers, no numbered lists.

Exceptions (only these):
1. The user explicitly asks for a list, a numbered format, or a checklist.
2. The content is a comparison of three or more distinct items where bullets materially aid scanning.

If neither exception applies, the default applies. "This would read cleaner as a list" is not an exception — the default is prose.
{/formatting_default}
```

## Before / after

**Before:**

> Use markdown formatting when it helps. Bullets are fine for lists and multiple items. Headers can be useful for structure. Keep it readable.

Problems:
- "When it helps" = always, for an over-helpful model.
- "Fine for lists" = treat almost anything as a list.
- "Keep it readable" = vibes.

Observed behavior: the model bulletizes everything, adds H2 headers to 200-word responses, bolds every other noun.

**After:**

```
{formatting}
Default: prose paragraphs. No bullet points, no headers, no bold emphasis.

Exceptions (use formatting only in these cases):
- User requests a list, table, or structured format explicitly.
- Content is a comparison of 3+ items that scan better as a table.
- Code blocks for code (this is formatting for code, not prose).

If none of these apply, write prose. "Multiple ideas" is not an exception. "Might be easier to read" is not an exception. The default applies.
{/formatting}
```

Observed behavior: the model writes prose. Bullets appear only when asked. The model may also lose the impulse to over-structure in ways you didn't anticipate.

## Misuse / anti-patterns

- **"Sometimes X, sometimes Y."** This is two defaults, which is no default. Pick one.
- **Default that disagrees with the product.** If your product is a code assistant and your default is "prose", you're fighting reality. Set the default that matches the 90% case.
- **Exceptions that cover 40% of cases.** If the exception fires a lot, it's not an exception, it's a co-default. Redesign: either split into two products (different defaults) or move the exception behavior into the default.
- **Implicit third paths.** "Do X, unless Y, unless Z." Now the model has three paths and has to disambiguate. Close the door explicitly on anything not listed.
- **Mixing with "please" or "try to".** "Please try to default to prose." No. "Default: prose." Imperative.

## Related primitives

- **[01 Namespace blocks](./01-namespace-blocks.md)** — put each default+exception pair in its own block so defaults don't bleed.
- **[03 Hard numbers](./03-hard-numbers.md)** — "3+ items" is a hard-numbered exception condition.
- **[12 Hierarchical override](./12-hierarchical-override.md)** — a safety default with exceptions carved out sits above a formatting default with exceptions carved out.
