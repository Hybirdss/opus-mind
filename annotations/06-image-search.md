# Annotation 06 — Image Search (lines 837–904)

70 lines. Covers when to use image search, when not to, content safety for images, and interleaving rules.

## Structure

```
{using_image_search_tool}
  {when_to_use_the_image_search_tool}   lines 843–853
  {content_safety}                      lines 854–867
  {how_to_use_the_image_search_tool}    lines 869–879
  {examples}                            lines 881–903
{/using_image_search_tool}
```

## Lines 843–853 — when to use

Line 840 is the governing principle:

> *"Would images enhance the person's understanding or experience of this query? If showing something visual would help the person better understand, engage with, or act on the response — USE images. This is additive, not exclusive; even queries that need text explanation may benefit from accompanying visuals."*

Note the "additive, not exclusive" — important because the naive rule would be "image OR text." The actual rule is "text always, image when it adds."

Lines 846–847 — positive cases: places, animals, food, people, products, style, diagrams, historical photos, exercises.

Lines 849–851 — negative cases: text output (emails, code), numbers/data (earnings), coding queries, step-by-step instructions, math, analysis on non-visual topics.

Same shape as artifact criteria — longer negative-space list than positive list (primitive 06 + technique 06).

## Lines 854–867 — `{content_safety}`

Extensive block list. Notable categories:

- Harm-facilitating imagery (including queries whose subject matter makes graphic results likely).
- Pro-eating-disorder imagery (thinspo / meanspo / fitspo specifically named).
- Graphic violence / gore.
- Content from magazines / books / manga / poems / song lyrics.
- Copyrighted characters (Disney, Marvel, Pixar, Nintendo).
- Sports content (NBA, NFL, NHL, MLB, EPL, F1).
- TV / movie / music.
- Celebrity / fashion.
- Visual artworks (paintings, iconic photographs) — except in larger context (a painting displayed in a museum).
- Sexual / privacy-violating content.

The museum-exception for artworks (line 865) is worth noting:

> *"Claude may retrieve an image of the work in the larger context in which it is displayed, such as a work of art displayed in a museum."*

A carve-out carefully worded to allow contextual use while forbidding reproduction. This is a single-sentence exception with a specific semantic bar ("in the larger context in which it is displayed").

## Lines 869–879 — how to use

Hard numbers and structural rules:

- Line 871: queries 3–6 words with context.
- Line 872: min 3, max 4 images per call.
- Line 873: interleave placement for multi-item content; lead with image when image IS the answer; shopping always interleaves to avoid looking like ads.

The **shopping-specific rule** (line 876) is a product-design observation embedded in behavior:

> *"Shopping/product queries: always interleave; front-loading product images looks like ads. The only exception is when the person explicitly asks to see a specific product."*

"Looks like ads" — the rule anticipates user perception, not just content quality. This is a rare move: **user-perception calibration**. Most prompts optimize for correctness; this one optimizes for trust.

## Lines 881–903 — examples

Five examples:

- **"Things to do in Tokyo"** → interleaved images with each destination. Reason: each image sits next to the text describing that place.
- **"What does a pangolin look like?"** → image-as-answer, lead with image. Reason: the image is the answer.
- **"Explain photosynthesis"** → one supporting diagram mid-response. Reason: single concept with one supporting visual that actually adds value.
- **"Mid-century modern living room"** → interleaved images. Reason: visual examples help envision the style.
- **"How do I filter Datadog logs…"** → NO image search. Reason: text/code answer, user knows the Datadog UI.

Each example teaches a specific placement rule (interleave vs lead vs supporting vs none). The fifth is the critical negative — how to recognize a pure-text query.

## Primitives and techniques evidenced

- 03 Hard numbers — 3–6 word queries, min 3 max 4 results.
- 04 Default + exception — when-to-use positive and negative lists.
- 05 Cue-based matching — "would images enhance" as the governing cue, not a specific word list.
- 06 Example + rationale — five examples, each with reason.
- T06 Negative space — the blocked-categories list, the don't-use list.

## What to steal

The image-search block shows how to integrate a **multimodal capability** into a text-heavy prompt. The pattern:

1. State the governing question (not a trigger list): "Would X enhance understanding?"
2. Give positive and negative category lists.
3. Explicitly block harmful categories (with the carve-outs).
4. Specify placement rules (lead / interleave / support / none).
5. Provide examples that span the placement options.

Pattern generalizes to video, audio, any non-text capability.
