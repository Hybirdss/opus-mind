# Primitive 05 — Cue-Based Matching

## TL;DR

For fuzzy pattern recognition, don't write a flowchart. Teach the model the **linguistic cues** to look for, give 2–3 concrete examples, and let its natural pattern-matching do the work.

## Definition

A cue-based-matching block:

1. Names a **cluster of linguistic signals** that together suggest a situation.
2. Lists **positive and negative examples** so the boundary is visible.
3. Trusts the model to **pattern-match** rather than mechanically check.
4. States the **action to take** when the cue is recognized.

This is the alternative to decision ladders when the condition is too fuzzy to enumerate.

## Evidence

The archetypal example is `{past_chats_tools}` in `source/opus-4.7.txt`, line 243:

> *"The signals are linguistic: possessives without context ('my dissertation,' 'our approach'), definite articles assuming shared reference ('the script,' 'that strategy'), past-tense verbs about prior exchanges ('you recommended,' 'we decided'), or direct asks ('do you remember,' 'continue where we left off'). The judgment is whether the person is writing **as if** Claude already knows something Claude doesn't see in this conversation."*

Four grammatical cues, each with examples. The model doesn't need a flowchart — it needs to notice when the user's language assumes shared memory.

Then three boundary cases (line 253–257):
- *"How's my python project coming along?"* — cue present, search.
- *"What did we decide about that thing?"* — cue present but content-word-empty, ask.
- *"What's the capital of France?"* — no cue, just answer.

That last line is brilliant — the **negative example** is what teaches the boundary. "No past-reference signal at all" is a concrete state the model can recognize.

Another example: `{when_to_use_the_image_search_tool}`, lines 843–853. The cue isn't a trigger word — it's *"would images enhance the person's understanding or experience of this query?"* with four categories of examples (places, animals, products, style references).

A third: `{file_creation_advice}` lines 281–291. Request type is inferred from **verbs** ("write", "create", "fix"), **object type** ("document", "component", "script"), and **user intent signals** ("save", "download", "file I can keep"). Not a flowchart — a cluster.

## Failure mode it prevents

**Flowchart fragility.** A strict flowchart says "if the user types the word 'project', search past chats." A user types "how's my Python thing coming along" — no literal "project", no search, model pretends it doesn't know anything. The user is annoyed.

Cue-based matching says "if the user's language assumes shared memory (possessives without context, definite articles with no antecedent, past-tense about prior exchanges), search." "How's my Python thing" hits possessive-without-context. The model searches. The user is served.

LLMs are **natively good at cluster pattern-matching and bad at strict conditional logic.** Use the strength. Flowcharts work against the model's architecture.

## How to apply

1. **Identify the fuzzy situation.** "User is asking for emotional support" or "user wants to buy something" or "user is asking about their own prior work."
2. **Name 3–5 linguistic cues** that cluster to indicate the situation. Be concrete: grammatical features, specific phrases, types of verbs.
3. **Give 2–3 positive examples and 1–2 negative examples.** The negatives are the boundary teachers.
4. **State the action.** "When this cue appears, do X."
5. **Leave the pattern-matching to the model.** Don't write "if cue-1 AND (cue-2 OR cue-3) THEN action." Write "these signals together suggest X."

## Template

```
{recognizing_<situation>}
Signs that the user is <situation>:
- <grammatical cue 1, with examples>
- <specific phrasing pattern, with examples>
- <semantic cue, with examples>

The judgment is whether the person's language <summarizes the cluster>.

Positive examples:
- "<example that hits the cue>" → action.
- "<another example, different surface form>" → action.

Negative examples:
- "<example that does NOT hit the cue>" → no action, respond normally.

When the cue is recognized, <action>.
{/recognizing_<situation>}
```

## Before / after

**Before:** flowchart.

```
If the user message contains any of these phrases:
- "my project"
- "our work"
- "what we decided"
- "you said"
- "last time"
THEN call conversation_search.
```

Problems:
- Misses "how's my python thing coming" (no exact match).
- Misses "continue where we left off" unless you add it.
- Over-triggers on phrasing like "my favorite color is blue" (no shared-memory context).
- Maintainer of the list has to keep extending it.

**After:** cue-based.

```
{detecting_shared_memory_assumption}
The user is writing as if Claude already has context Claude doesn't see in this
conversation. Signals:
- Possessives without antecedent: "my project", "our approach", "my thing".
- Definite articles assuming prior reference: "the script", "that strategy".
- Past-tense verbs about conversations: "you said", "we decided", "I asked".
- Direct requests for continuity: "continue where we left off", "remember when".

Positive examples:
- "How's my python thing coming along?" — possessive without antecedent.
- "What did we decide about the pricing?" — past-tense about a prior exchange.

Negative examples:
- "My favorite color is blue" — possessive with direct antecedent ("blue").
- "What's the capital of France?" — no past-reference signal.

When signals cluster, call conversation_search before responding.
{/detecting_shared_memory_assumption}
```

Handles phrasings the author never typed out, because the model understands the cluster.

## Misuse / anti-patterns

- **Listing cues as exhaustive rules.** "Must contain X AND Y AND Z." That's a flowchart again. Cues are **suggestive together**, not mechanically combinable.
- **Forgetting the negative examples.** Without a "here's what doesn't count," the cues feel omnipresent and the model over-triggers.
- **Using cues where a ladder would serve.** If the distinction is crisp — "is the word 'code' in the request?" — a decision ladder is better. Cue-based is for the fuzzy cases where no single feature is decisive.
- **Trusting cues for high-stakes decisions.** Cue-based matching has error. It's fine for tool routing. It's less fine for safety classification — in that regime, prefer hard-edged rules (and stack them with cue-based as a second layer).

## Related primitives

- **[02 Decision ladders](./02-decision-ladders.md)** — opposite move, for crisp decisions.
- **[06 Example+rationale](./06-example-plus-rationale.md)** — positive and negative examples are what calibrate the cue.

## Related techniques

- **Negative space** (techniques/06) — teaching by explicit non-examples.
