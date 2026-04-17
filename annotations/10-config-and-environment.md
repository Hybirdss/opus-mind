# Annotation 10 — Config & Environment (lines 1374–1408)

35 lines. The tail of the prompt. Network config, filesystem mounts, thinking mode toggle.

## Structure

```
{network_configuration}        lines 1374–1380
{filesystem_configuration}     lines 1382–1391
{antml:thinking_mode}auto{/antml:thinking_mode}     line 1393
[tail notes]                   lines 1395–1408
```

## Lines 1374–1380 — network configuration

A whitelist of allowed outbound domains for bash_tool:

> *"api.anthropic.com, archive.ubuntu.com, crates.io, files.pythonhosted.org, github.com, index.crates.io, npmjs.com, npmjs.org, pypi.org, pythonhosted.org, registry.npmjs.org, registry.yarnpkg.com, security.ubuntu.com, static.crates.io, www.npmjs.com, www.npmjs.org, yarnpkg.com"*

Package managers and system update sources. No general web access from bash.

Line 1379:

> *"The egress proxy will return a header with an x-deny-reason that can indicate the reason for network failures. If Claude is not able to access a domain, it should tell the user that they can update their network settings."*

This is capability disclosure (primitive 11) of a *failure mode*. The model is told *how failure looks* (`x-deny-reason` header) and *what to tell the user* (update network settings). Operational friction gets a user-facing message template.

## Lines 1382–1391 — filesystem configuration

Read-only mounts:
- `/mnt/user-data/uploads`
- `/mnt/transcripts`
- `/mnt/skills/public`
- `/mnt/skills/private`
- `/mnt/skills/examples`

Line 1390 states the copy-on-write convention:

> *"Do not attempt to edit, create, or delete files in these directories. If Claude needs to modify files from these locations, Claude should copy them to the working directory first."*

The policy handles two classes of mistake: writes that would fail, and reads that would go stale if the user replaced the source. The "copy to working directory" rule is a **defensive programming idiom** — turn read-only source material into a mutable local copy before modification.

## Line 1393 — thinking mode

> *"{antml:thinking_mode}auto{/antml:thinking_mode}"*

A single tag setting thinking mode. Brief, machine-consumed.

## Lines 1395–1408 — tail notes

The final paragraph instructs the model to consider using `{antml:thinking}...{/antml:thinking}` blocks after function results:

> *"Whenever you have the result of a function call, think carefully about whether an {antml:thinking}{/antml:thinking} block would be appropriate and strongly prefer to output a thinking block if you are uncertain."*

Interesting phrasing: "strongly prefer." Not "always." The default is lean-toward-thinking-block under uncertainty. This is a soft cue vs a hard rule — appropriate for a quality improvement that doesn't need strict enforcement.

## Primitives and techniques evidenced

- 01 Namespace blocks — the config blocks at the end of the prompt.
- 03 Hard numbers — allowed-domains whitelist.
- 11 Capability disclosure — `x-deny-reason` mechanism described.

## What to steal

Two design moves worth noting:

**Explicit failure-mode description.** The network section doesn't just say "some domains are blocked." It tells the model *how failure will present* (`x-deny-reason` header) and *what to communicate* (tell the user they can update network settings). When a tool might fail in ways the model doesn't naturally understand, document the failure surface.

**Tail placement for soft rules.** The thinking-mode preference sits at the end of the prompt — a **soft** rule (strong preference, not requirement) in a low-attention position. Hard rules go earlier; soft improvements can live at the tail. The model still reads them, but the positional cue signals non-criticality.
