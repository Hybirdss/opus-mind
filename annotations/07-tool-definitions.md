# Annotation 07 — Tool Definitions (lines 906–1241)

300+ lines of JSONSchema-like function definitions. The least prompt-engineered section of the document — mostly machine-readable schemas. But there are notable behavioral instructions embedded in the descriptions.

## Tools listed

| Tool | Purpose | Lines |
|---|---|---|
| `ask_user_input_v0` | Tappable-option elicitation widget | ~923 |
| `bash_tool` | Run shell commands | ~925 |
| `create_file` | Create files in sandbox | ~927 |
| `fetch_sports_data` | Sports scores / stats | ~929 |
| `image_search` | Web image search | ~931 |
| `message_compose_v1` | Email / Slack / text drafts | ~933 |
| `places_map_display_v0` | Render places on a map | ~935 |
| `places_search` | Search places / businesses | ~937 |
| `present_files` | Make files visible to user | ~939 |
| `recipe_display_v0` | Interactive recipe widget | ~941 |
| `recommend_claude_apps` | Recommend Anthropic apps | ~943 |
| `search_mcp_registry` | Search for MCP connectors | ~945 |
| `str_replace` | Edit files | ~947 |
| `suggest_connectors` | Prompt user to add connectors | ~949 |
| `view` | Read files / directories / images | ~951 |
| `weather_fetch` | Weather display | ~953 |
| `web_fetch` | Fetch URL contents | ~955 |
| `web_search` | Web search | ~957 |
| `visualize:read_me` | Load visual module | ~959 |
| `visualize:show_widget` | Render SVG / HTML widgets | ~961 |

## Behavioral content embedded in descriptions

The tool descriptions themselves contain behavioral rules. Three patterns:

**(a) Decision guidance in the description.** `ask_user_input_v0` (line 923) is mostly a description of WHEN NOT to use it:

> *"Use this for ELICITATION… WHEN NOT TO USE THIS TOOL: User asks 'A or B?' — they want YOUR analysis and recommendation. User is venting or processing emotions. User asks for your opinion. Factual questions. User needs prose feedback. User already gave you a detailed prompt with specific constraints."*

Six NOT-use cases vs about four USE cases. Negative-space technique (06) embedded in the schema description.

**(b) Anti-narration rules in tool descriptions.** `visualize:read_me` (line 959):

> *"Do NOT mention or narrate this call to the user — it is an internal setup step. Call it silently and proceed directly to the visualization in your response."*

The tool description itself carries the anti-narration rule. This is load-bearing because if the rule lived only in the system prompt's general anti-narration block, the model could forget to apply it here.

**(c) Product-design choices stated inline.** `message_compose_v1` (line 933):

> *"Generate 2-3 strategies that lead to different outcomes — not just tones. Label each clearly (e.g., 'Disagree and commit' vs 'Push for alignment'). Note what each prioritizes and trades off."*

"Different outcomes, not just tones" is a substantive product choice — the variants must represent different strategic approaches, not different wording styles. Embedded in the schema.

## Tool-schema design principles

Observations about how the schemas are structured:

**Description length is load-bearing.** The more behavioral nuance a tool has, the longer its description. `bash_tool` (~5 lines) vs `places_map_display_v0` (~35 lines of description explaining modes, fields, JSON examples).

**Examples embedded in descriptions.** `places_search` (line 937) contains a full JSON example showing multi-query usage. This is primitive 06 (example + rationale) at the tool level.

**Hard constraints stated as enum or constant.** Rather than "keep max_results small," the schema enforces `max_results: { minimum: 3, maximum: 5 }`. Hard numbers (primitive 03) at the type-system level.

**Warning-style rules for irreversible actions.** `search_mcp_registry` (line 945) includes:

> *"Returns results with connected status. Call suggest_connectors to show unconnected ones to the user."*

The tool chains — search tool's description references the suggest tool. This creates a **tool workflow** visible at the schema level.

## The visualize namespace

Two tools with a `visualize:` prefix:

- `visualize:read_me` — loads a design module (CSS vars, colors, typography, layout rules).
- `visualize:show_widget` — renders SVG / HTML inline.

The namespace is doing work — it signals "these tools are related, read_me is setup, show_widget is action." The prefix is itself a grouping primitive at the tool level.

## Connecting back to the prompt body

The tool schemas are the landing pad for behavioral rules stated earlier. Cross-references you can verify:

| Prompt-body rule | Tool-schema echo |
|---|---|
| Image search min 3, max 4 (line 872) | `image_search.max_results: { minimum: 3, maximum: 5 }` (line 931) |
| Anti-narration for visualizer (line 560) | `visualize:read_me` description says "Do NOT mention or narrate" (line 959) |
| Visualizer never generates images (line 560) | `visualize:show_widget` description says "SVG or HTML code" (line 961) |
| File outputs go in /mnt/user-data/outputs (line 336) | `present_files` description says "Makes files visible to the user" (line 939) |

The schemas reinforce the body text. The redundancy is a feature — behavior described in body + capability described in schema = harder to forget.

## Primitives and techniques evidenced

- 01 Namespace blocks — `visualize:` prefix as a namespace.
- 03 Hard numbers — enum and min/max constraints in JSONSchema.
- 04 Default + exception — `ask_user_input_v0` NOT-use list.
- 06 Example + rationale — full JSON examples in descriptions.
- 08 Anti-narration — embedded in `visualize:read_me` description.
- T06 Negative space — NOT-use lists in tool descriptions.

## What to steal

If you're designing a tool schema, write the description for a **model**, not a human reader. Include:

1. The core capability in one line.
2. Positive use cases (2–4 bullets).
3. Negative use cases — longer than positive — covering the model's likely over-use biases.
4. Behavioral rules (anti-narration, chaining, permissions).
5. Concrete examples for non-trivial inputs.
6. Hard constraints in the type system, not in prose.

The schemas in this prompt are simultaneously machine-readable specs AND mini-prompts about how to use the tool. That dual purpose is the pattern.
