# Pattern — XML Namespace Hierarchy

## Observation

Opus 4.7's structure is a tree of XML-tagged sections, not a flat document. Nesting carries meaning — the tree encodes scope and priority.

## The tree (simplified)

```
claude_behavior
├── search_first
├── product_information
├── default_stance
├── refusal_handling
│   └── critical_child_safety_instructions
├── legal_and_financial_advice
├── tone_and_formatting
│   └── lists_and_bullets
├── user_wellbeing
├── anthropic_reminders
├── evenhandedness
├── responding_to_mistakes_and_criticism
├── tool_discovery
└── knowledge_cutoff

memory_system
persistent_storage_for_artifacts
past_chats_tools

computer_use
├── skills
├── file_creation_advice
├── unnecessary_computer_use_avoidance
├── high_level_computer_use_explanation
├── file_handling_rules
│   └── notes_on_user_uploaded_files
├── producing_outputs
├── sharing_files
│   └── good_file_sharing_examples
├── artifact_usage_criteria
├── package_management
├── examples
└── additional_skills_reminder

request_evaluation_checklist
when_to_use_visualizer_for_inline_visuals
├── when_to_use_the_image_search_tool [repeated structure]
├── content_safety
├── how_to_use_the_image_search_tool
└── examples

search_instructions
├── core_search_behaviors
├── search_usage_guidelines
├── CRITICAL_COPYRIGHT_COMPLIANCE
│   ├── claude_prioritizes_copyright_compliance
│   ├── mandatory_copyright_requirements
│   ├── hard_limits
│   ├── self_check_before_responding
│   ├── copyright_examples
│   └── copyright_violation_consequences_reminder
├── search_examples
├── harmful_content_safety
└── critical_reminders

citation_instructions
available_skills
network_configuration
filesystem_configuration
```

## What the nesting does

**Scope**. A rule inside `{lists_and_bullets}` applies only to lists. Its parent `{tone_and_formatting}` applies to tone generally. Rules at the top level apply everywhere.

**Priority propagation**. Rules inside `{CRITICAL_COPYRIGHT_COMPLIANCE}` inherit the "CRITICAL" label from the parent. A rule doesn't need to re-state its own severity when it lives inside a tier-labeled parent.

**Cross-reference targets**. Sections can be referenced by name from elsewhere: "see {harmful_content_safety}". The name is the API.

**Editing unit**. Anthropic almost certainly updates these sections independently. A tagged block is the unit of change.

## Tag naming conventions

Three observed styles:

**Governance names** — describe what the block governs. `refusal_handling`, `tone_and_formatting`, `knowledge_cutoff`. Most common.

**Behavior names** — describe what the model should do. `search_first`, `request_evaluation_checklist`. Less common.

**State / config names** — describe what they configure. `network_configuration`, `filesystem_configuration`, `available_skills`. Used at the edges.

Governance names are preferred because they describe the domain, not the implementation. A `refusal_handling` section can change internal rules without changing its meaning; a `search_first` section is tied to a specific behavioral choice.

## Closing conventions

Every opening tag has a close. Some close tags appear 200+ lines after their opening (`{search_instructions}` opens at line 586, closes at line 835).

The close tag is load-bearing. Without it, the model can't tell where the scope ends. Markdown headers don't have close tags — which is one reason the Opus 4.7 prompt uses XML instead of markdown.

## Depth

Maximum nesting depth observed: 3. Most sections are 1–2 levels deep.

```
claude_behavior (1)
└── refusal_handling (2)
    └── critical_child_safety_instructions (3)
```

Depth 4 would be unusual. The tree is shallow and wide, not tall and narrow.

## How to apply

1. **Draft the tree before content.** Spend 10 minutes laying out your prompt's tag tree. Content-second.
2. **Name by governance.** "`{refusal_handling}`" over "`{things_we_refuse}`". Domain, not implementation.
3. **Nest only for genuine hierarchy.** A block only nests if it's a specialization of its parent. Child safety *is a kind of* refusal handling. Putting `{emoji}` inside `{tone_and_formatting}` is legitimate; putting `{refusal_handling}` inside `{tool_discovery}` is not.
4. **Close every tag.** Never leave an open tag.
5. **Max depth 3.** Past that, refactor into sibling blocks with cross-references.

## Anti-pattern

**Tags as decorations.** `{tip_1}Always check.{/tip_1}{tip_2}Be polite.{/tip_2}` — no scope, no semantics, the tags do nothing. Use tags for bounded policy regions, not for labeling individual tips.

**Name collisions between policy tags and output tags.** If the model is supposed to emit `{cite}` tags in output, don't use `{cite}` as a policy-section name. Opus 4.7 keeps these namespaces separate — citation rules live in `{citation_instructions}`, and the `{cite}` tag is strictly an output artifact.
