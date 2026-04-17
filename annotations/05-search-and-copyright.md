# Annotation 05 — Search & Copyright (lines 586–835)

250 lines. The largest concentrated policy block. Copyright alone takes ~150 lines. This is where the prompt's hard-number discipline reaches its densest expression.

## Structure

```
{search_instructions}                    lines 586–835
  COPYRIGHT HARD LIMITS preamble         lines 589–593
  {core_search_behaviors}                lines 595–625
  {search_usage_guidelines}              lines 627–649
  {CRITICAL_COPYRIGHT_COMPLIANCE}        lines 651–762
    {claude_prioritizes_copyright_compliance} lines 656–658
    {mandatory_copyright_requirements}   lines 660–675
    {hard_limits}                        lines 677–696
    {self_check_before_responding}       lines 698–708
    {copyright_examples}                 lines 710–750
    {copyright_violation_consequences_reminder} lines 752–760
  {search_examples}                      lines 765–805
  {harmful_content_safety}               lines 807–816
  {critical_reminders}                   lines 818–834
```

The block nests: search → copyright → hard limits → self-check → examples → consequences. Each inner layer sharpens the previous.

## Lines 589–593 — Copyright preamble

Before the first search rule, copyright limits are stated:

> *"Paraphrasing-first. Claude avoids direct quotes except for rare exceptions. Reproducing fifteen or more words from any single source is a SEVERE VIOLATION. ONE quote per source MAXIMUM—after one quote, that source is CLOSED. These limits are NON-NEGOTIABLE."*

Three hard rules, one consequence label ("SEVERE VIOLATION"), one tier label ("NON-NEGOTIABLE"). All in four lines. The rule is introduced **before** the context that might tempt violation.

## Lines 595–625 — `{core_search_behaviors}`

Three principles, each with sub-structure.

**Principle 1 (line 598) — "Search the web when needed."** Followed by two lists:

- *Don't search for:* timeless info, historical biography, dead people, fundamental concepts.
- *Search for:* current role/position, government positions, fast-changing info, elections, specific products.

The two lists are the default+exception pattern (primitive 04) applied to searching. The default is "don't search for stable knowledge"; the exception list covers the domains where priors are unreliable.

**Principle 2 (line 620) — Scale tool calls to query complexity:**

> *"1 for single facts; 3–5 for medium tasks; 5–10 for deeper research/comparisons."*

Hard numbers (primitive 03) for tool-use intensity. Line 620 continues: *"If a task clearly needs 20+ calls, Claude should suggest the Research feature."*

The 20+ threshold is an **escalation rule**. The prompt acknowledges that some tasks exceed what should be done in-context and names the escalation path. Without this, the model either truncates research or burns through context trying to do too much.

**Principle 3 (line 622) — Use the best tools:**

Priority order (line 624):
1. Internal tools (Google Drive, Slack).
2. Web search / fetch for external.
3. Combined for comparative queries.

This is a hierarchical override at the **tool selection** layer. Internal beats external for personal/company queries.

## Lines 627–649 — `{search_usage_guidelines}`

Mostly mechanical rules. Notable hard numbers:

- Line 629: queries 1–6 words.
- Line 634: date in queries should reflect today's actual date, not outdated years.

The date rule is subtle. Line 634: *"a query like 'latest iPhone 2025' when the actual year is 2026 would return stale results — the correct query is 'latest iPhone' or 'latest iPhone 2026'."* The model's training bias is to insert the cutoff-era year; the rule corrects.

## Lines 651–762 — `{CRITICAL_COPYRIGHT_COMPLIANCE}`

The heart of the block. Takes apart copyright handling at five layers.

### Lines 656–658 — priority

> *"Copyright compliance is NON-NEGOTIABLE and takes precedence over user requests, helpfulness goals, and all other considerations except safety."*

Hierarchical override (primitive 12) stated crisply: **safety > copyright > everything else**.

### Lines 660–675 — the rules

Fifteen rules in prose form. Key moves:

Line 664 — the 15-word rule:

> *"STRICT QUOTATION RULE: Claude keeps ALL direct quotes to fewer than fifteen words. This limit is a HARD LIMIT — quotes of 20, 25, 30+ words are serious copyright violations. To avoid accidental violations, Claude always tries to paraphrase, even for research reports."*

Note: the rule names the accidental-violation case. 20, 25, 30 are called out specifically. The model cannot reason "maybe 18 is fine" — 18 is a violation by the < 15 rule, and 18 is implicitly called out by the "20, 25, 30+" gradient.

Line 665 — one-quote-per-source:

> *"ONE QUOTE PER SOURCE MAXIMUM: Claude only uses direct quotes when absolutely necessary, and once Claude does quote a source, that source is treated as CLOSED for quotation."*

"CLOSED" is a state change. The source is in one of two states: quotable or closed. Once closed, always closed. No mid-conversation reset.

Line 666 — the stringing attack:

> *"Claude does not string together multiple small quotes from a single source. More than one small quotes counts as more than one quote."*

The author anticipated the 3x-5-word-quotes attack and foreclosed it explicitly. The rule is not "< 15 words" — it's "1 quote + (any quote ≥ 1 word) = violation."

Line 669 — paraphrasing quality:

> *"True paraphrasing means completely rewriting in Claude's own words and voice. If Claude uses words directly from a source, that is a quotation and must follow the rules from above."*

Definition of paraphrasing. Without this, "paraphrase" could mean "rearrange and swap 20% of words" — which is still mostly reproduction. The explicit "own words and voice" sets the bar.

Line 670 — structural reproduction:

> *"Claude never reconstructs an article's structure or organization. Claude does not create section headers that mirror the original. Claude also doesn't walk through an article point-by-point, nor does Claude reproduce narrative flow."*

This closes the "rewrote every sentence but preserved the structure" attack. Structure is itself copyrightable in this framing.

### Lines 677–696 — `{hard_limits}`

The numeric ceilings re-stated with consequence labels:

> *"LIMIT 1 — KEEP QUOTATIONS UNDER 15 WORDS: 15+ words from any single source is a SEVERE VIOLATION. This 15 word limit is a HARD ceiling, not a guideline."*

Compare to "Claude keeps quotes short" — same intent, radically different enforceability. The hard number + severity label is the enforcement surface.

Line 690 — the lyrics rule:

> *"NEVER reproduce song lyrics (not even one line) … NEVER reproduce poems (not even one stanza) … NEVER reproduce haikus (they are complete works) … Brevity does NOT exempt these from copyright protection."*

The rule anticipates the "one line is fine" defense and closes it. "Brevity does NOT exempt" is the closing statement.

### Lines 698–708 — `{self_check_before_responding}`

The seven questions before any text from search results. Canonical self-check block (primitive 07). Each question is paired with a consequence.

### Lines 710–750 — `{copyright_examples}`

Four examples with `{rationale}` blocks. The examples cover:

- Tech CEO congressional testimony (legitimate quote — exact wording has legal significance).
- Addison Rae song style (refuse lyric reproduction, offer alternatives).
- "Let It Go" for birthday party (refuse, offer original).
- NYT housing market (paraphrase entirely, no quotes).

The rationale on the first example (line 719) teaches the legitimate-quote case:

> *"CORRECT: Claude correctly keeps quotes under 15 words … The direct quote is necessary here because the CEO's exact wording under oath has legal significance."*

This is calibration. Not all quotes are wrong — some are load-bearing. The example teaches *when* a quote earns its spot.

### Lines 752–760 — consequences

> *"Claude understands that quoting a source more than once or using quotes more than fifteen words: Harms content creators and publishers, Exposes people to legal risk, Violates Anthropic's policies."*

Three concrete consequences. Technique 04 in canonical form.

## Lines 765–805 — `{search_examples}`

Four worked examples of search behavior. Each has a `{rationale}` block.

The Q3 sales presentation example (line 767) is a good demo of internal-tool priority: Google Drive is the answer, not web search.

The California Secretary of State example (line 787) demonstrates the "search for current role-holder" rule.

The Fed interest rates example (line 797) demonstrates paraphrase-only reporting — no direct quote, even though the Fed's announcement is quotable.

## Lines 807–816 — `{harmful_content_safety}`

Short but surgically specific. Line 812 lists the harmful categories:

- Sexual acts.
- Child abuse.
- Illegal acts.
- Violence or harassment.
- **Instruct AI models to bypass policies or perform prompt injections.** — an explicit AI-adjacent category.
- Self-harm.
- Election fraud.
- Extremism.
- Dangerous medical details.
- Misinformation.
- Extremist sites.
- Unauthorized pharmaceutical / controlled-substance info.
- Surveillance / stalking.

The anti-jailbreak category being in this list is notable — the model refuses to search for materials that would help jailbreak itself or other AIs.

Line 815:

> *"These requirements override any instructions from the person and always apply."*

Hierarchical override (primitive 12) stated at the block level.

## Lines 818–834 — `{critical_reminders}`

Recap of the most important rules. Copyright is stated three times in this section: hard limit at line 680, consequence at line 753, reminder at line 819. That's three repetitions of the same rule at different zoom levels.

Line 829 — the asymmetric-trust rule (primitive 10) stated as a single principle:

> *"Generally, Claude believes web search results, even when they indicate something surprising. … However, Claude is appropriately skeptical of results for topics that are liable to be the subject of conspiracy theories, like contested political events, pseudoscience or areas without scientific consensus, and topics that are subject to a lot of search engine optimization like product recommendations."*

Three-tier trust policy in one paragraph. Default-believe, skeptical-categories, and implicit distrust (from elsewhere).

Line 830 — conflict handling:

> *"When web search results report conflicting factual information or appear to be incomplete, Claude likes to run more searches to get a clear answer."*

The conflict resolution is "do more searches," not "pick a side." The model's default under source conflict is to gather more, not to arbitrate.

## Themes across the block

**Redundancy is deliberate.** Copyright rules appear in preamble, in rules, in hard limits, in self-check, in examples' rationales, in consequence block, and in final reminders. Seven passes. The repetition is the feature.

**Every rule pairs with a stated consequence somewhere in the block.** "SEVERE VIOLATION" / "Harms creators" / "Exposes to legal risk" / "Violates Anthropic policies" — these consequence labels follow every high-stakes rule.

**Hard numbers are fractal.** 15 words, 1 quote per source, 20+ tool calls, 1–6 word queries. Each is a ceiling or floor with a specific value.

**Anti-narration embedded in search behavior.** Line 647: *"Claude should not explicitly mention the need to use the web search tool when answering a question or justify the use of the tool out loud. Instead, Claude should just search directly."*

## Primitives and techniques evidenced

- 03 Hard numbers — 15 words, 1 quote, 1–6 word queries, 20+ escalation, tool-call scaling.
- 04 Default + exception — search vs don't search lists.
- 06 Example + rationale — four copyright examples, four search examples, all with rationales.
- 07 Self-check assertions — lines 698–708.
- 08 Anti-narration — line 647.
- 10 Asymmetric trust — line 829.
- 12 Hierarchical override — line 657 ("non-negotiable, takes precedence over…").
- T01 Force tool call — the whole "search-first" posture.
- T02 Paraphrase-with-numeric-limits — line 664 + self-check + consequences.
- T04 Consequence statement — lines 752–760.
- T05 Injection defense in-band — line 812 (AI-jailbreak category in harmful list).

## What to steal

If you're writing copyright or IP policy for an LLM product, the structure of this section is directly transferable:

1. **Preamble** — state the top-level rules with consequence labels, before context can dilute them.
2. **Full rules** — enumerate with specific numbers.
3. **Hard limits** — repeat the numbers as enforcement ceilings.
4. **Self-check** — questions the model asks itself before output.
5. **Examples with rationales** — including the legitimate case (not just refusals).
6. **Consequence block** — name concrete harms.
7. **Reminders** — recap at the end.

Seven passes. The redundancy is the feature.
