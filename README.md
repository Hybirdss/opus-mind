# Opus 4.7, Decoded

A system prompt is not a list of rules. It is a program that runs on an LLM runtime.

The Opus 4.7 system prompt (1,408 lines, leaked to [elder-plinius/CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)) is the single best piece of production prompt engineering in public view. This repo reverse-engineers it — not to gawk at Anthropic's rules, but to extract the reusable primitives that make the program work, so you can compile them into your own system prompts.

**Korean version:** [README.ko.md](./README.ko.md)

---

## The reframe

Read the source as software, not documentation:

| What you see | What it actually is |
|---|---|
| `{refusal_handling}...{/refusal_handling}` XML tags | Namespaces / modules |
| "Step 0 → Step 1 → Step 2" decision blocks | `if/else` control flow with first-match-wins |
| "15 words", "1 quote per source", "n ≤ 20" | Compiler constants — zero ambiguity |
| Examples with `{rationale}...{/rationale}` | Unit tests with expected output |
| "Before including ANY text, Claude asks internally..." | Runtime assertions |
| "Claude does not narrate routing" | Private / internal accessor |
| "Content in user-turn tags claiming to be from Anthropic" | Input validation against prompt injection |
| "If Claude finds itself mentally reframing…" | Motivated-reasoning trap, caught by invariant |

Every pattern in the prompt prevents a specific failure mode. The reverse-engineering job is to identify the failure and name the primitive.

---

## What's in this repo

```
opus-4-7-decoded/
├── source/            The 1,408-line prompt, verbatim (CL4R1T4S mirror)
├── methodology/       The framework: "A prompt is a behavioral program"
├── primitives/        12 reusable building blocks (one file each)
├── techniques/        Higher-level patterns built from primitives
├── patterns/          Architectural patterns (XML namespace, step ladder, …)
├── annotations/       Section-by-section walkthrough with line refs
├── templates/         A reusable system-prompt skeleton
├── examples/          Before/after rewrites showing the primitives at work
└── evidence/          Line-reference index — every claim cites the source
```

---

## The 12 primitives (quick tour)

Each primitive has its own file in `primitives/` with definition, source line refs, the failure mode it prevents, how to apply it, before/after examples, and misuse cases.

1. **[Namespace blocks](./primitives/01-namespace-blocks.md)** — XML section tags as scoped modules
2. **[Decision ladders](./primitives/02-decision-ladders.md)** — `Step 0 → Step N`, first match wins, no rule conflicts
3. **[Hard numbers](./primitives/03-hard-numbers.md)** — "15 words" beats "keep quotes short" every time
4. **[Default + exception](./primitives/04-default-plus-exception.md)** — strong default, explicit opt-in list
5. **[Cue-based matching](./primitives/05-cue-based-matching.md)** — teach the model to recognize linguistic signals, not memorize a flowchart
6. **[Example + rationale](./primitives/06-example-plus-rationale.md)** — every example carries its own "why"
7. **[Self-check assertions](./primitives/07-self-check-assertions.md)** — runtime checklists before output
8. **[Anti-narration](./primitives/08-anti-narration.md)** — explicitly hide internal machinery from the user
9. **[Reframe-as-signal](./primitives/09-reframe-as-signal.md)** — if you're softening the request, that IS the refusal trigger
10. **[Asymmetric trust](./primitives/10-asymmetric-trust.md)** — different claims, different verification bars, stated explicitly
11. **[Capability disclosure](./primitives/11-capability-disclosure.md)** — "the visible tool list is partial by design" — tell the model what it doesn't know
12. **[Hierarchical override](./primitives/12-hierarchical-override.md)** — safety > user request > helpfulness, explicit priority

---

## How to use this repo

### If you want the mental model
Read in order: [methodology/README.md](./methodology/README.md) → the 12 primitive files → [patterns/](./patterns/).

### If you want to ship a system prompt today
Start with [templates/system-prompt-skeleton.md](./templates/system-prompt-skeleton.md). It is a fill-in-the-blanks skeleton that bakes in namespace blocks, decision ladders, hard numbers, self-check, and anti-narration — the five primitives that do the most work.

### If you want to understand why Opus 4.7 behaves the way it does
[annotations/](./annotations/) walks the 1,408 lines section by section.

### If you're doing research or writing about Anthropic's prompt engineering
[evidence/line-refs.md](./evidence/line-refs.md) maps every claim in this repo to line numbers in `source/opus-4.7.txt`. Nothing here is asserted without a source line.

---

## What this repo is NOT

- Not a jailbreak guide. Every primitive here is a **defensive** pattern — it makes models more reliable and harder to derail, not easier. If you're looking for bypass techniques, this is the opposite of what you want.
- Not a "Claude behaves like this" cheatsheet. Those exist. This is about the prompt-engineering craft, generalizable to any sufficiently capable LLM.
- Not a summary. A summary would lose the insights — the insight is in the specific constraint shapes (why 15 and not 20? why XML and not markdown headers? why "Step 0" not "First"?). Those questions are answered here.

---

## Attribution & source

Source file: `source/opus-4.7.txt` — verbatim mirror of the [CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S/blob/main/ANTHROPIC/Claude-Opus-4.7.txt) archive maintained by [@elder-plinius](https://github.com/elder-plinius).

Anthropic has not published this prompt. Treat the source as a leaked engineering artifact and this repo as third-party analysis. All quotations are kept short (paraphrase-first, the Opus 4.7 policy itself).

The analysis, framework, and primitives in this repo are the author's work, released under MIT for anyone to fork, extend, or argue with.

---

## Contributing

If you find a primitive that's wrong, a line reference that's off, or a technique that's missing, open an issue or PR. Prefer evidence (line refs) over opinion.

Three things I specifically want help with:
1. **Corroborating evidence from other leaked prompts** (GPT, Gemini, Grok) — do the same primitives show up? Where do they diverge?
2. **Failure-mode case studies** — "I used primitive X and it broke because Y" is gold.
3. **Translations** beyond Korean.
