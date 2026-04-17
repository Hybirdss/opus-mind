# Annotation 08 — Citation Instructions (lines 1242–1261)

20 lines. Covers how to format citations from web search results, using `{cite index="..."}...{/cite}` tags.

## The rule

Line 1245:

> *"EVERY specific claim in the answer that follows from the search results should be wrapped in {cite} tags around the claim."*

Index format:
- Single sentence: `{cite index="DOC_INDEX-SENTENCE_INDEX"}...{/cite}`
- Contiguous range: `{cite index="DOC_INDEX-START:END"}...{/cite}`
- Multiple ranges: comma-separated.

## The critical rule

Line 1254:

> *"Claims must be in your own words, never exact quoted text. Even short phrases from sources must be reworded. The citation tags are for attribution, not permission to reproduce original text."*

The citation system is attribution-only. It does not unlock quoting. The copyright rules stated earlier (< 15 words, 1 per source, paraphrase-first) still apply inside `{cite}` tags.

This is a clarification against a predictable misunderstanding: the model might assume that once a claim is cited, it can be reproduced verbatim. The rule closes that door explicitly.

## Example block (lines 1256–1259)

> Search result sentence: The move was a delight and a revelation.
> Correct citation: `{cite index="..."}The reviewer praised the film enthusiastically{/cite}`
> Incorrect citation: The reviewer called it `{cite index="..."}"a delight and a revelation"{/cite}`

The contrast pair (primitive 06) teaches the principle: citation wraps your paraphrase, not their quote.

Note the incorrect example: it's 5 words quoted, within the 15-word limit, only one quote — and it's still wrong because the rule is "paraphrase inside cite tags," not "short quotes OK inside cite tags."

## Primitives and techniques evidenced

- 03 Hard numbers — structural format requirement (DOC_INDEX-SENTENCE_INDEX).
- 06 Example + rationale — correct vs incorrect contrast.
- 12 Hierarchical override — copyright rules override citation convenience.
- T06 Negative space — "citation tags are NOT permission to reproduce."

## What to steal

When a feature could be misunderstood as unlocking a rule it does NOT unlock, state the non-unlock explicitly. The sentence *"The citation tags are for attribution, not permission to reproduce"* is worth its weight — without it, the model will likely over-quote inside citations.

This is a specific form of injection defense (technique 05) — against the feature's own gravity.
