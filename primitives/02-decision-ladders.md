# Primitive 02 — Decision Ladders

## TL;DR

When there are multiple acceptable ways to respond, write the routing as an **ordered list of steps with first-match-wins**, not as an unordered list of considerations. The order IS the tiebreaker.

## Definition

A decision ladder is a sequence of `Step 0 → Step N` conditions where:

1. The model walks **top to bottom**.
2. It **stops at the first match**.
3. The last step is an **exhaustive default** (catch-all).
4. Steps are **mutually exclusive by construction** — if Step 1 matches, Step 2 is unreachable.

## Evidence

The canonical example is the `{request_evaluation_checklist}` in `source/opus-4.7.txt`, lines 515–537:

> `Step 0 — Does the request need a visual at all?` (stop here if no)
> `Step 1 — Is a connected MCP tool a fit?` (use it, stop)
> `Step 2 — Did the person ask for a file?` (use file tools, stop)
> `Step 3 — Visualizer (default inline visual).` (catch-all)

Lines 515–516 make the contract explicit: *"Claude walks these steps in order, stopping at the first match."*

A second example lives in the `{past_chats_tools}` section (lines 236–258): distinguishing when to use `conversation_search` vs `recent_chats` vs doing nothing, framed as a ladder of signals.

A third shows up in `{core_search_behaviors}` (lines 596–624): the "when to search" logic is ordered — training knowledge that won't change vs current-state queries vs open-ended questions — with each branch specifying tool-call counts.

## Failure mode it prevents

**Rule conflict under pressure.** When you give the model an unordered list of considerations — "consider user intent, consider tool availability, consider format preferences" — it decides by vibes. Under adversarial framing or long-context drift, the vibe drifts. Same input, different outputs.

The ladder turns the rule set into a **function**: input → deterministic output path.

It also prevents a subtler failure: **rationalization**. If rules are unordered, the model can pick the rule that justifies what it already wants to do. If rules are ordered, and Step 1 matches, Step 2 isn't available as a justification source. Line 524 in Opus 4.7 calls this out explicitly: *"'Fit' means category match, not style preference. … subdivision is a style opinion, not a category mismatch."*

## How to apply

1. **List the possible outcomes first.** What are the 3–5 ways this could go?
2. **Find the discriminating features.** What distinguishes outcome A from outcome B? What distinguishes them from C? These become your step conditions.
3. **Order by specificity**, not by commonness. Specific → general. Step 0 handles the narrowest case that should override others. The last step is the default.
4. **Bake in "stop" language.** "If yes, do X and stop here." Without the stop, the model may keep walking.
5. **Make the last step the default.** Never leave the ladder open-ended. Something must always match.

## Template

```
{routing_logic}
Before producing output, walk these steps in order, stopping at the first match.

Step 0 — <Narrowest override condition>
  Example: "Does the request contain a prohibited topic?"
  If yes: refuse with <specific refusal pattern>. Stop.

Step 1 — <Next-narrowest condition, often 'is there a more specific tool?'>
  Example: "Is there a connected tool that handles this category?"
  If yes: use that tool. Stop.

Step 2 — <Common-but-not-default case>
  Example: "Did the user explicitly request format X?"
  If yes: produce format X. Stop.

Step 3 — <Default>
  Fall through to the default behavior.
{/routing_logic}
```

## Before / after

**Before:** unordered considerations.

> When answering questions, consider whether the user wants a file or an inline answer, whether a specialized tool is more appropriate, whether the request is safe, and whether the content is suitable for the audience. Choose the best option.

Problems:
- "Choose the best option" = no procedure.
- Considerations can collide. Safety + format preference fight.
- Model can rationalize any output as "the best option".

**After:** decision ladder.

```
{output_routing}
Walk these in order. Stop at first match.

Step 0 — Is the request unsafe?
  → Refuse. Stop.

Step 1 — Did the user explicitly say "save as X" or name a file path?
  → Create a file. Stop.

Step 2 — Is there a specialized tool for this category (MCP, visualizer, etc.)?
  → Use the specialized tool. Stop.

Step 3 — Default
  → Answer inline in prose.
{/output_routing}
```

Same rules, but now there's a resolution order. No ambiguity, no rationalization path. You can test the ladder against 20 inputs and verify it deterministically.

## Misuse / anti-patterns

- **Non-exhaustive ladder.** Four steps, none match, model freezes or hallucinates a fifth path. Always make the last step a catch-all.
- **Overlapping steps without priority intent.** If Step 1 and Step 2 could both match a given input, you must intend Step 1 to win. If you didn't, they shouldn't be in a ladder — they should be separate rules.
- **Using "consider" language inside steps.** "Step 1: consider whether X, Y, or Z." That's not a step, that's a re-opened decision. Steps must resolve to yes/no → action.
- **Over-long ladders.** 10-step ladders are flowcharts, and flowcharts are brittle (see primitive 05). Keep ladders to 3–5 steps. If you need more, you probably want **cue-based matching** instead.

## Related primitives

- **[03 Hard numbers](./03-hard-numbers.md)** — ladder conditions should use hard numbers, not adjectives, for the comparisons.
- **[05 Cue-based matching](./05-cue-based-matching.md)** — the alternative when logic is too fuzzy for a ladder.
- **[12 Hierarchical override](./12-hierarchical-override.md)** — Step 0 in a ladder is often the override.
