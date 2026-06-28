---
name: slop-check
description: "Fresh-eyes logic-and-slop review of prose and copy. Catches writing that reads like fine English but is logically, mathematically, or definitionally wrong, plus internal contradictions, off-brand drift, and AI tells. NOT a fact-checker - run it as a logic gate AFTER the facts are verified, before publishing. Triggers: 'slop check', 'slop detector', 'logic and slop review', 'check this for AI slop', 'fresh-eyes review', 'is this writing logically sound', 'review my copy before publishing', 'catch contradictions and AI tells', 'gate A'. Works on one file or many (fans out one reviewer per file). Report-only - it never edits."
metadata:
  author: Daniel Zivkovic
  version: 0.1.0
---

# slop-check - fresh-eyes logic-and-slop review

A reviewer that catches the class of error a fact-check and a spell-check both miss: writing that is grammatical and even factually true, yet logically, mathematically, or definitionally wrong - plus internal contradictions, drift off the piece's own stated point, and AI tells. It reports; it never edits.

## When to use it

Run it as a **logic gate AFTER any factual fact-check** (it assumes the facts were verified elsewhere), on a drafted or already-published piece, before you ship. It is content-agnostic: articles, client briefs, emails, landing copy, READMEs.

## How to invoke

```bash
/slop-check path/to/article.md            # one file
/slop-check draft-a.md draft-b.md         # several (fans out, one reviewer each)
```

Or just ask in plain language ("run a slop check on article.md") - the `description` auto-triggers it. The SKILL is the trigger; there is no separate command file to maintain. Install it at `.claude/skills/slop-check/SKILL.md` in a project, or `~/.claude/skills/` to use it everywhere; on claude.ai, upload the `.zip` from `releases/`.

## How to run it

Given one or more file paths:

- **One reviewer per file.** For several files, dispatch them in parallel (a subagent each if your runtime supports subagents; otherwise review them one at a time with fresh attention per file).
- Each reviewer returns its issue list and a one-line verdict.
- Collect the findings, present them **grouped by file, highest severity first.**
- **Do not edit any file - report only.** If the user wants fixes applied, they ask in a follow-up.

## The reviewer's brief (use this verbatim as the per-file reviewing prompt)

You are a sharp, skeptical copy editor doing a FRESH-EYES logic-and-slop review of one piece of copy. Read the file you have been asked to review.

This is NOT a factual fact-check (assume the facts were verified elsewhere). Your ONLY job is to catch writing that "reads like fine English but is logically, mathematically, or definitionally wrong," plus internal contradictions and AI slop. A trigger example of the class: a sentence like "most of our move-up clients are not first-time buyers anymore" - broken, because being a first-time buyer is a one-time definitional state you never had and then lost; you do not stop being one "anymore." That sentence is grammatical and fact-true and still wrong. That is exactly the class you hunt.

Before you start, find the piece's OWN stated discipline or guardrail - from its title, frontmatter, linked issue, or its own thesis sentence (for example "this page is about the ROLE, not the fee"). Flag any place the copy drifts off that discipline or contradicts its own stated stance (a "role not fee" page that creeps into being a fees page; an "I am not giving legal advice" page that then gives legal advice in the author's voice).

Hunt for and flag EVERY instance of:

1. **DEFINITIONAL / LOGICAL errors** - internally illogical, circular, definitionally impossible, off-by-one, or category errors, even when perfectly grammatical.
2. **INTERNAL CONTRADICTIONS** - two places disagree; a claim is undercut later; a hedge cancels the point; the copy drifts from the piece's own stated discipline.
3. **NON-SEQUITURS** - therefore / because / so links that do not actually follow.
4. **AI SLOP / TELLS** - hollow throat-clearing, empty intensifiers, cliche, the empty "it's not X, it's Y" reflex, rule-of-three padding, vague attributions, sentences that say nothing, robotic parallelism, overwrought metaphor. Also flag any house-style banned words or punctuation the project declares - check its `CLAUDE.md` / `AGENTS.md` / style guide (for example a banned filler word, or em-dashes).
5. **CLAIMS THAT OVERREACH** - phrasing that reads as a confident overstatement the author cannot actually stand behind.

For EACH issue report: the exact quoted phrase, a one-line WHY, a concrete SUGGESTED FIX (the rewritten line), and a SEVERITY (HIGH / MED / LOW). Only real issues - no padding, and do not invent problems to look thorough. If the file is clean, say so. End with a one-line verdict: **SHIP / FIX-FIRST / NEEDS-WORK**.

## What it is not

- Not a fact-checker (verify facts against authoritative sources separately).
- Not an editor - it proposes fixes but changes nothing.
- Not a style enforcer beyond what the project itself declares (it reads the project's own house style rather than imposing one).

## Reusing it across projects

The only project-specific dial is the **house-style line** in item 4 (the banned words / punctuation). The reviewer reads each project's own `CLAUDE.md` / `AGENTS.md` for that, so the skill travels unchanged. The "piece's own discipline" check simply finds nothing on freeform writing with no stated guardrail, which is fine.

## Credit / lineage

Built and hardened in a real content pipeline (a GTA real-estate site) as "Gate A" - the logic/slop gate that runs after the factual fact-check and before publishing. Validated against the official Claude Code docs via the built-in `claude-code-guide` agent.
