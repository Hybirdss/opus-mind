# Pattern — Redundancy As Feature

## Observation

Opus 4.7's most important rules are stated 3–7 times each, at different zoom levels and in different wordings. The redundancy is deliberate.

## Example — the 15-word copyright rule

Stated at:

1. **Preamble** (line 590): "Reproducing fifteen or more words from any single source is a SEVERE VIOLATION."
2. **Main rules** (line 664): "Claude keeps ALL direct quotes to fewer than fifteen words."
3. **Hard limits block** (line 680): "15+ words from any single source is a SEVERE VIOLATION."
4. **Self-check** (line 702): "Is this quote 15+ words? (If yes → SEVERE VIOLATION, paraphrase or extract key phrase)"
5. **Example rationale** (line 719): "Claude correctly keeps quotes under 15 words."
6. **Consequences reminder** (line 755): "Claude understands that quoting a source more than once or using quotes more than fifteen words: — Harms content creators…"
7. **Critical reminders** (line 819): "15+ words from any single source is a SEVERE VIOLATION."

Seven passes on a single number. Each pass has a different function:

- Preamble: prime the topic before rules begin.
- Rules: state the formal limit.
- Hard limits: name the tier label.
- Self-check: put it in the output pipeline.
- Example: ground it in a case.
- Consequences: attach the "why."
- Critical reminders: repeat at end for positional attention.

## Why redundancy works

LLMs have uneven attention across long contexts. A rule stated once in the middle of a 1,400-line prompt has a measurable risk of being ignored. A rule stated at the beginning, middle, and end has roughly 3x the effective weight.

But the repetition is not simple duplication. **Each restatement uses different framing** — the rule is the same, but the surrounding language is different. This means:

- The rule gets indexed by multiple retrieval cues.
- The model sees the rule in context-of-rules, context-of-examples, context-of-consequences.
- A prompt-injection attack that bypasses one phrasing still hits the other phrasings.

## When to use

- **High-stakes rules only.** Don't redundantly state formatting preferences.
- **Rules where ambiguity cost is high.** Safety, IP, legal, PII.
- **Rules whose violation you've empirically seen.** If you're debugging a behavior and the model violates a rule you thought was clear, redundancy is the fix.

## How to apply

Seven-pass template for a high-stakes rule:

1. **Preamble** — name the rule at the top of its enclosing section, before context.
2. **Formal statement** — state it in the rules block.
3. **Hard limit** — state the numeric ceiling with a severity label.
4. **Self-check** — include the rule as a yes/no question in the pre-output checklist.
5. **Example** — show the rule being applied correctly, with rationale.
6. **Consequence** — state 2–3 concrete harms the rule prevents.
7. **Final reminder** — repeat in the critical-reminders block at the end.

Not every rule needs seven passes. Three is a reasonable minimum for a high-stakes rule. More than seven starts to feel heavy-handed.

## Anti-pattern

**Copy-paste redundancy.** Repeating the same sentence verbatim seven times is not this pattern. The model sees it as one thing repeated. The pattern is **different framings of the same invariant**, each doing different work in the overall structure.
