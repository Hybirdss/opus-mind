# Pattern — Cue + Example + Rationale

## Observation

For any fuzzy pattern-recognition rule, Opus 4.7 teaches through three layers stacked together: **cue**, **example**, **rationale**. Not one or two — all three.

## The three layers

**Cue** — a linguistic or semantic signal to look for.

**Example** — a concrete input where the cue is present (or absent), with the correct response.

**Rationale** — why this response is correct. Names the principle.

Any two without the third is weaker than all three.

## Canonical instance — past chats (lines 243–257)

**Cue layer** (line 243):
> *"The signals are linguistic: possessives without context ('my dissertation,' 'our approach'), definite articles assuming shared reference ('the script,' 'that strategy'), past-tense verbs about prior exchanges ('you recommended,' 'we decided'), or direct asks ('do you remember,' 'continue where we left off')."*

Four grammatical categories, each with examples.

**Example layer** (lines 253–257):
- *"How's my python project coming along?"* — cue present.
- *"What did we decide about that thing?"* — cue present but content-empty.
- *"What's the capital of France?"* — no cue.

**Rationale layer** (same lines, inline):
- First: "the possessive plus the assumption of ongoing state is the cue. Search `python project`."
- Second: "no content words to search on. Ask which thing."
- Third: "no past-reference signal at all. Just answer."

Three cases, each with its rationale. Together they teach the principle ("search when language assumes shared memory; ask when cue is present but content-empty; skip when no cue").

## Other instances

**Image search examples** (lines 882–902): each example has a "Reason:" line.

**File creation advice** (line 281–289): triggers (cue) + the "standalone vs conversational" distinction (principle) + examples ("write me a quick 200-word blog post lol").

**Copyright examples** (lines 710–750): cue (what to quote) + example (specific user request and correct response) + {rationale} block.

**Request evaluation examples** (lines 566–584): six router cases, each with a one-line rationale.

Pattern repeats across domains.

## Why all three layers

Each layer fails alone:

- **Cue only**: the model knows what to look for but doesn't know what to do. "Search for X when you see Y" — OK, and then?
- **Example only**: the model pattern-matches the surface features but can't generalize. New inputs that don't look like the example fall through.
- **Rationale only**: too abstract. The model can't bridge principle to specific input.

Cue + example: the model generalizes poorly when new inputs lack surface similarity.
Example + rationale: the model can't spot when to fire the rule on novel inputs.
Cue + rationale: the model has the abstract machinery but no concrete anchor.

**All three**: cue tells the model when to attend, example provides an anchor, rationale provides the generalization engine.

## How to apply

For any rule more complex than a hard-numbered threshold:

1. **Cue**: 3–5 specific signals — words, grammatical features, topic types.
2. **Example**: 2–4 concrete inputs showing the cue (including at least one negative example).
3. **Rationale**: 1–2 sentences naming the principle each example embodies.

Total cost: usually 10–20 lines in your prompt. Benefit: the rule generalizes to inputs you never thought of.

## Anti-pattern

**Skipping the rationale.** "Do X. Here are 5 examples: …" Without rationale, the 5 examples are 5 data points — not a function.

**Rationale that restates the example.** "This is correct because the response addresses the question." Teaches nothing. The rationale must name the **general principle**.

**Too many cues.** Seven or more grammatical categories in the cue layer becomes a flowchart. The cue layer works because it's a small, legible cluster.
