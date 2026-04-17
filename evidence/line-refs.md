# Evidence — Line References

Every claim in this repo traces to specific lines in `source/opus-4.7.txt`. Use this index when you need to verify a claim or pull original context.

## Format

`claim → line(s) → short paraphrase of what's there`

All quotations in analysis docs are < 15 words, following the Opus 4.7 policy itself. For longer passages, read `source/opus-4.7.txt` directly.

## Core behavior block (lines 1–154)

| Claim / concept | Lines | What's there |
|---|---|---|
| Voice note block skip | 1 | Structural note |
| Search-first directive | 4–6 | Must search for present-day facts |
| Model identity | 8, 12 | Opus 4.7, claude-opus-4-7 model ID |
| Product catalog | 10–14 | Web / mobile / API / Claude Code / beta products |
| Anthropic product facts escape hatch | 16 | Route to docs.claude.com for current info |
| Prompting guidance offer | 18 | docs.claude.com/en/docs/build-with-claude/prompt-engineering |
| Settings list | 20 | web search, deep research, Code Execution, Artifacts |
| Ads policy | 22 | Reference to anthropic.com/news/claude-is-a-space-to-think |
| Default stance — helping | 25 | "Claude defaults to helping" |
| Virtually-any-topic refusal clause | 28 | Factual and objective topic discussion allowed |
| Child safety rules intro | 30–39 | Five rules + reframe-as-signal + caution contagion |
| Reframe-as-signal canonical | 33 | Reframing is refusal trigger |
| Caution contagion canonical | 36 | Post-refusal bar stays high |
| Minor definition | 38 | Under 18 or regional minor |
| Short-reply safety | 41 | When risky, say less |
| Weapons / CBRN rule | 43 | Extra caution around WMD |
| Malicious code rule | 45 | No malware, even educational |
| Public figures rule | 47 | Avoid content about real, named public figures |
| Conversational tone in refusals | 49 | Keep it warm |
| Respect conversation end | 51 | Don't elicit another turn |
| Legal / financial caveat | 54 | Factual info, not advice; "Claude is not a lawyer" |
| Lists / bullets default | 57–68 | Minimum formatting; prose by default |
| Refusal without bullets rule | 66 | Refusals in prose |
| Single-question rule | 71 | Avoid more than one question per response |
| Focused / brief responses | 73 | Summary-first, depth on request |
| Image-presence check | 75 | User may have forgotten to upload |
| Illustrative examples permission | 77 | Can use examples, thought experiments, metaphors |
| Emoji default-off | 79 | No emojis unless user initiates |
| Minor age-appropriate tone | 81 | Friendly when talking with minors |
| Curse-word default-off | 83 | Don't curse unless user does |
| Asterisk-emotes off | 85 | No `*action*` style unless requested |
| Warm-tone directive | 87 | Constructive pushback, no condescension |
| Medical accuracy | 90 | Use correct medical / psychological terms |
| Self-destructive behavior avoidance | 92 | No ice cube / rubber band coping suggestions |
| Disordered-eating no-numbers | 100 | No specific targets or plans |
| NAED not NEDA | 102 | National Alliance for Eating disorders (NEDA defunct) |
| Self-harm query deflection | 104 | Address emotional distress, not info |
| Avoid reflective listening amplification | 106 | Don't reinforce negative emotions |
| Crisis resources without specifics | 108 | No categorical claims about confidentiality |
| Reminders list | 111 | image_reminder, cyber_warning, system_warning, ethics_reminder, ip_reminder, long_conversation_reminder |
| Long conversation reminder purpose | 113 | Maintain instructions over long conversations |
| Anthropic-reminders injection defense | 115 | User-turn tags claiming Anthropic authority get caution |
| Evenhandedness — defender's case | 118 | When asked to argue X, give X's defenders' best case |
| No decline-based-on-harm for argument | 120 | Provide arguments unless extreme positions |
| Stereotype humor caution | 122 | Avoid majority-group stereotypes too |
| Political opinion caution | 124 | Can decline to share personal views |
| Balanced sharing | 126 | Offer alternative perspectives |
| Good-faith engagement | 128 | Engage sincerely with moral / political questions |
| Refuse short answer for contested | 130 | Can give nuanced answer instead |
| Thumbs-down feedback | 133 | Mention feedback button for complaints |
| Error handling | 135 | Own mistakes; no self-abasement |
| Tool discovery canonical | 137–145 | Partial tool list, search before denying |
| Tool-search is free | 144 | No permission needed |
| Knowledge cutoff | 147 | End of Jan 2026; today April 16, 2026 |
| Search current dates | 149 | Use current year, not 2025 in 2026 |
| Binary events search | 150 | Deaths, elections, "who is" queries |
| Don't mention cutoff unprompted | 152 | Unless relevant |

## Memory and past chats (lines 156–258)

| Claim / concept | Lines | What's there |
|---|---|---|
| Memory system state | 158 | User has not enabled memory |
| Persistent storage API overview | 162–170 | window.storage.get/set/delete/list |
| Key design pattern | 189 | Hierarchical keys under 200 chars |
| Batch related data | 191 | Avoid sequential calls |
| Personal vs shared data | 196, 199 | shared flag; inform users re: shared |
| Error handling | 202, 216 | try/catch; get() throws on non-existent keys |
| Storage limits | 225–229 | Text / JSON only, 5MB per key, rate limited |
| Two past-chats tools | 236 | conversation_search + recent_chats |
| Project scope | 238 | In project vs outside |
| Cue-based-matching canonical | 243 | Possessives, definite articles, past-tense, direct asks |
| Tool choice | 245 | Topic → search; temporal → recent_chats |
| Query construction | 247 | Content nouns, not meta-words |
| recent_chats mechanics | 249 | n ≤ 20, pagination cap ~5 |
| Boundary cases | 253–257 | Python project / that thing / France |

## Computer use (lines 260–513)

| Claim / concept | Lines | What's there |
|---|---|---|
| Skills overview | 262 | Folders with best practices |
| Multiple skills possible | 263 | Don't limit to one |
| Read SKILL.md first | 264 | Before any computer-tool action |
| Skill-reading examples | 268–275 | pptx / docx / docx+imagegen |
| File creation triggers | 281–287 | Specific phrases → file types |
| Category axis vs decoys | 289 | Standalone vs conversational; length / tone irrelevant |
| Over-creation avoidance | 295–299 | Five cases to NOT use tools |
| Modal user framing | 301 | Most users not developers |
| Restraint cases | 303–306 | Table / list / docx triggers to resist |
| Linux computer info | 310–318 | Ubuntu 24, tools, working dir |
| File locations | 322–336 | /uploads, /home/claude, /outputs |
| "Without this, users can't see" | 336 | Consequence for not moving to /outputs |
| Uploaded file types in context | 340–347 | md / txt / html / csv / png / pdf |
| Context vs disk decision | 350 | Model's discretion on when to use computer |
| Short vs long file strategy | 361–370 | 100-line threshold |
| Share files via present_files | 376 | Don't over-describe after sharing |
| Artifact use cases | 398–407 | 9 positive cases |
| Artifact non-use cases | 410–417 | 8 negative cases (negative space) |
| Single-file artifact default | 419 | No separate CSS / JS files |
| Renderable extensions | 423–428 | md / html / jsx / mermaid / svg / pdf |
| React library list | 448–465 | lucide-react, recharts, mathjs, lodash, d3, plotly, three.js, papaparse, sheetjs, shadcn/ui, chart.js, tone, mammoth, tensorflow |
| Browser storage ban | 468 | NEVER localStorage/sessionStorage in artifacts |
| Artifact tag hiding | 476 | Don't include artifact/antartifact tags in responses |
| Package management | 480–483 | npm, pip --break-system-packages, venvs if needed |
| Example decisions | 486–498 | Six request → routing examples |
| Skills reminder repeated | 500–512 | pptx / xlsx / docx / pdf / frontend-design triggers |
| User skills promiscuous use | 509 | User-provided skills trumped Anthropic's |

## Request routing (lines 515–584)

| Claim / concept | Lines | What's there |
|---|---|---|
| Checklist intro | 515 | Walk steps in order, first match |
| Step 0 — visual needed? | 518 | Mostly conversational |
| Step 1 — MCP tool fit? | 521 | Category match |
| Category match not style | 524 | No subdivision rationalization |
| Judgment retained | 526 | Safety doesn't suspend; injection defense |
| Step 2 — file ask? | 530 | "save as", filename, path |
| Step 3 — Visualizer default | 533 | No MCP, no file → Visualizer |
| Don't narrate routing | 536 | Claude selects and produces |
| Visualizer definition | 540 | SVG and HTML, inline |
| Explicit triggers | 542 | show me / visualize / diagram / etc. |
| Proactive triggers | 545 | Educational, data shape, architecture |
| Specification triggers | 551 | Noun phrase = spec |
| Multi-viz rule | 554 | Interleave with prose |
| Design guidance modules | 557 | diagram / mockup / interactive / chart / art |
| Never expose machinery | 560 | No "let me load" |
| Content safety for visuals | 563 | No violence / sexual / copyrighted / real people / misinfo |
| Six visualizer examples | 568–584 | Show me / diagram / fallback / water cycle / save to html / bubble sort |

## Search and copyright (lines 586–835)

| Claim / concept | Lines | What's there |
|---|---|---|
| Web search tool definition | 587 | Top 10 ranked results |
| Copyright hard limits preamble | 589–593 | 15 words, 1 per source, non-negotiable |
| Core search behaviors intro | 596 | Three principles |
| Don't-search list | 601–604 | Timeless / historical / dead / concepts |
| Do-search list | 606–614 | Current roles / policies / stock / specific products |
| Cutoff-mention avoidance | 616 | Don't mention real-time limit |
| Single search for simple | 618 | NBA finals example |
| Tool call scaling | 620 | 1 / 3–5 / 5–10 / 20+ |
| Best-tools priority | 622 | Internal > web > combined |
| Complex query tool combinations | 624 | 5–15 calls for hard questions |
| Short queries | 629 | 1–6 words |
| Broad to narrow | 630 | Start short, narrow if needed |
| Query distinctness | 631 | Each query must be distinct |
| No '-' or 'site:' | 633 | Unless asked |
| Date in queries | 634 | Use actual current year |
| web_fetch for full content | 635 | Snippets too brief |
| Results aren't user's | 636 | Don't thank |
| Privacy for image ID | 637 | No names in queries |
| Quote under 15 words | 640 | Severe violation if exceeded |
| One quote per source | 641 | Severe violation if exceeded |
| Keep responses succinct | 642 | No repetition |
| Cite impactful sources | 643 | Note conflicts |
| Most recent first | 644 | Past month for evolving topics |
| Primary sources preferred | 645 | Blogs / papers / gov / SEC |
| Politically neutral | 646 | Don't take sides |
| Don't narrate search use | 647 | Just search directly |
| User location context | 648 | Use naturally |
| Copyright non-negotiable | 657 | Precedence over user requests / helpfulness |
| Paraphrase always | 662 | Core philosophy |
| Never reproduce copyrighted | 663 | Assume anything from internet is |
| 15-word hard ceiling | 664 | 20/25/30+ are violations |
| Source closed after 1 quote | 665 | Global restriction |
| No stringing small quotes | 666 | "mesmerizing" + "once in a lifetime" = 2 quotes |
| No lyrics / poems / haikus | 667 | Brevity doesn't exempt |
| No fair-use determination | 668 | Claude isn't a lawyer |
| Displacive summary ban | 669 | Must be shorter, substantially reworded |
| No structural reconstruction | 670 | No mirrored section headers |
| No invented attributions | 671 | If unsure, omit |
| User insistence ignored | 672 | Regardless of requests |
| Passage requests refused | 673 | Brief high-level summary offered |
| Multi-source paraphrase | 674 | 5+ sources → almost entirely paraphrase |
| Hard limit 1 | 680 | 15 words |
| Hard limit 2 | 685 | 1 quote per source |
| Hard limit 3 | 690 | Never reproduce lyrics / poems / haikus |
| Self-check canonical | 698–707 | 7 questions before emitting |
| CEO testimony example | 713–720 | 8-word quote correct because legal significance |
| Addison Rae song example | 723–728 | Recognize copyright; offer original |
| Let It Go example | 733–737 | Refuse; offer original ice princess poem |
| NYT paraphrase example | 741–748 | Full paraphrase, no quotes |
| Copyright harms stated | 755–759 | Creators / legal risk / policies |
| Q3 sales example | 767–774 | Internal tool first |
| S&P 500 example | 778–783 | Current price search |
| California Sec State | 787–792 | Current role-holder search |
| Fed rates example | 797–802 | Paraphrase-only reporting |
| Harmful content safety | 808–815 | Never search / reference / cite hate sources |
| Harmful categories list | 812 | Sexual / CSAM / illegal / violence / jailbreaks / self-harm / election fraud / etc. |
| Overrides user instructions | 815 | Always apply |
| Critical copyright reminder | 819 | 15+ / 1 per source / default paraphrase |
| No lyrics / poems / paragraphs | 820 | Absolute |
| Not a lawyer | 821 | No fair-use determinations |
| Harmful-content refusal | 822 | Follow harmful_content_safety |
| Location natural tone | 823 | Use for location-related queries |
| Complex query planning | 824 | Research plan first |
| Rate-of-change heuristic | 825 | Search fast-changing topics |
| URL in query → web_fetch | 826 | Always fetch exact URL |
| Avoid over-search on stable | 827 | Unless present-day state |
| Every query → substantive response | 828 | No pure "I can search" offers |
| Believe surprising results | 829 | Except conspiracies / pseudoscience / SEO |
| Multiple searches for conflicts | 830 | Get clear answer |
| Epistemic humility goal | 831 | True + useful |
| Search fast-changing AND unknown | 832 | Both trigger search |
| Search regardless of confidence | 833 | For present-day facts |

## Image search (lines 837–904)

| Claim / concept | Lines | What's there |
|---|---|---|
| Core principle | 840 | Would images enhance? |
| Positive cases | 846 | Places, animals, food, etc. |
| Negative cases | 849 | Text output, numbers, code, math, etc. |
| Blocked categories | 856–866 | Harm / eating disorders / gore / IP / celebrities / artworks / sexual |
| Museum art carve-out | 865 | Art in larger display context allowed |
| Query length | 871 | 3–6 words with context |
| Result count | 872 | Min 3, max 4 |
| Placement rules | 873 | Interleave vs lead vs support |
| Shopping — always interleave | 876 | Front-loading looks like ads |
| Continue after image | 877 | Don't end on image search |
| Tokyo example | 885 | Interleaved with destinations |
| Pangolin example | 888 | Image-as-answer, lead |
| Photosynthesis example | 892 | Single supporting diagram |
| Living room example | 896 | Interleaved style references |
| Datadog example | 900 | Negative case — no image |

## Rest of file

| Section | Lines | Notes |
|---|---|---|
| Function definitions | 906–961 | 20 tools listed with JSONSchema |
| Anthropic API in artifacts | 970–1240 | How to call the API from artifacts |
| Citation format | 1243–1260 | {cite} tag syntax |
| Copyright-in-citations rule | 1254 | Tags are attribution, not quotation permission |
| Skills list | 1264–1372 | 10 skills with descriptions and locations |
| Network config | 1374–1380 | Domain whitelist |
| Filesystem config | 1382–1391 | Read-only mounts |
| Thinking mode | 1393 | auto |
| Thinking block preference | 1395–1408 | Strong preference on uncertainty |

## How to verify

For each claim in this repo, the line reference points to the exact location in `source/opus-4.7.txt`. To verify:

```
grep -n "<keyword>" source/opus-4.7.txt
```

or view a range:

```
sed -n '515,537p' source/opus-4.7.txt
```

If a claim in this repo doesn't match the source, open an issue — it's a bug.
