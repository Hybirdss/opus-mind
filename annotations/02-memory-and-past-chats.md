# Annotation 02 — Memory & Past Chats (lines 156–258)

Two adjacent blocks on how Claude accesses information outside the immediate conversation. Short but dense with technique.

## Structure

```
{memory_system}                lines 156–159
{persistent_storage_for_artifacts}  lines 161–233
{past_chats_tools}             lines 235–258
```

## Lines 156–159 — `{memory_system}`

Just four lines. The memory system and its enabled/disabled state. Notable pattern: the prompt states the state, not the capability.

> *"Claude has no memories of the user because the user has not enabled Claude's memory in Settings."*

The model is told **the current state** of memory, not a general "you might have memory, you might not." This prevents the "I may or may not remember things" hedging output that would otherwise emerge.

Instruction design move: **compress uncertainty into runtime state and inject state explicitly.** The model doesn't reason about whether memory exists; it's told.

## Lines 161–233 — `{persistent_storage_for_artifacts}`

Storage API documentation, mostly technical. Two instruction-design notes:

**Line 189 — the key-design pattern** combines hard numbers (keys < 200 chars) with a pattern statement (hierarchical keys). The numbered limit is adjacent to the stylistic guidance.

**Line 191 — batching instruction**:

> *"Combine data that's updated together in the same operation into single keys to avoid multiple sequential storage calls."*

This is an implicit performance rule, stated as a default pattern. Example immediately follows (line 192): "instead of `await set('cards'); await set('benefits'); await set('completion')` use `await set('cards-and-benefits', {cards, benefits, completion})`."

Pattern: API docs include **design guidance**, not just signatures. This is unusual — most SDK docs list methods and leave the architecture to the reader. The prompt acts as an opinionated SDK.

**Line 199** names an explicit UX obligation:

> *"When using shared data, inform users their data will be visible to others."*

Capability description (`shared: true`) paired with user-disclosure obligation. The two live together.

## Lines 235–258 — `{past_chats_tools}`

This block is unusually well-written as English prose. It is also the canonical example of **cue-based matching** (primitive 05).

### Line 236 — the why

> *"They exist because people naturally write as if Claude shares their history — they reference 'my project' or 'the bug we discussed' or 'what you suggested' without re-explaining, and if Claude doesn't recognize that as a cue to search, it breaks the continuity they're assuming and forces them to repeat themselves. An unnecessary search is cheap; a missed one costs the person real effort."*

Three things this sentence does:

1. States the user-experience failure mode (being forced to repeat yourself).
2. States the cost asymmetry (unnecessary search cheap, missed search expensive).
3. Frames the rule as a user-service obligation, not a mechanical rule.

The cost-asymmetry argument is worth internalizing: when two possible behaviors have asymmetric costs, the rule should lean to the cheap side. The model will drift toward the expensive side without explicit correction.

### Line 243 — the cue catalog

> *"The signals are linguistic: possessives without context ('my dissertation,' 'our approach'), definite articles assuming shared reference ('the script,' 'that strategy'), past-tense verbs about prior exchanges ('you recommended,' 'we decided'), or direct asks ('do you remember,' 'continue where we left off')."*

Four grammatical categories. Each one has 2 examples. Together they cover:

- Reference without antecedent.
- Implied prior conversation.
- Stated prior conversation.
- Explicit request for continuity.

Next line: *"The judgment is whether the person is writing as if Claude already knows something Claude doesn't see in this conversation."*

The summary sentence is the compressed rule. The four categories are the teachable surface.

### Lines 245–247 — tool choice

> *"`conversation_search` when there's a topic to match, `recent_chats` when the anchor is temporal ('yesterday,' 'last week,' 'my first chats'). When both apply, a specific time window is usually the stronger filter."*

One-sentence rule per tool, plus a tiebreaker. Economical.

### Line 247 — query construction

> *"It's a text match — the query needs words that actually appeared in the original discussion. That means content nouns (the topic, the proper noun, the project name), not meta-words like 'discussed' or 'conversation' or 'yesterday' that describe the act of talking rather than what was talked about. 'What did we discuss about Chinese robots yesterday?' → query 'Chinese robots', not 'discuss yesterday.'"*

This is a technique-adjacent instruction: **the query is not the question**. The model's default would be to pass the user's question verbatim. The rule redirects.

Notable pedagogical move: "content nouns vs meta-words" — a category the model can generalize from two negative examples ("discussed", "conversation").

### Lines 249–251 — tool mechanics

Hard numbers (primitive 03) for recent_chats:
- `n` caps at 20 per call.
- Pagination: `before` set to earliest `updated_at`.
- Stop after roughly 5 calls; tell the person the summary isn't comprehensive.

The "tell the person the summary isn't comprehensive" is an **uncertainty disclosure** that pairs with capability disclosure — when the model hits a limit, it names the limit. Not hides it.

### Lines 253–257 — boundary cases

Three positive/negative examples:

- **"How's my python project coming along?"** — possessive-without-antecedent + ongoing-state assumption. → search.
- **"What did we decide about that thing?"** — past-tense about prior exchange, but no content words. → ask.
- **"What's the capital of France?"** — no past-reference cue. → answer directly.

These three span the interesting space. They're also a mini-demonstration of example+rationale (primitive 06) — each case has a one-sentence rationale.

## Primitives and techniques evidenced

- 03 Hard numbers — storage API limits, recent_chats `n ≤ 20`, pagination cap.
- 05 Cue-based matching — canonical example at line 243.
- 06 Example + rationale — boundary cases at 253–257.
- 08 Anti-narration — results are "reference material for Claude, not text to quote back" (line 251).
- 11 Capability disclosure — "tell the person the summary isn't comprehensive" when hitting pagination limit (line 249).
- T01 Force tool call — line 241, "search — don't assume it doesn't exist."

## What to steal

If you're designing a memory/context-retrieval feature, study this section closely. The `past_chats_tools` block is ~25 lines and covers:

- When to invoke (cue-based).
- Tool choice (crisp two-way split with tiebreaker).
- Query construction (content nouns, not meta).
- Result handling (synthesize, don't quote back).
- Limit handling (disclose when hitting pagination).
- Boundary examples (three, with rationale).

That's a complete retrieval specification in 25 lines. The compression is instructive.
