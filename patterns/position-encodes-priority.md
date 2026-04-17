# Pattern — Position Encodes Priority

## Observation

The Opus 4.7 prompt is ordered deliberately. Character first, tool infrastructure middle, environment config last. Within each section, the opening sentence states the default. High-stakes rules get restated at both the beginning and end of their block.

## The three-part order

**First 154 lines — character.** Default stance, refusal handling, safety categories, tone. The identity layer.

**Middle ~600 lines — infrastructure.** Memory, past chats, file handling, skills, artifacts, request routing, visualizer, search, images.

**Last ~200 lines — environment.** Tool schemas, citations, skills list, network/filesystem config.

Why this order: **identity shapes behavior**. A model that has absorbed "Claude defaults to helping" on line 25 interprets every infrastructure rule through that stance. Flipping the order — config first, character last — would give the model a worse reading of the same content.

## Within sections

**First sentence states the default.** Check any `{…}` block:

- `{search_first}` line 5: "For any factual question about the present-day world, Claude must search before answering."
- `{default_stance}` line 25: "Claude defaults to helping."
- `{refusal_handling}` line 28: "Claude can discuss virtually any topic factually and objectively."
- `{tool_discovery}` line 138: "The visible tool list is partial by design."
- `{knowledge_cutoff}` line 147: "Claude's reliable knowledge cutoff date is the end of Jan 2026."

Every section's opening move is to **set the default**. Rules and exceptions follow.

## Bookend restatement

High-stakes rules appear at both beginning and end:

- Copyright: preamble (line 589) AND critical reminders (line 819).
- Harmful content: list (line 812) AND override statement (line 815).
- Safety override: default stance (line 25) AND injection defense (line 115).

The pattern: **open with the rule, repeat at close**. The middle carries the details; the bookends carry the priority.

## Within critical reminders (lines 818–834)

17 bullet-style reminders at the end of the search section, each 1–2 sentences. This is the "final pass" at attention. Content that appears here is what the author most feared would be forgotten.

First three items in this block:
1. Copyright hard limits.
2. Never output lyrics / poems / haikus.
3. Not a lawyer; no copyright speculation.

Three of 17 devoted to copyright. The author expected copyright violations more than other failure modes and weighted the final-pass accordingly.

## Why this works mechanically

LLMs have two known attention biases:

- **Primacy**: first tokens in a context get disproportionate attention.
- **Recency**: last tokens in a context get disproportionate attention.

Placing character at the start, critical reminders at the end, and infrastructure in the middle directly leverages these biases. You can't eliminate them; you can use them.

## How to apply

1. **Top of your prompt**: identity, mission, default stance, priority hierarchy. This is character.
2. **Middle**: tool descriptions, infrastructure, output routing, domain-specific rules.
3. **Bottom**: environment config, reminders, the "things you most want the model to remember."

Within each major section:

- First sentence = default.
- Mid-section = details, examples, exceptions.
- Last sentence(s) = critical restatement.

## Anti-pattern

**Putting rules in random order** and hoping attention averages out. The attention biases are real; they reward deliberate ordering.

**Over-weighting the tail** with a giant critical-reminders block at the end that re-states every rule. The tail works best when it highlights 3–10 items. A 50-item tail dilutes.
