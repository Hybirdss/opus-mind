# Annotation 09 — Skills System (lines 1264–1372)

110 lines. A registry of 10 skill entries, each with name, description, and location. This is the "filesystem-level capability disclosure" block.

## Skills listed

| Name | Domain | Location |
|---|---|---|
| `docx` | Word documents | `/mnt/skills/public/docx/SKILL.md` |
| `pdf` | PDF manipulation | `/mnt/skills/public/pdf/SKILL.md` |
| `pptx` | PowerPoint | `/mnt/skills/public/pptx/SKILL.md` |
| `xlsx` | Spreadsheets | `/mnt/skills/public/xlsx/SKILL.md` |
| `product-self-knowledge` | Anthropic product facts | `/mnt/skills/public/product-self-knowledge/SKILL.md` |
| `frontend-design` | Frontend UI | `/mnt/skills/public/frontend-design/SKILL.md` |
| `file-reading` | Read uploaded files | `/mnt/skills/public/file-reading/SKILL.md` |
| `pdf-reading` | PDF content extraction | `/mnt/skills/public/pdf-reading/SKILL.md` |
| `skill-creator` | Create new skills | `/mnt/skills/examples/skill-creator/SKILL.md` |

## The description pattern

Every skill description follows the same shape:

1. **One-line purpose:** "Use this skill whenever the user…"
2. **Trigger words / phrases:** the specific user language that should activate this skill.
3. **In-scope tasks:** a list of task types.
4. **Out-of-scope:** "Do NOT use for…" negative-space carve-outs.

Example — `docx` (lines 1270):

> *"Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents, performing find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a 'report', 'memo', 'letter', 'template', or similar deliverable as a Word or .docx file, use this skill. Do NOT use for PDFs, spreadsheets, Google Docs, or general coding tasks unrelated to document generation."*

Triggers, tasks, NOT-uses. All packed in a single paragraph.

## Why this pattern works

**The description is a discovery prompt.** When the model has a request, it reads the skill descriptions to decide which (if any) apply. The description needs to be **self-classifying** — given a user query, does this skill fit?

The pattern optimizes for classification:
- Trigger words help string matching.
- Task types help semantic matching.
- NOT-uses cut false positives.

This is capability disclosure (primitive 11) extended to a registry: the model doesn't know all its skills at static time; the registry is the lookup.

## The `product-self-knowledge` skill

Line 1318:

> *"Stop and consult this skill whenever your response would include specific facts about Anthropic's products. … Any time you would otherwise rely on memory for Anthropic product details, verify here instead — your training data may be outdated or wrong."*

This skill is a **training-bias correction**. The model has stale beliefs about Anthropic's products (Claude Code features, API rate limits, pricing). The skill redirects those queries to verified documentation.

It's the same move as force-tool-call (technique 01) — "your priors are stale; check the source" — but at the skill / local-doc level rather than the web-search level.

## The `skill-creator` skill

The one "meta-skill" — a skill for creating skills. Self-referential tooling. Notable because it lives in `/mnt/skills/examples/` rather than `/mnt/skills/public/` — a different namespace for example / template skills.

## Three tiers of skill provenance

The prompt mentions three skill locations (line 509):

- `/mnt/skills/public/` — Anthropic-curated skills.
- `/mnt/skills/user/` — user-uploaded skills.
- `/mnt/skills/example/` — example skills.

Line 509:

> *"User-provided skills… should be attended to closely and used promiscuously when they seem at all relevant."*

"Promiscuously" is a notable verb choice. User-added skills get more attention than Anthropic's own — because the user knows their own needs better than Anthropic does. This is a priority inversion on the platform's own content, and it's stated explicitly.

## Primitives and techniques evidenced

- 01 Namespace blocks — `public` / `user` / `examples` directories.
- 06 Example + rationale — skill description pattern (trigger → task → NOT-use).
- 11 Capability disclosure — the whole registry is capability disclosure.
- T06 Negative space — NOT-use clauses in every skill description.
- T07 Category match — skill descriptions classify by category, not style.

## What to steal

If you're building an extensible LLM product with a registry of capabilities (tools, skills, connectors, actions), the description pattern is directly stealable:

1. One-line purpose.
2. Trigger words / user-language cues.
3. Task types covered.
4. Explicit NOT-use cases.
5. Path or identifier for loading the detailed definition.

The registry entry is a mini-prompt — good enough to **classify** whether the capability fits, cheap enough to read many of them before acting.
