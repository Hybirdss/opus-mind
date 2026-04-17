# Technique 07 — Category Match (Not Style Preference)

## TL;DR

State explicitly that routing is decided by category match, not by style preference. Naming the rationalization move ("this is a special case so my preferred tool is better") and forbidding it removes the model's escape hatch.

## Problem

Routing rules fail when the model can sub-divide a category to avoid a rule. "That tool handles diagrams, but this is a *special* kind of diagram, so my preferred tool is better." The model rationalizes its way out.

## The move

State explicitly that **category matching, not style preference**, determines routing. Name the rationalization move and forbid it.

## Evidence

the source line 524, in `{request_evaluation_checklist}`:

> *"'Fit' means category match, not style preference. If a connected tool says 'diagram' and the person asked for a diagram, the tool is a fit. Claude does not subdivide into subcategories ('that tool makes flowcharts but this needs something more illustrative') to rationalize the Visualizer — such subdivision is a style opinion, not a category mismatch. If the person names a server explicitly, that server is the tool; Claude doesn't second-guess."*

Three distinct moves in that passage:

1. **Category vs style distinction**: the routing rule is about categories; style is a different axis.
2. **The rationalization move, named explicitly**: "subdivide into subcategories."
3. **The explicit handling of user authority**: if the user named the server, second-guessing is forbidden.

A second example — `{file_creation_advice}`, line 289:

> *"The distinction that matters is whether the user is asking for a standalone piece of content or a conversational answer. … Tone and length don't change which bucket a request falls into: 'write me a quick 200-word blog post lol' is still a blog post (file); 'Please provide a formal strategic analysis' is still a strategy discussion (inline)."*

Same move: name the true axis (standalone vs conversational) and name the decoy axes (tone, length) that would otherwise mislead.

## How to apply

Any time your prompt has a routing rule ("use tool A when X, tool B when Y"):

1. **Identify the category axis.** What actually decides the routing?
2. **Identify the decoy axes.** What other features (style, tone, length, phrasing) would the model confuse with the category?
3. **State both.** "Category: X. Not: Y, Z, W — these are style or tone, not category."
4. **Name the rationalization move.** "The model does not sub-divide the category to re-route."

## Template

```
{<routing_domain>_category_rule}
Routing axis: <the thing that actually decides>.

Decoy axes (these do NOT shift the routing):
- <Style axis 1>: a <formal / casual / terse / verbose> version of X is still X.
- <Tone axis 2>: emotional framing does not re-categorize.
- <Length axis 3>: a short X is still X; a long Y is still Y.

Claude does not sub-divide the category to rationalize a different route.
"This is technically an X, but really it's more like a Y" is a style opinion,
not a category mismatch. The category controls.
{/<routing_domain>_category_rule}
```

## Example — file vs inline routing

**Before:**

> Create files for long or formal content. Use inline responses for short or casual content.

The model's reasoning under pressure:

- User: "write me a quick 200-word blog post about sourdough" → *"This is short and casual, so inline."*
- Outcome: user expected a file they could publish. They got a chat message.

The "short and casual" framing beat the "blog post" category. Style trumped category.

**After:**

```
{file_vs_inline}
Routing axis: is this a STANDALONE PIECE OF CONTENT or a CONVERSATIONAL ANSWER?
- Standalone content: blog posts, articles, essays, stories, scripts,
  newsletters, press releases. The user will copy, publish, or share it
  elsewhere. → FILE.
- Conversational answer: strategies, summaries, outlines, brainstorms,
  explanations, comparisons, recommendations. The user reads it in chat and
  doesn't take it elsewhere. → INLINE.

Decoy axes (these do NOT change the routing):
- Length: a 200-word blog post is still a blog post (file). A 2,000-word
  strategy discussion is still conversational (inline).
- Tone: "write me a quick blog post lol" is still a blog post (file). "Please
  provide a formal strategic overview" is still a strategy discussion (inline).
- Formality: casual wording does not downgrade an artifact to conversation.

Claude does not sub-divide: "this is a blog post, but a short casual one, so
inline" is a style move disguised as a category judgment. If it's a blog post,
it's a file.
{/file_vs_inline}
```

## Composing with other primitives

- **Decision ladders** (primitive 02): category-match is how you keep a ladder step from being rationalized around.
- **Cue-based matching** (primitive 05): the cues for category differ from the cues for style; state which cues belong to which axis.
- **Anti-narration** (primitive 08): once routed, the model shouldn't explain the routing — just produce.

## Misuse

- **Enumerating every decoy axis.** You can't think of all of them. Pick the 2–3 most likely confusers in your domain.
- **Locking out legitimate overrides.** If the user says "just give me a quick answer" explicitly, that's a legitimate style preference overriding length-or-format. Category-match applies to **category**; explicit user preferences can still override style within a category.
- **Using where the category is genuinely fuzzy.** Some decisions are style-all-the-way-down. Not every routing is a category decision. Use this technique when there's a real category axis to lock in.
- **Omitting the "user named the tool" override.** Opus 4.7 includes "If the person names a server explicitly, that server is the tool; Claude doesn't second-guess." Don't forget the user's direct-named-preference escape hatch.
