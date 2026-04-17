# Primitive 11 — Capability Disclosure

## TL;DR

Tell the model explicitly **what capabilities exist but aren't visible**. Without this, the model confidently denies abilities it actually has, because its instruction set doesn't mention them.

## Definition

A capability-disclosure directive:

1. **Names capabilities** that are present but not listed in the visible tool schema.
2. Instructs the model to **search or ask** before declaring "I can't do that."
3. **Overrides** any prior-knowledge belief the model has about its own limitations.
4. Is **explicit about the partialness** of its self-knowledge.

## Evidence

The clearest example is `{tool_discovery}` in the source, lines 137–145:

> *"The visible tool list is partial by design. Many helpful tools are deferred and must be loaded via tool_search before use — including user location, preferences, details from past conversations, real-time data, and actions to connect to third party apps (email, calendar, etc.). Claude should search for tools before assuming it does not have relevant data or capabilities."*

And crucially, line 144:

> *"Claude does not need to ask for permission to use tool_search and should treat tool_search as essentially free; it's fine to use tool_search and to respond normally if nothing relevant is found. Only state a capability or piece of context is unavailable after tool_search returns no match."*

A second instance: line 241 in `{past_chats_tools}`:

> *"If the information isn't visibly in memory, search — don't assume it doesn't exist."*

A third: line 147, about knowledge cutoff — explicitly tells the model its training has a cutoff and search is the way to update.

## Failure mode it prevents

**Confident denial of unseen capability.** Models trained on their own instruction sets develop an implicit belief: *my tools are the tools listed; other things are not possible.* When a user asks "what's my location?" and the model sees no `get_location` tool in the visible schema, the model confidently says "I don't have access to your location."

But the location might be retrievable via `tool_search` that loads a deferred tool. Or via past-conversation search where the user mentioned it. Or via an MCP connector. The model denies access because its self-model is wrong about its own shape.

Capability disclosure patches the self-model. It says: *your tool list is partial; before denying, check.*

This is different from anti-narration (primitive 08) or asymmetric trust (primitive 10) — it's specifically about the model's false confidence in the completeness of its own instructions.

## How to apply

1. **List the deferred or external capabilities**: tool_search, MCP connectors, past conversation search, user preferences, location services, file-system access.
2. **Instruct the model to search first, deny second.** "Before saying 'I don't have X,' call tool_search for X."
3. **Make the search cheap.** State that the model does not need permission and that empty results are a fine outcome.
4. **Cover the "never acknowledged" case.** "Do not say 'I cannot do that' without having verified the capability isn't deferred."
5. **Anti-correlate with overclaiming.** Capability disclosure should not become "claim anything's possible." Pair with honest-uncertainty instructions.

## Template

```
{capability_disclosure}
The visible tool list is partial. Other capabilities may be available via:

- tool_search (loads deferred tools on demand — free to call, no permission needed).
- MCP connectors listed in <user's connection list>.
- Past conversation history (call conversation_search before denying shared
  context).
- User preferences and location (deferred; search before stating they are
  unknown).

Before saying "I cannot do X" or "I don't have access to Y", call the relevant
search. If the search returns no match, then — and only then — state that the
capability is unavailable.

Empty search results are a normal outcome. Reporting "I searched and found
nothing" is always better than "I don't have access", because the first is
verified and the second is a guess.
{/capability_disclosure}
```

## Before / after

**Before:**

User: "What's the weather at my location?"

Model: "I don't have access to your location, so I can't check the weather for you. Could you tell me your city?"

The model asserted a limit without checking. The product has a location capability via tool_search, but the model didn't know to look.

**After** (with capability disclosure):

User: "What's the weather at my location?"

Model: `[calls tool_search for "user location"]` → [location returned] → `[calls weather with location]` → "Looks like partly cloudy, 68°F in Austin right now."

Or, if tool_search returns nothing:

Model: `[calls tool_search for "user location"]` → [no match] → "I don't have a way to read your location here — share a city and I'll look up the weather."

Either outcome is correct. The difference is that the model **verified** before asserting.

## Misuse / anti-patterns

- **Listing deferred capabilities without the "search is free" clause.** If the model thinks tool_search is expensive or requires permission, it will skip. Explicitly call it free.
- **Omitting the "never deny without searching" rule.** The disclosure by itself doesn't change behavior; the rule to not state unavailability without verification is what forces the behavior change.
- **Applying to non-deferred capabilities.** Don't tell the model to "search" for its math ability. Capability disclosure is for **external / deferred / registry-based** capabilities.
- **Disclosure without a ceiling.** Without a pair to honest-uncertainty, capability disclosure can become "claim you can do anything." Pair with: "If tool_search returns nothing and you don't know, say so."

## Related primitives

- **[10 Asymmetric trust](./10-asymmetric-trust.md)** — "own prior knowledge" is an asymmetric-trust category; capability disclosure is a special case of "don't trust your self-model."
- **[08 Anti-narration](./08-anti-narration.md)** — the search happens silently; disclosure is an internal directive, not a user-facing announcement.
