# Pattern — Hard Tier Labels

## Observation

Opus 4.7 uses a small set of **tier labels** applied to rules: "SEVERE VIOLATION", "HARD LIMIT", "NON-NEGOTIABLE", "NEVER", "ABSOLUTE", "CRITICAL". These labels act as compiler directives — they tell the model how to treat the rule at runtime.

## The labels in use

**SEVERE VIOLATION** — "15+ words from any single source is a SEVERE VIOLATION" (line 640). Used for the top tier of copyright and content rules. Implies: this cannot be reasoned around.

**HARD LIMIT / HARD ceiling** — "This 15 word limit is a HARD LIMIT" (line 664), "a HARD ceiling, not a guideline" (line 682). Used to prevent "it's close enough" reasoning.

**NON-NEGOTIABLE** — "Copyright compliance is NON-NEGOTIABLE" (line 657). "These limits are NON-NEGOTIABLE" (line 591). Pre-empts negotiation attacks.

**NEVER** — "Claude NEVER creates romantic or sexual content involving or directed at minors" (line 32), "Claude NEVER reproduces copyrighted material" (line 663). Used for absolute prohibitions.

**ABSOLUTE / ABSOLUTE LIMITS** — "ABSOLUTE LIMITS — Claude never violates these limits under any circumstances" (line 678). The escalation when NEVER alone feels insufficient.

**CRITICAL** — "`{CRITICAL_COPYRIGHT_COMPLIANCE}`" section name (line 651), "CRITICAL BROWSER STORAGE RESTRICTION" (line 467). Used at the section-header level to signal that what follows is top-tier.

## Why labels are load-bearing

Rules without tier labels get treated as suggestions. A rule with a label is pre-categorized — the model doesn't have to infer severity from context.

**Consider the adjective "important."** "It's important that Claude not do X." The word is informational but carries no enforcement signal. The model can interpret "important" as "usually do this but exceptions exist."

**Now consider "SEVERE VIOLATION."** That phrase is category-coded. It maps to a behavior regime the model has training on — severe violations aren't exception-welcoming; they're refused.

The label is not decorative. It's the **enforcement handle** for the rule.

## Casing matters

ALLCAPS labels get noticed more than lowercase labels. This is not a theoretical claim — try it with a model. "15+ words is a severe violation" lands softer than "15+ words is a SEVERE VIOLATION."

Opus 4.7 uses ALLCAPS selectively:
- Tier labels: SEVERE VIOLATION, HARD LIMIT, NON-NEGOTIABLE, NEVER, ABSOLUTE, CRITICAL.
- Section names: `CRITICAL_COPYRIGHT_COMPLIANCE`.
- Emphasis on rule names: "STRICT QUOTATION RULE", "ONE QUOTE PER SOURCE MAXIMUM".

Not used for every high-stakes rule — only when the label is doing enforcement work. Over-using ALLCAPS dilutes it (every warning is a warning = no warning is a warning).

## Label + number = enforceable

The most effective pattern: tier label + hard number.

- "15+ words is a SEVERE VIOLATION" — both.
- "1 quote per source MAXIMUM" — both.
- "NEVER reproduce song lyrics (not even one line)" — label + explicit numeric carve-out ("not even one line").

Label alone: "no long quotes" — adjective, no ceiling.
Number alone: "< 15 words" — ceiling, no severity.
Together: the ceiling has teeth.

## How to apply

1. **Pick a small, consistent label vocabulary.** 4–6 labels for your entire prompt. Don't invent new ones per rule.
2. **Assign labels by tier.** Tier 1 rules get your strongest label. Tier 2 gets the second strongest. Don't give the same label to rules of different severity.
3. **Pair labels with numbers where possible.** "HARD LIMIT: ≤ N" is stronger than either alone.
4. **Use ALLCAPS selectively.** Reserve for actual enforcement labels. Don't caps-lock headers for style.
5. **State the consequence of violating a labeled rule at least once** (technique 04). The label plus the stated consequence is the full enforcement package.

## Anti-pattern

**Inflating the labels.** If every rule is "CRITICAL," none are. The label regime has to have variance — things that are CRITICAL, things that aren't.

**Using feelings-words as tier labels.** "Important," "recommended," "strongly preferred." These don't map to enforcement regimes; they map to fuzzy intensity.

**Labels without numeric ceilings for rules that could have them.** "The quote length is ABSOLUTE: keep it short." What's short? The label is doing no work.

## Sample label vocabulary for your own prompt

Start with these four:

- **NEVER** — top-tier absolute. Tier 1 safety violations.
- **SEVERE VIOLATION** — enforceable ceiling breach. Tier 2 IP / legal / PII violations.
- **HARD LIMIT** — numeric ceiling with enforcement (usually paired with a number).
- **DEFAULT** — the opposite direction — marks normal behavior, not a rule. Use to make the exception-free cases visible.

Add **CRITICAL** as a section-header qualifier (`{CRITICAL_ACCOUNT_ACCESS}`) for whole blocks that should be read with top-tier attention.

Five labels, clearly differentiated, applied consistently. That's enough.
