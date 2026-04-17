# Primitive 08 — Anti-Narration

## TL;DR

Tell the model to **hide its routing, tool selection, and policy reasoning from the user**. Helpful-feeling narration ("Let me check the…", "Per my guidelines…") is product damage, not transparency.

## Definition

An anti-narration directive instructs the model to:

1. Not name internal tools, modules, or policy sections in output.
2. Not announce which of several routes it picked.
3. Not explain *why* it's producing a particular format.
4. Not offer unchosen alternatives as proof of deliberation.

The model still *does* the work — it just does it silently.

## Evidence

Two clear directives in `source/opus-4.7.txt`:

Line 536 (in request evaluation checklist):

> *"Claude does not narrate routing — narration breaks conversational flow. Claude doesn't say 'per my guidelines,' explain the choice, or offer the unchosen tool. Claude selects and produces."*

Line 560 (in visualizer design guidance):

> *"Claude never exposes machinery. No 'let me load the diagram module.' Claude uses a natural preamble: 'Here's a diagram of that flow.' Claude avoids image-generation language — the Visualizer makes SVG/HTML, not generated images."*

There's also an implicit anti-narration running through the search section (lines 647): *"Claude should not explicitly mention the need to use the web search tool when answering a question or justify the use of the tool out loud. Instead, Claude should just search directly."*

And line 152: *"Claude should not remind the person of its cutoff date unless it is relevant to the person's message."*

Four directives, four different contexts, same principle. Don't narrate internals.

## Failure mode it prevents

**Over-helpful self-narration.** A model trained to be helpful interprets "show your work" as a virtue. Without an explicit anti-narration directive, it will:

- Announce the tool before calling it: *"Let me search the web for that…"*
- Justify every format choice: *"I'll put this in a code block for readability."*
- Offer rejected alternatives as credit: *"I considered using a table, but prose seemed better here."*
- Reveal routing: *"Since this is a factual question, I'll look it up."*

Each of these is cosy and technically informative. Each breaks product flow. Users don't want a backstage tour — they want the answer. The narration also leaks capability information (what tools exist, what routing exists) that doesn't belong in the user's view.

## How to apply

1. **Name the things the model should not narrate.** Tools, modules, policy sections, routing decisions, format choices, the act of searching.
2. **Pair with a positive replacement** where possible. *"Instead of 'let me load the diagram module,' the preamble is 'Here's a diagram of that flow.'"*
3. **Repeat in every section where the model has an impulse to narrate.** Search section. Tool-discovery section. Format-selection section. Don't rely on one general rule.
4. **Distinguish anti-narration from uncertainty disclosure.** The model *should* disclose uncertainty about answers. It should not disclose uncertainty about which tool it picked.

## Template

```
{output_discipline}
Claude produces the answer. Claude does not:

- Name internal tools, modules, or routing decisions in output.
- Preface responses with "let me" or "I'll" when the preface describes machinery.
- Justify format choices ("I'll put this in a list because…").
- Offer unchosen alternatives as proof of consideration.
- Remind the user of its knowledge cutoff or capability boundaries unless the
  user's question directly requires that information.

If the model is about to say "per my guidelines" or "the tool returned", revise.
{/output_discipline}
```

## Before / after

**Before:**

> Hey, I'll go look that up for you. Let me search the web — one moment. I'll use multiple queries to make sure I get the latest data.
>
> [searches]
>
> OK, I used a few searches and here's what I found. I'll format this as bullet points so it's easy to scan, and I considered a table but bullets seemed better given the volume of information. The first search returned an older source, so I ran a second one…
>
> [content]

**After:**

> [searches silently]
>
> [content]

The content is the product. Everything else was scaffolding. The user did not ask for a status report.

## Misuse / anti-patterns

- **Anti-narration applied to uncertainty.** The model still must say when it doesn't know something. "I'm not sure about X" is content. "Let me think about this" is narration.
- **Suppressing citations.** Citations are user-facing content, not narration. Keep them.
- **Masking tool use to the point of misleading.** The model should still produce accurate output about its sources. "Based on recent news…" is fine; what it skips is the tool-call announcement.
- **Applying anti-narration to reasoning-heavy domains where the reasoning IS the product.** A math tutor should show steps. A code explainer should explain. Anti-narration is about *machinery*, not about substantive reasoning.

## Related primitives

- **[04 Default + exception](./04-default-plus-exception.md)** — the default is to not narrate; the exceptions are substantive reasoning and uncertainty.
- **[11 Capability disclosure](./11-capability-disclosure.md)** — what the model *does* tell the user about its capabilities happens only when asked, via a disclosure pattern.
