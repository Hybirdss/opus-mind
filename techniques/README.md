# Techniques

Higher-level patterns built by composing the [12 primitives](../primitives/). Each technique is a known move — use the index below to pick the one that solves your problem.

| Technique | Problem it solves | Primitives composed |
|---|---|---|
| [01 Force tool call](./01-force-tool-call.md) | Model answers from stale priors instead of searching | 02 ladders, 06 examples, 10 asymmetric trust |
| [02 Paraphrase-with-numeric-limits](./02-paraphrase-with-numeric-limits.md) | Quotes grow, copyright creeps | 03 hard numbers, 07 self-check, consequence statement |
| [03 Caution contagion](./03-caution-contagion.md) | Model refuses once, then relents on softer follow-up | 09 reframe-as-signal, 12 hierarchical override |
| [04 Consequence statement](./04-consequence-statement.md) | Rule survives rephrasing attacks | 03 hard numbers, example+rationale |
| [05 Injection defense in-band](./05-injection-defense-in-band.md) | User content impersonates system instruction | 10 asymmetric trust, 12 hierarchical override |
| [06 Negative space](./06-negative-space.md) | Model does surprising thing you forgot to forbid | 04 default+exception, 06 example+rationale |
| [07 Category match](./07-category-match.md) | Model rationalizes its way out of a routing rule | 02 ladders, 05 cue-based |
