#!/usr/bin/env python3
"""
opus-mind boost.py — for everyday prompters.

    boost ≠ lint.

LINT (`audit.py`) is for BUILDERS writing production agent prompts
(CLAUDE.md, SKILL.md, .cursorrules, chatbot system prompts). Its
invariants target rule conflicts, refusal design, policy tiers,
consequence statements — layers the LLM runtime sits on top of.

BOOST (`boost.py`) is for USERS writing chat messages or task
prompts. It has two layers of slots:

SPECIFICATION layer (what Claude should produce) — grounded in
Anthropic's public prompt-engineering docs:

    B1 task         — imperative verb + object, what to produce
    B2 format       — output shape (JSON / markdown / bullets / prose)
    B3 length       — numeric constraint on size
    B4 context      — audience, background, domain setup
    B5 few_shot     — one or more examples of the desired output
    B6 constraints  — tone, style, avoid-list
    B7 clarify      — policy for ambiguity (ask vs assume)

REASONING layer (how Claude should think) — grounded in public
prompt-engineering research (see `evidence/smart-prompting-refs.md`):

    B8  reasoning     — ask for step-by-step / outline-first thinking
    B9  verification  — ask Claude to check its own answer, flag uncertainty
    B10 decomposition — ask for plan-before-execute / break into subtasks

Safety and refusal policy are NOT in scope here — the system prompt
running Claude already handles those (that's LINT's job).

Subcommands:
    boost check   <prompt_or_path>   slot coverage, actionable
    boost ask     <prompt_or_path>   emit the questions to fill slots
    boost expand  <prompt_or_path>   emit the composition prompt for the
                                      current LLM (Claude Code's Claude,
                                      or any LLM the CLI user pastes into)

Architecture:
    All three subcommands are deterministic — regex, slot detection, string
    templates. No API calls. When `expand` emits a composition prompt, the
    LLM synthesis is performed by the surrounding runtime — typically the
    Claude Code session that invoked this skill. Outside Claude Code, users
    paste the emitted prompt into any LLM of choice.

Usage:
    opus-mind boost check "write a blog post about AI safety"
    opus-mind boost check prompt.txt
    opus-mind boost ask - < prompt.txt
    opus-mind boost expand prompt.txt --answers answers.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Slot detectors. Structural where possible; minimal vocabulary where not.
# ---------------------------------------------------------------------------

# B1 — task intent. A prompt opens with an imperative verb + object pattern.
# This is the one slot that needs a small verb list — imperative mood is
# grammatical, not lexical, and a full parser is overkill. We keep the list
# tight and common-task-oriented.
TASK_VERBS = [
    "write", "create", "make", "build", "design", "draft", "compose",
    "generate", "produce", "render", "change", "update", "modify",
    "analyze", "review", "audit", "evaluate", "assess", "critique",
    "explain", "describe", "summarize", "outline", "list", "compare",
    "translate", "rewrite", "refactor", "rename", "convert",
    "find", "search", "extract", "identify", "classify",
    "fix", "debug", "solve", "improve", "optimize",
    "plan", "schedule", "organize", "structure",
    "help", "suggest", "recommend", "propose", "diagnose",
    "show", "visualize", "illustrate", "graph", "chart",
]
TASK_VERB_RE = re.compile(
    r"(?:^|[.?!]\s+)(?:please\s+|can you\s+|could you\s+|would you\s+)?"
    r"\b(?:" + "|".join(TASK_VERBS) + r")\b\s+\w+",
    re.IGNORECASE | re.MULTILINE,
)

# B2 — output format. Structural: format nouns or markup mentions.
FORMAT_SIGNALS = [
    r"\bjson\b", r"\byaml\b", r"\btoml\b", r"\bxml\b", r"\bcsv\b",
    r"\bmarkdown\b", r"\bmd\b", r"\bhtml\b", r"\btable\b",
    r"\bbullet[s]?\b", r"\bnumbered list\b", r"\bcheck ?list\b",
    r"\bprose\b", r"\bparagraph[s]?\b", r"\bheadings?\b",
    r"\bcode ?block\b", r"\bdiff\b", r"\bpseudocode\b",
    r"\bas an? (?:list|table|bullet|heading)",
    r"\brespond (?:as|in|with) [a-z]",
    r"\bformat\s*:", r"\boutput\s*:", r"\bstructure\s*:",
]

# B3 — length / scope. Reuse audit.py NUMBER_CONSTRAINT plus prompt-y nouns
# (words, sentences, paragraphs, bullets, examples).
LENGTH_RE = re.compile(
    # "800 words", "800-word", "800 word"
    r"\b\d+(?:\s*[-–—]\s*\d+)?\s*[-–—]?\s*"
    r"(?:word|token|char|character|line|sentence|paragraph|bullet|"
    r"item|example|section|heading|row|step|point|tip)s?\b"
    r"|\bunder\s+\d+\s*(?:words?|tokens?|chars?|minutes?|seconds?)\b"
    r"|\b(?:≤|<=|at most|max(?:imum)?)\s+\d+\s*\w+"
    r"|\b(?:≥|>=|at least|min(?:imum)?)\s+\d+\s*\w+"
    r"|\b\d+\s*min(?:ute)?\s+read\b",
    re.IGNORECASE,
)

# B4 — context. Audience / domain / background.
CONTEXT_SIGNALS = [
    # "for <any adj/noun> (audience|engineers|devs|users|team|...)"
    r"\bfor\s+(?:a|an|our|my|the)?[\s\w/-]{0,60}?"
    r"(?:audience|reader|readers|user|users|team|dev|devs|developer|developers|"
    r"analyst|analysts|engineer|engineers|writer|writers|student|students|"
    r"beginner|beginners|expert|experts|specialist|specialists|customer|customers|"
    r"PM|PMs|manager|managers|researcher|researchers|doctor|doctors|patient|patients)\b",
    r"\b(?:audience|target|context|background)\s*:",
    r"\btarget(?:ed)?\s+(?:at|for|audience)",
    r"\bassum(?:e|ing)\s+(?:the reader|they|we|you)\s+(?:know|have|are|can)",
    r"\bgiven that\b", r"\bgiven the\b",
    r"\bfor (?:people|users|readers|devs|engineers|someone|anyone) who\b",
    r"\bI am\b", r"\bI'm\s+(?:a|an|the|working|trying|building)",
    r"\bwe are\b", r"\bour (?:team|company|product|users|customers|codebase)\b",
    r"\b(?:beginner|intermediate|advanced|expert)[- ]level\b",
    r"\bwho\s+(?:aren'?t|don'?t know|never|haven'?t|are new)\b",
    r"\bnot\s+(?:alignment|ML|technical|domain)\s+\w+",
    # Role / persona framing — classic context anchor.
    r"\bYou are (?:an?|the) [A-Za-z]",
    r"\bAct as (?:an?|the) [A-Za-z]",
    r"\bYour (?:task|job|role) is\b",
    r"\bhelp (?:doctors?|users?|engineers?|analysts?|writers?|students?|customers?|teams?|PMs?)",
    # Document / data context via XML structure (multi-doc prompting).
    r"<documents?>", r"<context>", r"<background>", r"<setup>",
    # Explicit scope setting.
    r"\b(?:in the context of|given the following|based on (?:the|this))\b",
]

# B5 — few-shot / example. Structural: example markers, quoted samples.
FEWSHOT_SIGNALS = [
    r"(?:^|\n)\s*(?:example|사례|예시)\s*\d*\s*[:\n]",
    r"\bexample\s+(?:style|prompt|output|response|input|format)\s*:",
    r"(?:^|\n)\s*(?:like this|for instance|e\.g\.|such as)\b",
    r"(?:^|\n)\s*>\s+\w",                         # markdown quote block
    r"(?:^|\n)```[^\n]*\n",                       # fenced code block
    r"\binput\s*:[^\n]+\n.*?\boutput\s*:",        # input/output pair
    r"\bhere'?s?\s+(?:an? )?example\b",
    r"\bhere is (?:an? )?example\b",
    r"\bformat (?:it )?like\b",
    r"\bmatch(?:ing)? (?:the )?(?:style|tone|voice) of\b",
    r"\bmatch(?:ing)? \w+[- ]style\b",
    r"\bin the style of\b",
    r"\b(?:sample|reference|example) (?:post|article|code|essay|response|format)\b",
    # XML-tagged examples — Anthropic's recommended few-shot pattern.
    r"<example[ s>/]", r"</example[s]?>",
]

# B6 — constraints. Tone / avoid / style / limits beyond length.
CONSTRAINT_SIGNALS = [
    r"\btone\s*:", r"\bstyle\s*:", r"\bvoice\s*:",
    r"\b(?:avoid|don't|do not|no|without|never)\s+(?:use|include|mention|say)\b",
    r"\b(?:keep it|make it|be)\s+(?:concise|brief|formal|casual|playful|dry|direct|warm|cold)",
    r"\bno jargon\b", r"\bno buzzwords\b", r"\bno filler\b",
    r"\bno preamble\b", r"\bwithout preamble\b",
    r"\b(?:formal|casual|conversational|academic|technical|friendly)\s+(?:tone|voice|style|register)",
    r"\bavoid (?:using |mentioning |the word )",
    r"\b(?:plain english|simple language|accessible language)\b",
    # "show only X", "respond directly", "skip non-essential"
    r"\bshow only\b", r"\brespond directly\b", r"\bskip (?:non[- ]essential|the)\b",
    r"\bnever use\b",
    r"\bpreserve (?:all|the) existing",
]

# B7 — ambiguity / clarification policy.
CLARIFY_SIGNALS = [
    r"\bif (?:unclear|ambiguous|uncertain|you don'?t know|you'?re not sure)\b",
    r"\bwhen (?:in doubt|unclear|ambiguous)\b",
    # \s+ (not literal space) lets patterns span newline-wrapped text.
    r"\bask\s+(?:me|first|for clarification|if|one specific|before)\b",
    r"\bassume\s+(?:that|the|I|we)\b",
    r"\bdefault to\b", r"\buse your best judg?ment\b",
    r"\bflag\s+(?:any|it|anything|them|which|assumption)\b",
    r"\bdon'?t\s+(?:invent|make up|guess|fabricate)\b",
    # "If records / docs / context are inconsistent" — Anthropic doc-loading pattern.
    r"\bif\s+(?:records|docs|the input|context|the records|the docs)\s+(?:are|is)\s*(?:inconsistent|incomplete|unclear|missing)\b",
]

# ---------------------------------------------------------------------------
# Reasoning-quality slots (B8-B10). These target "how should Claude think",
# not "what does Claude produce". Grounding lives in a separate evidence
# file (evidence/smart-prompting-refs.md) because the source is public
# prompt-engineering research, not the Opus 4.7 system prompt.
# ---------------------------------------------------------------------------

# B8 — Reasoning request. Explicit ask for chain-of-thought or plan-first.
# Evidence: Wei et al. 2022 "Chain-of-Thought Prompting Elicits Reasoning
# in Large Language Models"; Anthropic "Let Claude think" docs page.
REASONING_SIGNALS = [
    r"\bthink (?:step by step|step-by-step|carefully|through this)\b",
    r"\blet'?s think\b",
    r"\bshow (?:your|the) (?:work|reasoning|thinking|steps)\b",
    r"\bexplain (?:your|the) (?:reasoning|thinking|thought process|rationale)\b",
    r"\breason (?:through|about|over) this\b",
    r"\bwalk (?:me )?through (?:your|the) (?:reasoning|thinking|steps)\b",
    r"\bbefore (?:answering|responding|writing|drafting)[^.]{0,40}\b(?:think|plan|outline|consider|reflect)\b",
    r"\b(?:outline|plan|sketch)\s+(?:first|before|your approach|the approach|the steps)\b",
    r"\b<thinking>\s*\.?\.?\.?\s*</thinking>?",    # Anthropic-idiomatic thinking tag
    r"\bshow (?:your|the) (?:scratchpad|chain[- ]of[- ]thought)\b",
    r"\bwrite (?:out|down) (?:your|the) (?:reasoning|thought|plan)\b",
    r"\bconsider (?:each|every|all|the following)\s+\w+\s+(?:one by one|in turn|separately)\b",
]

# B9 — Verification / self-check request. Asking the model to check its own
# output before or after emitting. Evidence: Shinn et al. 2023 (Reflexion);
# Wang et al. 2022 (self-consistency); Anthropic docs "Prefill Claude's
# response" and prompt-engineering best-practices page.
VERIFICATION_SIGNALS = [
    r"\b(?:verify|double[- ]check|check|validate|audit)\s+(?:your|each|every|all|the)\s+\w+",
    r"\bafter (?:writing|drafting|answering|producing)[^.]{0,60}\b(?:review|check|verify|critique|audit)\b",
    r"\b(?:critique|review)\s+(?:your own|your|the) (?:answer|output|response|draft)\b",
    r"\brate (?:your|the) (?:confidence|certainty)\b",
    r"\b(?:confidence|certainty)\s*(?:score|level|:)\s*(?:\d+|low|medium|high)",
    r"\bflag\s+(?:uncertain|unverified|speculative|low[- ]confidence)\s*(?:claims?|facts?|statements?)?\b",
    r"\bmark\s+(?:uncertain|unverified|speculative)\s*(?:claims?|facts?|parts?|sections?)?\b",
    r"\bif\s+(?:any|some|a)\s+(?:claim|fact|step)\s+(?:is|seems)\s+(?:uncertain|unverified|wrong)\b",
    r"\bthen\s+(?:revise|rewrite|fix|correct|iterate)\b",
    r"\bself[- ]check\b",
    r"\bsanity[- ]check\b",
    r"\bbefore (?:emitting|sending|finalizing|returning)[^.]{0,40}\b(?:check|verify|confirm)\b",
]

# B10 — Decomposition request. Breaking the task into smaller pieces, or
# asking for an explicit plan before execution. Evidence: Zhou et al. 2022
# "Least-to-most prompting"; Anthropic "Break complex tasks into steps"
# docs page; Yao et al. 2023 (ReAct: reasoning + acting interleaved).
DECOMPOSITION_SIGNALS = [
    # Explicit decomposition vocabulary — user directly asks the model to
    # split the task. "First X, then Y" (imperative sequencing) is NOT
    # decomposition; removed the generic first/then chain to cut false
    # positives on normal instruction lists.
    r"\bbreak\s+(?:this|it|the (?:problem|task))\s+(?:down|into|up)\b",
    r"\bdecompose\s+(?:this|it|the)\b",
    # Numbered structure with punctuation — user defining explicit phases.
    # "Step 1:" counts; bare "step 1" in prose does not.
    r"\b(?:phase|stage|step)\s*\d+\s*[:\-\u2014]",
    r"\bsubtasks?\b",
    r"\b(?:sub[- ]?steps?|sub[- ]?problems?|sub[- ]?goals?)\b",
    # Plan-before-execute meta-instruction.
    r"\b(?:make|write|produce|create|give me)\s+(?:a|an)\s+(?:plan|outline|roadmap|todo|checklist)\s+(?:first|before)\b",
    r"\bplan[- ]?and[- ]?(?:solve|execute|act)\b",
    r"\bleast[- ]to[- ]most\b",
    r"\bbefore (?:implementing|writing|coding|drafting)[^.]{0,40}\b(?:plan|outline|design|list)\b",
    r"\bfirst (?:outline|plan|sketch|draft a plan|produce a plan|list the (?:steps|sub[- ]?steps))\b",
    # Iteration ONLY when paired with meta-vocabulary, not arbitrary nouns.
    # "for each section" is meta; "for each worker" is not.
    r"\bfor each (?:of the|item|step|subtask|sub[- ]step|section|phase|part)\b",
    r"\benumerate (?:the|each|every|all)\s+(?:steps?|phases?|sub[- ]?tasks?|sub[- ]?problems?|sections?|parts?)\b",
]

SLOT_NAMES = [
    "B1", "B2", "B3", "B4", "B5", "B6", "B7",
    "B8", "B9", "B10",
]
SLOT_LABELS = {
    "B1":  "task",
    "B2":  "format",
    "B3":  "length",
    "B4":  "context",
    "B5":  "few_shot",
    "B6":  "constraints",
    "B7":  "clarify",
    "B8":  "reasoning",
    "B9":  "verification",
    "B10": "decomposition",
}


# ---------------------------------------------------------------------------
# Task-type inference. Drives dynamic slot ranking in the skill: a code
# task needs B10 (decomposition) earlier than an essay needs B10; an
# analytical task needs B8/B9 earlier than a short rewrite needs either.
# ---------------------------------------------------------------------------

TASK_TYPE_SIGNALS: dict[str, list[str]] = {
    # Code / engineering — precision + decomposition critical.
    "code": [
        r"\b(?:write|implement|generate|refactor|fix|debug|build)\s+(?:a|an|the|some)?\s*(?:function|class|module|script|program|test|api|endpoint|component|hook|agent|bot)\b",
        r"\b(?:python|javascript|typescript|rust|go|java|c\+\+|c#|bash|sql|shell)\b",
        r"\b(?:regex|algorithm|data structure|compiler|parser)\b",
        r"\bcode\s+(?:review|snippet|block)\b",
        r"\b(?:refactor|optimize)\s+(?:this|the)?\s*(?:code|function|loop)\b",
    ],
    # Analytical — reasoning + verification critical.
    "analyze": [
        r"\b(?:analyze|analyse|evaluate|assess|investigate|diagnose|audit)\b",
        r"\b(?:what (?:is|are) the (?:root cause|causes|reasons|implications))\b",
        r"\b(?:compare|contrast)\s+\w+\s+(?:to|vs|against|with)\b",
        r"\b(?:pros and cons|tradeoffs?|trade[- ]offs?)\b",
        r"\b(?:identify|find)\s+(?:the )?(?:patterns|issues|gaps|risks)\b",
    ],
    # Research — verification + citation critical.
    "research": [
        r"\bresearch\b",
        r"\bfind (?:sources|papers|studies|citations)\b",
        r"\b(?:summarize|synthesize) (?:the|recent|relevant) (?:literature|papers|research)\b",
        r"\bliterature review\b",
    ],
    # Creative writing — constraints + audience critical, reasoning less so.
    # `\w+\s+` allows intervening adjectives ("write a conversational blog").
    "write": [
        r"\bwrite\s+(?:a|an)?\s*(?:\w+\s+){0,3}(?:blog|essay|post|article|story|poem|script|newsletter|letter|email|tweet|thread|intro|outro|summary)\b",
        r"\bdraft\s+(?:a|an)?\s*(?:\w+\s+){0,3}(?:reply|response|pitch|proposal|announcement|intro|outro|post|article|message)\b",
        r"\bcompose\s+(?:a|an)?\s*(?:\w+\s+){0,3}(?:message|note|caption|reply|tweet|post)\b",
        r"\bsummari[sz]e (?:this|the|these|that)\b",
    ],
    # Short / one-off — heavy reasoning is overkill.
    "short": [
        r"\b(?:rename|translate|convert|reformat|rewrite)\s+(?:this|the|it)\b",
        r"\bone[- ]liner\b",
        r"\bfix (?:this|the) typo\b",
        r"^\s*[A-Z][^.!?]{0,80}[.!?]?\s*$",        # very short prompts
    ],
}


def detect_task_type(text: str) -> str:
    """Return one of: code, analyze, research, write, short, unknown.

    The result drives dynamic slot-impact ranking in SKILL.md Flow B —
    the skill asks B10/B8 earlier for code/analysis tasks, B4/B6 earlier
    for creative writing, etc. Not a strict classification; a heuristic
    for prioritising which empty slot to ask about first.
    """
    scores: dict[str, int] = {}
    lowered = text.lower()
    for kind, patterns in TASK_TYPE_SIGNALS.items():
        score = 0
        for pat in patterns:
            hits = len(re.findall(pat, lowered, re.MULTILINE))
            score += hits
        if score:
            scores[kind] = score
    if not scores:
        # Short prompts (< 15 words) default to "short" even if none of
        # the explicit patterns matched — length itself is the signal.
        if len(text.split()) < 15:
            return "short"
        return "unknown"
    return max(scores.items(), key=lambda kv: kv[1])[0]


# Impact ranking per task type. SKILL.md Flow B Phase 2 uses the task
# type to pick the highest-impact EMPTY slot to ask about first. For
# each type, slots are listed in order of impact — earlier = ask sooner.
# Slots not listed fall to the end in default numeric order.
SLOT_IMPACT_BY_TASK: dict[str, list[str]] = {
    # Code: decomposition + verification dominate; length + format matter;
    # few-shot (example of desired output) lifts accuracy most.
    "code":     ["B10", "B8",  "B9",  "B2",  "B5",  "B3",  "B6",  "B4",  "B7", "B1"],
    # Analyze: reasoning + verification first; context (what's the corpus)
    # and format (table/summary/bullets) next.
    "analyze":  ["B8",  "B9",  "B4",  "B2",  "B10", "B3",  "B6",  "B5",  "B7", "B1"],
    # Research: verification is paramount; then reasoning, context,
    # length, decomposition.
    "research": ["B9",  "B8",  "B4",  "B3",  "B10", "B2",  "B6",  "B5",  "B7", "B1"],
    # Creative writing: audience + constraints + length drive the feel;
    # reasoning helps long pieces, verification for factual claims only.
    "write":    ["B4",  "B6",  "B3",  "B2",  "B5",  "B10", "B8",  "B9",  "B7", "B1"],
    # Short one-offs: skip the reasoning layer entirely; format + length
    # are usually all that's missing.
    "short":    ["B2",  "B3",  "B6",  "B4",  "B7",  "B5",  "B1",  "B8",  "B9", "B10"],
    # Unknown: the original default — specification-heavy, reasoning last.
    "unknown":  ["B3",  "B4",  "B2",  "B6",  "B8",  "B9",  "B10", "B5",  "B7", "B1"],
}


def rank_slots_by_impact(task_type: str) -> list[str]:
    """Return SLOT_NAMES ordered by impact for the given task type."""
    ordered = SLOT_IMPACT_BY_TASK.get(task_type, SLOT_IMPACT_BY_TASK["unknown"])
    # Guarantee every slot appears exactly once.
    seen = set(ordered)
    tail = [s for s in SLOT_NAMES if s not in seen]
    return ordered + tail


@dataclass
class SlotHit:
    slot: str
    filled: bool
    evidence: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class BoostReport:
    source: str
    text: str
    slots: dict[str, SlotHit] = field(default_factory=dict)
    task_type: str = "unknown"
    impact_order: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> str:
        filled = sum(1 for s in self.slots.values() if s.filled)
        return f"{filled}/{len(self.slots)}"

    @property
    def filled_count(self) -> int:
        return sum(1 for s in self.slots.values() if s.filled)


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if m:
            return m.group(0)[:80]
    return None


def _any_match(text: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            snippet = m.group(0).strip()[:80]
            if snippet and snippet not in hits:
                hits.append(snippet)
    return hits


def check(text: str, source_label: str = "<prompt>") -> BoostReport:
    r = BoostReport(source=source_label, text=text)

    # B1 task — imperative verb + object on an opening sentence.
    task_hit = TASK_VERB_RE.search(text)
    r.slots["B1"] = SlotHit(
        slot="B1",
        filled=bool(task_hit),
        evidence=[task_hit.group(0).strip()] if task_hit else [],
        suggestions=(
            []
            if task_hit
            else [
                "start with an imperative verb: write / analyze / explain / build / ...",
                "state the object: ... a 500-word blog post / a Python function / a comparison table",
            ]
        ),
    )

    # B2 format.
    fmt_hits = _any_match(text, FORMAT_SIGNALS)
    r.slots["B2"] = SlotHit(
        slot="B2",
        filled=bool(fmt_hits),
        evidence=fmt_hits[:2],
        suggestions=(
            []
            if fmt_hits
            else [
                "name the output shape: JSON / markdown / table / bullets / prose",
                'example: "respond as a markdown table with columns X, Y, Z"',
            ]
        ),
    )

    # B3 length.
    length_hits = [m.group(0).strip() for m in LENGTH_RE.finditer(text)][:3]
    r.slots["B3"] = SlotHit(
        slot="B3",
        filled=bool(length_hits),
        evidence=length_hits[:2],
        suggestions=(
            []
            if length_hits
            else [
                "add a numeric budget: 300 words / 5 bullets / 3 paragraphs / under 200 tokens",
                "vague words like 'short', 'detailed', 'comprehensive' will drift",
            ]
        ),
    )

    # B4 context.
    ctx_hits = _any_match(text, CONTEXT_SIGNALS)
    r.slots["B4"] = SlotHit(
        slot="B4",
        filled=bool(ctx_hits),
        evidence=ctx_hits[:2],
        suggestions=(
            []
            if ctx_hits
            else [
                "who reads this? e.g. 'for ML engineers', 'for a non-technical PM'",
                'what can the reader be assumed to know? e.g. "assume they know Python basics"',
            ]
        ),
    )

    # B5 few-shot.
    shot_hits = _any_match(text, FEWSHOT_SIGNALS)
    r.slots["B5"] = SlotHit(
        slot="B5",
        filled=bool(shot_hits),
        evidence=shot_hits[:1],
        suggestions=(
            []
            if shot_hits
            else [
                "show one example of the output you want — a real sentence, not a description",
                "for complex tasks, one good example beats a page of adjectives",
            ]
        ),
    )

    # B6 constraints (beyond length).
    cons_hits = _any_match(text, CONSTRAINT_SIGNALS)
    r.slots["B6"] = SlotHit(
        slot="B6",
        filled=bool(cons_hits),
        evidence=cons_hits[:2],
        suggestions=(
            []
            if cons_hits
            else [
                'state tone: "conversational / academic / skeptical / warm / terse"',
                'state avoid-list: "no jargon", "no buzzwords", "no corporate hedging"',
            ]
        ),
    )

    # B7 clarify.
    clr_hits = _any_match(text, CLARIFY_SIGNALS)
    r.slots["B7"] = SlotHit(
        slot="B7",
        filled=bool(clr_hits),
        evidence=clr_hits[:1],
        suggestions=(
            []
            if clr_hits
            else [
                'decide once: "if ambiguous, ask me" vs "assume X and flag it"',
                "saves you the back-and-forth or a confidently-wrong first answer",
            ]
        ),
    )

    # B8 reasoning — explicit chain-of-thought / plan-first request.
    reason_hits = _any_match(text, REASONING_SIGNALS)
    r.slots["B8"] = SlotHit(
        slot="B8",
        filled=bool(reason_hits),
        evidence=reason_hits[:1],
        suggestions=(
            []
            if reason_hits
            else [
                'ask Claude to think step by step before answering',
                'e.g. "Think step by step, outline first, then draft"',
                'Wei et al. 2022 (Chain-of-Thought) — accuracy lift on reasoning tasks',
            ]
        ),
    )

    # B9 verification — ask for self-check or critique-then-revise.
    verify_hits = _any_match(text, VERIFICATION_SIGNALS)
    r.slots["B9"] = SlotHit(
        slot="B9",
        filled=bool(verify_hits),
        evidence=verify_hits[:1],
        suggestions=(
            []
            if verify_hits
            else [
                "ask Claude to check its own answer before emitting",
                'e.g. "After drafting, verify each claim. Flag any that are uncertain."',
                "Shinn 2023 (Reflexion) — self-critique loop cuts hallucination",
            ]
        ),
    )

    # B10 decomposition — break-into-subtasks / plan-before-execute.
    decomp_hits = _any_match(text, DECOMPOSITION_SIGNALS)
    r.slots["B10"] = SlotHit(
        slot="B10",
        filled=bool(decomp_hits),
        evidence=decomp_hits[:1],
        suggestions=(
            []
            if decomp_hits
            else [
                "for multi-step work, ask for a plan before the execution",
                'e.g. "First outline the 3 sections, then draft each."',
                "Zhou 2022 (Least-to-most) — decomposition lifts long-horizon tasks",
            ]
        ),
    )

    # Task-type inference → dynamic impact ranking. Used by the skill to
    # decide which empty slot to ask about first: code prompts surface
    # B10 (decomposition) early, essays surface B4 (audience) early, etc.
    r.task_type = detect_task_type(text)
    r.impact_order = rank_slots_by_impact(r.task_type)

    return r


# ---------------------------------------------------------------------------
# ask — emit the questions needed to fill empty slots.
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES = {
    "B1": "what should Claude produce? (verb + object, e.g. 'write a 500-word summary')",
    "B2": "what output format? (JSON / markdown / table / bullets / prose)",
    "B3": "what length or scope? (e.g. 300 words / 5 bullets / 3 paragraphs / under 200 tokens)",
    "B4": "who reads this, and what can they be assumed to know?",
    "B5": "can you paste one concrete example of what you want?",
    "B6": "what tone, and what should Claude avoid? (e.g. 'conversational, no jargon')",
    "B7": "on ambiguity: ask you, or assume-and-flag?",
    "B8": "should Claude think step-by-step / outline before writing? (yes/no — raises accuracy on complex work)",
    "B9": "should Claude verify its own answer before emitting? (yes/no — cuts hallucination)",
    "B10": "should Claude break this into sub-steps / produce a plan first? (yes/no — helps long tasks stay coherent)",
}


def ask(report: BoostReport) -> list[dict]:
    """Emit empty-slot questions in impact order for the inferred task type.

    Code tasks surface B10/B8 first; creative writing surfaces B4/B6
    first; short one-offs skip the reasoning layer to the end. The skill
    reads the first entry and asks that single question; on answer it
    refreshes and re-reads the head of the list.
    """
    order = report.impact_order or SLOT_NAMES
    out = []
    for slot in order:
        s = report.slots.get(slot)
        if s is None or s.filled:
            continue
        out.append({
            "slot": slot,
            "label": SLOT_LABELS[slot],
            "question": QUESTION_TEMPLATES[slot],
            "hints": s.suggestions,
            "impact_rank": order.index(slot) + 1,
        })
    return out


# ---------------------------------------------------------------------------
# expand — build the composition prompt for the surrounding LLM runtime.
# Emits prompt text only; never calls an API. In a Claude Code session the
# invoking Claude applies it in-chat. Outside, paste into any LLM.
# ---------------------------------------------------------------------------

EXPAND_TEMPLATE = """You are helping a user rewrite a vague prompt into a concrete one.

The user's original prompt was:
<<<
{original}
>>>

They have provided answers to the missing slots:
{answers_block}

Slot semantics:
- B1 task / B2 format / B3 length / B4 context / B5 few_shot / B6 constraints / B7 clarify
  — the "specification" layer: what Claude should produce and for whom.
- B8 reasoning / B9 verification / B10 decomposition
  — the "reasoning" layer: how Claude should think through the work.
  Fold these in as explicit directives at the END of the prompt:
    * B8 yes → append "Think step by step / outline before writing."
    * B9 yes → append "After drafting, verify each claim; flag uncertain ones."
    * B10 yes → append "First produce a plan / outline, then execute it."

Rewrite the prompt as a single, concrete, self-contained instruction
that an assistant (Claude / ChatGPT / Cursor) can act on in one pass.

Rules for your rewrite:
- Preserve the user's original intent exactly.
- Fold each provided answer into the instruction; do not add slots the
  user did not answer.
- Open with an imperative verb + object. No preamble, no apology.
- No "you are a ..." roleplay framing unless the user explicitly asked.
- No hedging: prefer specific numbers and names over adjectives.
- Put reasoning/verification/decomposition directives as separate
  short sentences at the end — do not blend them into the task line.
- Return ONLY the rewritten prompt text. No explanation, no markdown
  fence, no commentary.
"""


def build_expand_prompt(original: str, answers: dict[str, str]) -> str:
    lines = []
    for slot in SLOT_NAMES:
        if slot in answers and answers[slot]:
            lines.append(f"- {SLOT_LABELS[slot]}: {answers[slot]}")
    block = "\n".join(lines) if lines else "(no answers provided)"
    return EXPAND_TEMPLATE.format(original=original.strip(), answers_block=block)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _format_check_human(r: BoostReport) -> str:
    out = []
    out.append(f"source: {r.source}")
    out.append(f"coverage: {r.coverage}")
    out.append("")
    out.append("filled slots:")
    any_filled = False
    for slot in SLOT_NAMES:
        s = r.slots[slot]
        if s.filled:
            any_filled = True
            evidence = f" — {s.evidence[0]!r}" if s.evidence else ""
            out.append(f"  [✓] {slot} {SLOT_LABELS[slot]}{evidence}")
    if not any_filled:
        out.append("  (none)")
    out.append("")
    out.append("empty slots — missing spec:")
    any_empty = False
    for slot in SLOT_NAMES:
        s = r.slots[slot]
        if not s.filled:
            any_empty = True
            out.append(f"  [ ] {slot} {SLOT_LABELS[slot]}")
            for hint in s.suggestions:
                out.append(f"         · {hint}")
    if not any_empty:
        out.append("  (none — prompt is specified)")
    out.append("")
    if r.filled_count < 7:
        out.append("next:")
        out.append("  opus-mind boost ask    <this prompt>    # get the exact questions")
        out.append("  opus-mind boost expand <this prompt>    # generate the concrete prompt")
    return "\n".join(out)


def _format_check_json(r: BoostReport) -> str:
    payload = {
        "source": r.source,
        "coverage": r.coverage,
        "filled_count": r.filled_count,
        "task_type": r.task_type,
        "impact_order": r.impact_order,
        "slots": {
            slot: {
                "label": SLOT_LABELS[slot],
                "filled": r.slots[slot].filled,
                "evidence": r.slots[slot].evidence,
                "suggestions": r.slots[slot].suggestions,
            }
            for slot in SLOT_NAMES
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _read_input(path_or_text: str) -> tuple[str, str]:
    """Return (text, source_label). Treat as file if it looks like a path."""
    if path_or_text == "-":
        return sys.stdin.read(), "<stdin>"
    p = Path(path_or_text)
    if p.exists() and p.is_file():
        try:
            return p.read_text(encoding="utf-8"), str(p)
        except UnicodeDecodeError:
            raise SystemExit(f"error: {p} is not valid UTF-8")
    # Treat as literal prompt text.
    return path_or_text, "<inline>"


def _cmd_check(args) -> int:
    text, source = _read_input(args.input)
    report = check(text, source_label=source)
    if args.json:
        print(_format_check_json(report))
    else:
        print(_format_check_human(report))
    return 0 if report.filled_count == len(SLOT_NAMES) else 1


def _cmd_ask(args) -> int:
    text, source = _read_input(args.input)
    report = check(text, source_label=source)
    questions = ask(report)
    if args.json:
        print(json.dumps(questions, indent=2, ensure_ascii=False))
        return 0
    if not questions:
        print(f"all {len(SLOT_NAMES)} slots already filled — the prompt is complete.")
        return 0
    print(f"# {len(questions)} question(s) to fill the empty slots:")
    print()
    for q in questions:
        print(f"{q['slot']} {q['label']}:")
        print(f"  {q['question']}")
        for hint in q["hints"]:
            print(f"  · {hint}")
        print()
    return 0


def _cmd_expand(args) -> int:
    text, source = _read_input(args.input)
    answers: dict[str, str] = {}
    if args.answers:
        try:
            answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"error: cannot read answers: {exc}", file=sys.stderr)
            return 2
    # Accept per-slot flags: --length, --format, --reasoning, etc.
    slot_flag = {
        "B1":  args.task,
        "B2":  args.format,
        "B3":  args.length,
        "B4":  args.context,
        "B5":  args.few_shot,
        "B6":  args.constraints,
        "B7":  args.clarify,
        "B8":  args.reasoning,
        "B9":  args.verification,
        "B10": args.decomposition,
    }
    for slot, val in slot_flag.items():
        if val:
            answers[slot] = val

    # Emit the composition prompt only. In a Claude Code session, Claude
    # reads this prompt and composes the expanded rewrite directly in chat —
    # no API call, no key, no cost. Outside Claude Code, paste the emitted
    # prompt into any LLM and run it there. This script never calls an API.
    print(build_expand_prompt(text, answers))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="boost",
        description="opus-mind boost — spec quality for user prompts",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="slot coverage report")
    p_check.add_argument("input", help="prompt text, file path, or '-' for stdin")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=_cmd_check)

    p_ask = sub.add_parser("ask", help="emit questions to fill missing slots")
    p_ask.add_argument("input")
    p_ask.add_argument("--json", action="store_true")
    p_ask.set_defaults(func=_cmd_ask)

    p_exp = sub.add_parser(
        "expand",
        help="emit composition template for the LLM (NOT an API response)",
        description=(
            "Emits a composition prompt — a template that instructs an LLM "
            "to rewrite the user's vague prompt into a concrete one, using "
            "the slot answers as raw material. This script never calls an "
            "API. In a Claude Code session, the invoking Claude reads the "
            "emitted template and writes the rewritten prompt as its reply. "
            "Standalone CLI users should paste the output into any LLM "
            "(Claude.ai, ChatGPT, Cursor) and run it there."
        ),
    )
    p_exp.add_argument("input")
    p_exp.add_argument("--answers", help="path to JSON with slot answers")
    p_exp.add_argument("--task")
    p_exp.add_argument("--format", dest="format")
    p_exp.add_argument("--length")
    p_exp.add_argument("--context")
    p_exp.add_argument("--few-shot", dest="few_shot")
    p_exp.add_argument("--constraints")
    p_exp.add_argument("--clarify")
    p_exp.add_argument(
        "--reasoning",
        help="B8 — request step-by-step thinking (e.g. 'yes' or explicit clause)",
    )
    p_exp.add_argument(
        "--verification",
        help="B9 — request self-check after drafting (e.g. 'yes' or explicit clause)",
    )
    p_exp.add_argument(
        "--decomposition",
        help="B10 — request plan-before-execute (e.g. 'yes' or explicit clause)",
    )
    p_exp.set_defaults(func=_cmd_expand)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
