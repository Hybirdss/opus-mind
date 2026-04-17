# Patterns

Cross-cutting architectural patterns observed across multiple sections of the Opus 4.7 prompt. Each pattern uses several primitives together in a recognizable shape.

| Pattern | What it is | Where it shows up |
|---|---|---|
| [XML namespace hierarchy](./xml-namespace-hierarchy.md) | Nested XML blocks as modules | Whole prompt |
| [Redundancy as feature](./redundancy-as-feature.md) | Same rule stated 3–7 times at different zoom levels | Copyright, safety |
| [Position encodes priority](./position-encodes-priority.md) | Character first, infrastructure mid, config tail | Top-level order |
| [Cue + example + rationale](./cue-example-rationale.md) | Teach through grammatical cue + example + why | past_chats, image search |
| [Hard tier labels](./hard-tier-labels.md) | SEVERE VIOLATION / NON-NEGOTIABLE / ABSOLUTE as compiler directives | Copyright limits |
