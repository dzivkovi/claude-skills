# read-along

A guided, visual walkthrough of accumulated work, staged as a childhood storybook: a page you read, live pictures that move (the real product driven in a real browser), and a bell that tells you when to turn the page.

This is the skill I reach for the morning after an autonomous overnight run, when the problem is no longer "did the work get done" but "can I comprehend everything that happened." Autonomous agents do not just implement what you asked. They find new problems along the way and fix them, so you routinely wake up to more than you requested. read-along is how I tour all of it, ranked most-important-first, without reading a single commit by hand.

## What it actually does

You say `/read-along` (optionally scoped: `/read-along last night`, `/read-along PRs 40-60`). The skill then:

1. Gathers from durable artifacts, never chat memory. Merged PRs and their bodies, closed and newly-opened issues, `work/<date>/` debriefs, deploy evidence, and a mandatory sweep for buried decisions (`TODO(HUMAN)`, "Decisions for", open PRs awaiting review).
2. Writes a self-contained storybook. One local HTML file, big serif type, dark ground, one ranked section per "stop." Each stop carries a green benefit box (why it matters, in your language), an amber dilemma box (the near-miss, the decision, the plan a measurement killed), and a dashed demo box (what to watch next door).
3. Opens a real browser and drives the real product. A visible Chrome over CDP, storybook in one tab, the live app in the second. Inputs are typed character by character so you watch the question write itself; clicks land on real elements. The story and the evidence sit in adjacent tabs, so claims are watched, not trusted.
4. Runs a strict stop-and-go protocol. One stop per message, then it parks: "Say **go** for Stop N+1, or ask me anything." That parking line is the bell and the state pointer at once. It never advances without go.
5. Lands on one decisions list. Every open call the sweep found, one line each, with a recommendation, so you act from a single highlighted list instead of hunting buried asks.

The interruptions are the feature, not a derailment. When you diverge mid-tour, it handles the tangent completely (investigates with real traces, files issues in your house format, spawns background fixes, even hotfix-review-deploys when you have standing authorization), banks the side quest durably, then returns to the exact same parking line. You can wander because convergence is guaranteed.

## This is a Claude Code skill, not a claude.ai upload

The other skills in this repo are claude.ai capability skills: you upload the `.zip` under Settings and Claude styles a document inside its own sandbox. read-along is different in kind. It orchestrates your local environment: a git repo, `gh` PR history, `work/` notes, subagents, and a real browser it drives over the Chrome DevTools Protocol. None of that exists in the claude.ai sandbox, so uploading it there would do nothing.

Install it where those things live, under Claude Code:

- Copy the folder to `~/.claude/skills/read-along/` (available in every project) or a project's `.claude/skills/read-along/` (that project only). Unzipping `releases/read-along.zip` into either location does the same thing.
- Keep `SKILL.md` and `audio-player.md` side by side. `SKILL.md` reads the audio doc "beside this file" when it adds the in-page voice player, which is why this skill keeps its reference doc at the folder root rather than in a `references/` subfolder.
- Invoke it as `/read-along` in a Claude Code session opened on the repo you want toured.

What it expects to find, and degrades sanely without: `gh` authenticated for the PR sweep, a browser MCP wired to a CDP-enabled Chrome for the live demos (without it, the skill runs in narrate-only mode and you click under its direction), and a repo whose story lives in PRs, issues, and `work/` notes rather than in scattered chat.

## Three scope modes

The gather and the story shape adapt; the stop-and-go protocol never changes.

- OWN-WORK (the default, battle-tested): your recent work in a repo you drive. Stops are shipped features and the decisions they forced.
- ARCHAEOLOGY: a cloned or forked repo you did not build. The story becomes the evolution of its ideas, gathered from releases, high-discussion PRs, and the commit graph's turning points. Tour quality tracks the repo's artifact hygiene, and the skill says so out loud when PR bodies are thin.
- DIVERGENCE: a fork that drifted from upstream, or two long-lived branches. The story is the delta since the merge-base, and the decisions stop becomes a reconciliation list: for each collision, whose work should survive.

## The read-along voice (the literal part)

The storybook can narrate itself. `audio-player.md` is the research and a paste-ready, roughly 110-line, zero-dependency widget built on the browser's Web Speech API: a top-right pill with play/pause, section skip, and a speed cycle; the reading section highlights and scrolls into view so the page follows the voice; sentence chunking plus a 14-second pause/resume keep-alive defeats Chrome's decade-old 15-second cutoff bug. It adds zero bytes, works offline on local OS voices, and disappears cleanly from print. The honest tradeoff, stated rather than hidden: offline local voices sound more robotic than the network "natural" voices, and pre-generated MP3 narration is the opt-in alternative when you want a guaranteed premium voice for a keepsake.

## The scale: five versions in a single day

I did not design this skill up front. It was born during an actual read-along tour of an overnight run, and it earned every one of its rules by being run, breaking, and being hardened, five times over, across two different projects in one day (2026-07-18). The versions that stay in my local library tell the story of what real use taught:

- v1: the core idea. Ranked storybook, live browser demos next door, the stop-and-go bell.
- v2: port safety (a hardcoded debug port attached to a different session's browser with unrelated tabs, so the skill now probes and verifies before driving), artifact-based demos, in-tour honesty (read the artifacts live during the tour, because a live read can reveal a surface is a skeleton and reframe a decision), and the keepsake print property.
- v3: a demo-prep bound (at most one polish pass on demo data, after a run burned four queries hunting a cleaner example while the operator waited), a renderer-aim rule, fatigue adaptation, and verbatim transcript export from the session's own on-disk log rather than a from-memory paraphrase.
- v4: the export menu (repo commit, PDF, Claude artifact), the ARCHAEOLOGY and DIVERGENCE scope modes, in-page audio narration, and narrate-only mode for when the browser port is already taken.
- v5: export refinements from real use. Exports land in Downloads by default with the destination path always named, a Markdown twin as the durable substrate, a black-on-white print palette, and export discoverability surfaced in the first stop.

The pattern worth stealing is not any single rule. It is that a skill improved fastest when its own honest transcript export preserved the real back-and-forth, mistakes included, so each run's failures became the next version's guardrails. The published `SKILL.md` (version 5) is the distilled result. The intermediate v1 through v4 files are kept out of this package on purpose: they are my learning trail, not part of the tool.

## Why it works (the properties to keep if you adapt it)

- Ranked storytelling beats chronology. Dilemmas teach more than wins. Numbers are the plot twists.
- The story and the evidence sit in adjacent tabs, so every claim is watched.
- The strict parking line makes divergence safe: you can wander because the tour is guaranteed to land back on its feet.
- The decisions sweep converts "you asked me things somewhere and I never saw them" into one highlighted list.
- Side quests are banked in durable artifacts before the story resumes, so the tour itself leaves the project better than it found it.
