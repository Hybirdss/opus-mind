# Annotation 03 — Computer Use (lines 260–513)

The single largest behavior block. Covers skills, file handling, artifact routing, and sandbox mechanics. 250+ lines.

## Structure

```
{computer_use}
  {skills}                                  lines 261–278
  {file_creation_advice}                    lines 281–292
  {unnecessary_computer_use_avoidance}      lines 294–307
  {high_level_computer_use_explanation}     lines 309–319
  {file_handling_rules}                     lines 321–358
    {notes_on_user_uploaded_files}          lines 339–357
  {producing_outputs}                       lines 360–373
  {sharing_files}                           lines 375–393
    {good_file_sharing_examples}            lines 378–390
  {artifact_usage_criteria}                 lines 395–477
  {package_management}                      lines 479–484
  {examples}                                lines 485–499
  {additional_skills_reminder}              lines 500–512
{/computer_use}
```

12 sub-blocks. Heavy on file I/O semantics, heavy on routing.

## Lines 261–278 — `{skills}`

Skills are *"folders that contain a set of best practices for use in creating docs of different kinds."* The block tells Claude to read SKILL.md files before using computer tools.

Line 264 — the rule:

> *"Claude's first order of business should always be to examine the skills available in Claude's {available_skills} and decide which skills, if any, are relevant to the task. Then, Claude can and should use the `view` tool to read the appropriate SKILL.md files and follow their instructions."*

Three moves:

1. **Mandate the read before the action.** Read SKILL.md → then act.
2. **Allow multiple skills.** Line 262: *"Sometimes multiple skills may be required to get the best results, so Claude should not limit itself to just reading one."*
3. **Use concrete triggers.** Line 268–275 — three worked examples (pptx, docx, docx+imagegen) each showing the skill read happening as the first tool call.

This is capability disclosure (primitive 11) at the file-system level. The prompt tells Claude "you have these skills; read them before using their associated tools."

## Lines 281–292 — `{file_creation_advice}`

The file-vs-inline routing rule. This is technique 07 (category match) in pure form.

Line 281 — decision triggers:

```
- "write a document/report/post/article" → .md or .html
- "create a component/script/module" → code files
- "fix/modify/edit my file" → edit the uploaded file
- "make a presentation" → .pptx
- "save", "download", "file I can [view/keep/share]" → file
- writing more than 10 lines of code → file
```

Line 289 — the principle behind the triggers:

> *"The distinction that matters is whether the user is asking for a standalone piece of content or a conversational answer."*

Then the kill-the-decoy-axis move (lines 289–291):

> *"Tone and length don't change which bucket a request falls into: 'write me a quick 200-word blog post lol' is still a blog post (file); 'Please provide a formal strategic analysis' is still a strategy discussion (inline)."*

Length and tone are named as decoys. The category axis (standalone artifact vs conversational) is named as the real axis.

## Lines 294–307 — `{unnecessary_computer_use_avoidance}`

Pure negative-space technique (06). List of five cases where tools should NOT be used:

- Factual answers from training.
- Summarizing already-provided content.
- Explaining concepts.
- Short conversational content.
- (Specific restraint cases, lines 303–306.)

Line 301 is the meta-rule:

> *"Most people asking questions on Claude.ai are not developers, and most requests don't need a file. Before reaching for create_file, Claude considers whether an answer directly in the chat would serve the person just as well."*

The "most people are not developers" framing is a **user-model calibration** — a rare move. Most system prompts are audience-agnostic; this one explicitly states the modal user and lets the default bias toward that user.

## Lines 321–358 — `{file_handling_rules}`

Three filesystem locations with distinct semantics:

1. `/mnt/user-data/uploads` — read-only. User uploads.
2. `/home/claude` — Claude's scratch space. User can't see.
3. `/mnt/user-data/outputs` — final deliverables. User sees.

Line 336: *"It is very important to move final outputs to the /outputs directory. Without this step, users won't be able to see the work Claude has done."*

Stated consequence (technique 04). Without the consequence, the rule would be ignored under pressure — "oh it's fine, the file is on disk somewhere." With the consequence, the model knows the user cost.

Line 350 is a subtle but important rule:

> *"For files whose contents are already present in the context window, it is up to Claude to determine if it actually needs to access the computer to interact with the file, or if it can rely on the fact that it already has the contents of the file in the context window."*

Pairing of capability awareness with discretion. The file is in two places (context + disk). Claude chooses based on task.

## Lines 360–373 — `{producing_outputs}`

Two-part rule for file creation, parametrized by length:

> *"For SHORT content (<100 lines): Create the complete file in one tool call. Save directly to /mnt/user-data/outputs/.*
>
> *For LONG content (>100 lines): Use ITERATIVE EDITING — build the file across multiple tool calls. Start with outline/structure. Add content section by section. Review and refine. Copy final version to /mnt/user-data/outputs/."*

Hard number (100 lines) drives a process change. This is primitive 03 (hard numbers) affecting **workflow** rather than output content. Same mechanic.

## Lines 395–477 — `{artifact_usage_criteria}`

The longest single block in computer_use. Notable structure:

- *"Claude uses artifacts for"* — 9 positive cases (lines 398–407).
- *"Claude does NOT use artifacts for"* — 8 negative cases (lines 410–417).
- Technical guidance for each artifact type (lines 421–475).

This is negative-space technique (06) in its clearest form: the NOT list is longer than the USE list.

Lines 410–417 worth quoting partially (paraphrased for the one-quote-per-source rule):
- Short code (≤ 20 lines).
- Short creative (poems, haikus).
- Lists, tables — regardless of item count.
- Brief structured content.
- Single recipes.
- Short prose.
- Conversational responses.
- Content user explicitly asks for short.

Notice: **"regardless of item count"** on lists. That's the author anticipating a decoy axis — the model would otherwise think "long list → artifact." Countered.

Lines 467–474 — the **browser storage restriction**. Named as "CRITICAL" with consequence: *"cause artifacts to fail in the Claude.ai environment."* Hard capability rule (primitive 11) paired with consequence (technique 04).

## Lines 500–512 — `{additional_skills_reminder}`

Redundant reminder, repeated from earlier in the block. Line 511 explicitly says *"This is extremely important, so thanks for paying attention to it."*

The redundancy is deliberate. Load-bearing instructions that must not be forgotten get repeated at the end of the block. This is a **positional pattern** — first and last positions get better attention than middle positions, so the key rule gets stated in both.

## Primitives and techniques evidenced

- 02 Decision ladders — file-vs-inline routing (lines 281–292).
- 04 Default + exception — computer use default (use tools) with explicit "don't use when…" list.
- 06 Example + rationale — examples at lines 268–275, 378–390, 485–498.
- 07 Self-check assertions — implicit in `{examples}` block (lines 485–498) showing correct decisions.
- 11 Capability disclosure — skills system, deferred reading.
- T06 Negative space — artifact NOT-use list, computer-use NOT-use list.
- T07 Category match — file-vs-inline rule with length/tone named as decoys.
- T04 Consequence statement — "users won't be able to see" (line 336), "artifacts will fail" (line 468).

## What to steal

The artifact block is a master class in **teaching the model to under-use a capability it's biased to over-use**. If your product has a feature the model reaches for too eagerly (creating files, generating images, calling external APIs), copy this structure:

1. Positive use cases — 5–10 items, each specific.
2. Negative use cases — 5–10 items, longer than positive, each hitting a specific bias.
3. A principle sentence that resolves edge cases.
4. Decoy axes explicitly killed.
5. Reiteration at the end of the block.
