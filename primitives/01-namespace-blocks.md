# Primitive 01 — Namespace Blocks

## TL;DR

Wrap every coherent block of policy in named XML tags like `{refusal_handling}…{/refusal_handling}`. Use the same tag to scope, to diff, and to close. Markdown headers are not enough.

## Definition

A namespace block is an XML-tagged region of the prompt that:

1. Has a **meaningful name** (what the section governs).
2. Has an **explicit close tag** (where it ends).
3. Can **contain nested blocks** (hierarchy preserved).
4. Is **referenced by name** from other sections when needed.

## Evidence

`source/opus-4.7.txt` uses this pattern pervasively. A partial map:

```
{claude_behavior}
  {search_first} ... {/search_first}
  {product_information} ... {/product_information}
  {default_stance} ... {/default_stance}
  {refusal_handling}
    {critical_child_safety_instructions} ... {/critical_child_safety_instructions}
  {/refusal_handling}
  {legal_and_financial_advice} ... {/legal_and_financial_advice}
  {tone_and_formatting}
    {lists_and_bullets} ... {/lists_and_bullets}
  {/tone_and_formatting}
  {user_wellbeing} ... {/user_wellbeing}
  {anthropic_reminders} ... {/anthropic_reminders}
  {evenhandedness} ... {/evenhandedness}
  {responding_to_mistakes_and_criticism} ... {/responding_to_mistakes_and_criticism}
  {tool_discovery} ... {/tool_discovery}
  {knowledge_cutoff} ... {/knowledge_cutoff}
{/claude_behavior}
```

(Derived from lines 3–154.)

Lines to spot-check:
- line 30 / line 39 — `{critical_child_safety_instructions}` opens and closes a five-rule block cleanly.
- line 117 / line 131 — `{evenhandedness}` scopes political-neutrality rules.
- line 587 / line 835 — `{search_instructions}` wraps **250 lines** of search policy with close at 835.

## Failure mode it prevents

**The "unscoped rules everywhere" file.** Without namespaces, a long prompt becomes a soup of sentences. Under long-conversation pressure or adversarial framing, the model can't tell which rule governs which region of behavior. Rules cross-contaminate. A search-time copyright rule leaks into creative writing. A minor-safety instruction gets ignored during research because it looked like a general guideline.

Namespace blocks tell the model: **these rules apply here, within this scope, and end when the close tag fires**.

## How to apply

1. **Section your prompt before writing content.** Lay out the tags first, content second.
2. **Name by governance, not topic.** `{refusal_handling}` is good — it says what the block *does*. `{dangerous_stuff}` is bad — it just labels a topic.
3. **Nest when there's genuine hierarchy.** A child-safety block inside refusal handling is legitimate nesting. Don't nest for decoration.
4. **Reference by name from other sections.** Opus 4.7 does this: line 111 refers back to `{harmful_content_safety}` by name. This creates cross-section coherence without duplicating content.
5. **Always close.** Every open tag ends.

## Template

```
{role}
Claude is an <agent description>. Claude's primary job is <mission>.
{/role}

{default_stance}
Claude defaults to <positive action>. Claude only <negative action> when <specific trigger>.
{/default_stance}

{refusal_handling}
Claude refuses when <concrete harm X>. Claude does not refuse for <merely uncomfortable Y>.

{high_severity_cases}
... specific cases ...
{/high_severity_cases}
{/refusal_handling}

{tone_and_formatting}
{length} ... {/length}
{structure} ... {/structure}
{/tone_and_formatting}

{tool_usage}
{search_rules} ... {/search_rules}
{file_creation} ... {/file_creation}
{/tool_usage}
```

## Before / after

**Before:** a 4,000-token system prompt written as one wall of markdown with `##` headers.

> ```
> ## Safety
> You should refuse harmful requests. Be helpful otherwise.
> ## Formatting
> Use short paragraphs. Avoid excessive markdown.
> ## Tools
> Search before answering factual questions.
> ```

Problems:
- No explicit scope close — where does "Safety" end?
- Headers lost in rendering for the model (many tokenizers flatten `##`).
- Can't cross-reference sections by name.

**After:**

```
{safety}
Claude refuses requests that create concrete risk of serious harm.
Claude defaults to helping for uncomfortable, edgy, or hypothetical requests.
{/safety}

{formatting}
Claude writes prose in paragraphs, not bullet points, unless the user requests lists.
Claude uses markdown emphasis sparingly.
{/formatting}

{tools}
{search_policy}
Claude searches the web before answering any question about present-day facts
(prices, role-holders, laws). Claude does not search for stable historical facts.
{/search_policy}
{/tools}
```

The close tag forces scope. You can diff. You can A/B test one section at a time. You can reference `{safety}` from `{tools}` if needed. The model sees clean boundaries.

## Misuse / anti-patterns

- **Using tags cosmetically.** `{tip_1}Always check your work{/tip_1}{tip_2}Be polite{/tip_2}`. There's no scoping value; the tags are decoration. Use tags for **bounded policy regions**, not for labeling tips.
- **Opening without closing.** A dangling open tag pollutes the rest of the prompt with ambiguous scope. Always close.
- **Over-nesting.** Four levels deep and the model starts to treat nesting as noise. Two or three levels is the practical ceiling.
- **Using tag names that collide with output syntax.** `{quote}` is bad if the model is supposed to emit `{quote}` in output. Opus 4.7 uses `{cite}` in output and **different tags** (`{mandatory_copyright_requirements}`) in policy. Separate the namespaces.

## Related primitives

- **[02 Decision ladders](./02-decision-ladders.md)** — ladders often live inside a namespace block.
- **[12 Hierarchical override](./12-hierarchical-override.md)** — hierarchy of priority, often expressed via nesting.
