# Annotations — Section-By-Section

The 1,408-line Opus 4.7 system prompt walked section by section. Every sub-file maps a major XML block, calls out the specific primitives and techniques at work, and cites source line ranges.

**Reading order:** annotations are in source order. For thematic reading, start with the [primitives](../primitives/) and [techniques](../techniques/); come back here when you need evidence for a claim.

## Section map

| # | Source lines | Block | Annotation file | Primitives at work |
|---|---|---|---|---|
| 1 | 1–154 | `{claude_behavior}` | [01-core-behavior.md](./01-core-behavior.md) | 01, 04, 06, 08, 09, 10, 12 |
| 2 | 156–258 | Memory + past chats | [02-memory-and-past-chats.md](./02-memory-and-past-chats.md) | 05, 08, 11 |
| 3 | 260–513 | `{computer_use}` — skills, files, artifacts | [03-computer-use.md](./03-computer-use.md) | 02, 04, 06, 11 |
| 4 | 515–584 | Routing — request checklist + visualizer | [04-request-routing.md](./04-request-routing.md) | 02, 05, 07, 08, T07 |
| 5 | 586–835 | `{search_instructions}` + copyright | [05-search-and-copyright.md](./05-search-and-copyright.md) | 03, 06, 07, 12, T02, T04 |
| 6 | 837–904 | Image search tool | [06-image-search.md](./06-image-search.md) | 03, 04, 05 |
| 7 | 906–1241 | Tool definitions (schemas) | [07-tool-definitions.md](./07-tool-definitions.md) | 01, 03 |
| 8 | 1242–1261 | Citation instructions | [08-citations.md](./08-citations.md) | 03, 06 |
| 9 | 1264–1372 | `{available_skills}` | [09-skills-system.md](./09-skills-system.md) | 11, T07 |
| 10 | 1374–1408 | Network, filesystem, thinking mode | [10-config-and-environment.md](./10-config-and-environment.md) | 01, 03 |

(T## = technique numbers from [techniques/](../techniques/). Two-digit numbers = primitives.)

## Structural observation

Before diving in: notice how the prompt is ordered.

**First 154 lines** = core behavior. Who Claude is, what it defaults to, how it handles refusals, tone, safety. The "character" definition.

**Next ~100 lines** = memory and context tools. How Claude accesses what's outside its immediate view.

**Next ~250 lines** = computer use. Files, skills, artifacts — the heavy infrastructure.

**Next ~70 lines** = routing. Request evaluation and visualizer selection. This is unusually compact for how load-bearing it is.

**Middle 250 lines** = search and copyright. The single largest concentrated policy block. Copyright alone gets ~150 lines.

**Next ~70 lines** = image search.

**Rest** = tool schemas (machine-readable), skill registry, env config.

The order matters. Character first, because character frames everything downstream. Infrastructure second. Behavior specifics last. If you're writing your own prompt, this ordering is a good default.

## What to look for in each section

- **Opening sentence of a section usually states the default.** "Claude defaults to helping" (line 25). "Claude has access to…" (line 137). "Claude should always follow these principles" (line 596).
- **Hard numbers cluster in technical / safety-sensitive blocks**. Copyright (15, 1), search scaling (1, 3–5, 5–10), image count (3–4), artifact thresholds (20 lines, 1,500 chars).
- **Explicit priority statements live at policy boundaries**. "Non-negotiable" and "takes precedence over" mark tier-1 and tier-2 rules respectively.
- **Examples with rationale always follow rule blocks, not precede them**. Rule → example → rationale is the order. Read the rationale to generalize the rule.

## How to use annotations alongside primitives

When you see a design choice you want to replicate:

1. Find the section in annotations.
2. Identify the primitives at work (listed in the section map table).
3. Read those primitive docs for the *why*.
4. Apply the primitives to your own domain.

Annotations tell you *what* Opus 4.7 does. Primitives tell you *why*, and *how to do your own version*.
