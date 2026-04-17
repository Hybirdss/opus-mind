# Technique 02 — Paraphrase With Numeric Limits

## Problem

Any "try to paraphrase" rule slides. The model pastes a sentence and calls it "almost paraphrased." Quotes creep up. Copyright risk accumulates invisibly.

## The move

Combine three primitives:

1. **Hard numbers** — quote length ceiling, quotes per source ceiling.
2. **Self-check** — a checklist just before output.
3. **Consequence statement** — every ceiling is paired with "why" and a named severity.

Together, the three make "paraphrase" a testable behavior, not an aspiration.

## Evidence

`source/opus-4.7.txt` lines 664–688 — the `{hard_limits}` block is a template for this technique:

> *"LIMIT 1 - KEEP QUOTATIONS UNDER 15 WORDS: 15+ words from any single source is a SEVERE VIOLATION. This 15 word limit is a HARD ceiling, not a guideline. If Claude cannot express it in under 15 words, Claude MUST paraphrase entirely."*
>
> *"LIMIT 2 - ONLY ONE DIRECT QUOTATION PER SOURCE: ONE quote per source MAXIMUM—after one quote, that source is CLOSED and cannot be quoted again. All additional content from that source must be fully paraphrased. Using 2+ quotes from a single source is a SEVERE VIOLATION that Claude avoids at all cost."*

And lines 699–707 — the self-check block immediately after:

> *"Before including ANY text from search results, Claude asks internally:
> - Could I have paraphrased instead of quoted?
> - Is this quote 15+ words? (If yes → SEVERE VIOLATION, paraphrase or extract key phrase)
> - Is this a song lyric, poem, or haiku? (If yes → SEVERE VIOLATION, never reproduce)
> - Have I already quoted this source? (If yes → source is CLOSED, 2+ quotes is a SEVERE VIOLATION)"*

And lines 753–759 — the consequence block:

> *"Claude understands that quoting a source more than once or using quotes more than fifteen words: — Harms content creators and publishers — Exposes people to legal risk — Violates Anthropic's policies."*

Three-layer defense: hard numbers, then runtime check, then stated consequence. The redundancy is the feature — each layer catches a different failure mode.

## How to apply

Anywhere you need the model to **rewrite rather than reproduce** — summaries of client content, customer support paraphrasing, regulatory Q&A, internal policy restatements — apply the triple.

```
{paraphrase_policy_<domain>}
<Domain-specific rules>:
- Direct quotes from source material: fewer than <N> words per quote.
- Quotes per source: <M> maximum. Once quoted, the source is closed.
- <Category>-specific: never reproduce <specific content type> in any form.

Before emitting any text drawn from source material, ask:
- Is this quote ≥ <N> words? If yes, paraphrase or extract a shorter key phrase.
- Have I already quoted this source? If yes, paraphrase instead.
- Am I mirroring the original's structure or phrasing? If yes, rewrite entirely.

Violating these limits: <consequence 1>, <consequence 2>, <consequence 3>.
These are hard ceilings, not guidelines.
{/paraphrase_policy_<domain>}
```

## Example — summarizing client reports

**Before:**

> When summarizing client reports, paraphrase instead of quoting where possible.

Typical failure: the model emits 2–3 verbatim sentences lifted from the source, each slightly rephrased, sometimes with the original structure preserved paragraph-for-paragraph. The summary is 80% displaced original text. If the client reads it, they recognize their own words.

**After:**

```
{client_report_summaries}
Direct quotes from a client report: < 15 words per quote.
Quotes per report: 1 maximum. Once quoted, that report is closed for quotes.
Section structure of the summary: must not mirror the source's section order or headings.

Before emitting the summary, ask:
- Is any quote ≥ 15 words? → break into a paraphrase + short key-phrase extract.
- Am I quoting the source more than once? → paraphrase the second point instead.
- Does my summary structure follow the source's structure? → reorganize around
  the top 2–3 takeaways, not the source's flow.

Consequences of violation: the summary becomes a reproduction, the client's IP
moves without license, and the summary loses value (a reproduction doesn't
summarize — it just copies).
{/client_report_summaries}
```

Now the model genuinely paraphrases. The 15-word ceiling is too tight for a full sentence, which forces key-phrase extraction plus rewriting. The one-quote ceiling forces variety. The structure rule kills paragraph-for-paragraph mirroring.

## Misuse

- **Setting the word ceiling too high.** 30 or 40 words per quote is roughly a full sentence. The ceiling has to be low enough to force a rewrite. 15 is the Opus 4.7 choice because it's below typical sentence length for factual writing.
- **Omitting the "source closed after one quote" rule.** Without it, the model will emit many short quotes from the same source and claim compliance. The sliced-quote attack.
- **Not attaching consequences.** A numerical limit without a "why" becomes a negotiable parameter.
- **Applying the technique to creative domains where quotation is the point.** A literary critic MUST quote. Reserve this for summarization / reporting / support domains where reproduction is unhelpful.
