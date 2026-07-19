---
name: read-along
description: Guided visual walkthrough of accumulated work (a session, a PR batch, an overnight run) as an interactive storybook page plus live browser demos, with a strict stop-and-go protocol. Use after long or autonomous sessions, before demos, or whenever the operator says they cannot comprehend everything that happened.
---

# /read-along : the guided storybook walkthrough

Version 5 (2026-07-18). Prior versions preserved beside this file (v1.md through v4.md). v2: port safety, artifact demos, in-tour honesty, keepsake print. v3: demo-prep bound, renderer aim, fatigue adaptation, verbatim transcript export. v4: the export menu, archaeology and divergence scope modes, audio narration, narrate-only mode. v5 (all export refinements, operator-driven): exports land in the operator's Downloads folder by default with the destination path ALWAYS named in the confirmation; the Markdown twin as the post-processing substrate; the black-on-white print palette; export discoverability in the first parking line.

The operator's framing: the childhood read-along record book. A storybook page they read, live pictures that move (the real product driven in a real browser), a bell that tells them when to turn the page, and a host who welcomes interruptions and always lands the story back on its feet. Target 5 to 15 minutes of reading: 5 to 9 stops, most important first. Mark Twain rule: a short walkthrough takes MORE contemplation than a long one - rank hard, cut hard.

Origin: the 2026-07-18 overnight-run tour in ask-your-binder (work/2026-07-18/02-night-run-morning-summary.md is the source material it narrated). This skill codifies exactly what made that session work. The origin project happened to be a web app - that is an EXAMPLE, not a template; Phase 3 explains how the demo medium adapts per project. The bell metaphor is literal: the original Disney read-along records paced the child's reading and rang when it was time to turn the page - the parking line is that bell, so keep its rhythm steady and unmissable.

## Phase 0 : scope

Resolve what period or set of work the read-along covers, in this order: (1) an explicit argument ("/read-along last night", "/read-along PRs 40-60", "/read-along since v2.1"); (2) the marker left by the previous read-along (grep work/ for "read-along landed" - the closing note this skill always writes); (3) if neither exists, ask ONE question with 2-3 concrete options (e.g. "since yesterday's session / the last 20 merged PRs / this week") and proceed. Never interrogate further - scope precision is not the product.

Three scope MODES (v4) - the gather and story shape adapt, the protocol never changes:

- OWN-WORK mode (the default, battle-tested): your recent work in a repo you drive - PRs, issues, work notes, deploys.
- ARCHAEOLOGY mode (a cloned or forked repo you did NOT build): the story is the EVOLUTION OF ITS IDEAS - gather from releases, the highest-discussion PRs and issues, CHANGELOG arcs, and the commit graph's turning points; the stops become eras or pivotal decisions rather than shipped features. Honesty rule: tour quality tracks the repo's artifact hygiene - when PR bodies are thin, say so and lean on reading the code live instead of inventing narrative.
- DIVERGENCE mode (a fork that drifted from upstream, or two long-lived branches): gather BOTH sides since the merge-base (git log --left-right upstream...fork, PRs on each), and the story is the delta - what upstream did, what the fork did, where they collide. The decisions stop becomes a reconciliation list: for each collision, whose work should survive, with a recommendation - this is a collaboration surface, not just a recap. (Designed, not yet battle-tested; expect a finding on first run.)

## Phase 1 : gather from durable artifacts, never from chat memory

The repo is the accumulator; scattered chat sessions do not matter. Collect (delegate to ONE read-only subagent if the sweep is large, to protect the narrator's context):

- Merged PRs in scope: `gh pr list --state merged` + bodies of the significant ones (PR bodies carry the deep whys).
- Closed AND newly-opened issues in scope, with the titles' priority prefixes.
- work/<date>/ notes in scope, especially debriefs, morning summaries, and RESULTS-style reports.
- Deploy or release evidence (revision numbers, build ids, live URLs) when the project ships.
- THE DECISIONS SWEEP (mandatory - the operator has been blindsided by buried asks before): grep the repo for `TODO(HUMAN)`, grep work/ for "Decisions for" and "waiting on", list OPEN PRs awaiting review, and scan recent issue comments for taste blocks. Everything found feeds the final stop.

## Phase 2 : write the storybook

One self-contained local HTML file in the session scratchpad (no external assets - it must open from file://). The proven shape:

- Big serif type (Georgia), dark background, generous line-height; a sticky top nav of stop anchors; header with a one-paragraph promise of the story.
- One `<section class="stop" id="stopN">` per stop, most important first. Per stop: a kicker line ("Stop N of M : theme"), a heading, 1-3 short narrative paragraphs, then the box vocabulary that carries the teaching load:
  - GREEN "benefit" box: why it matters, in the operator's language, never engineering language.
  - AMBER "dilemma" box: the decision, the near-miss, the thing the review caught, the plan the measurement killed. These teach MORE than the wins - never omit them.
  - DASHED "demo" box: what to watch in the live tab, one sentence.
- Deep-dive stops (a "Stop N.5") use the SIX-ACT shape when a single change deserves its own story: the complaint, the suspect, the measurement where the story turns, the real culprit, the fix, the dilemma killed by its own numbers. Include the real measured numbers as a small table - numbers are the plot twists.
- The FINAL stop is always "the paper trail": where the story lives durably for a newcomer (the capabilities/benefits doc, the summary note, the PR bodies), links the operator should open in THEIR browser (auth-walled things like GitHub), and the DECISIONS LIST from the Phase 1 sweep - every open call, one line each, with your recommendation.
- Prose rules: the operator's global rules apply INSIDE the HTML too - no em-dashes or en-dashes, no emojis, no hard-wrapped paragraphs.
- A closing "end" block with the one-sentence through-line of the whole story.

## Phase 3 : the browser and the demo medium

FIRST, detect what kind of project this is and pick the demo medium accordingly - the storybook always lives in the browser, but the "pictures that move" differ (this generalization came from the skill's first cross-project run: it was written on a web-app project and a CLI project immediately exposed the assumption):

- Web app or served product (a serve entrypoint, a deploy script, a live URL): drive the LIVE product in a second tab - real inputs typed visibly, real clicks.
- CLI, library, or pipeline project: the moving pictures are (a) the project's own generated artifacts opened live in browser tabs - HTML visualizations, reports, generated docs/wikis, notebooks - and (b) real CLI invocations run in front of the operator with their actual output narrated (run the command fresh; never paste stale output into the story). If an artifact does not exist yet but one command away, generating it live IS the demo.
- Docs or data projects: the artifacts themselves (rendered pages, diagrams, before/after diffs opened side by side).
- WHEN THE NATURAL RENDERER IS FIDDLY (an Obsidian vault that opens to a blank canvas, a notebook needing a kernel, a desktop app you cannot drive): publish the material as a Claude artifact and show that instead - a battle-tested fallback the operator themselves reached for. RESTRAINT RULE: artifacts are for when the surface should outlive the session, be shareable, or replace a renderer you cannot drive; when a plain local HTML file opened in the tour browser would do the same job, use the plain file. Never mint artifacts for ordinary demo beats.

Detection is cheap: look for a serve/web entrypoint or deploy config first, then for generated-artifact directories (docs/reports, *.html outputs, wiki folders), then default to CLI-output demos. When a project has both (a CLI that also ships an HTML report), prefer the browser-openable artifact for the demo box and the CLI run as its build-up.

Launch a VISIBLE (headed, never headless) Chrome with CDP, isolated profile, and the storybook as the opening tab:

```
"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=<PORT> \
  --user-data-dir="$TEMP/chrome-readalong-<PORT>" --no-first-run --window-size=1400,950 "file:///<storybook path>"
```

AUDIO NARRATION - the literal read-along (v4, researched): the storybook can carry a built-in voice. The full research and a paste-ready ~110-line widget live in audio-player.md BESIDE THIS FILE - read it when adding the player. The essentials: Web Speech API (speechSynthesis) as primary - zero bytes, offline via local OS voices, hidden in print by one @media rule; a top-right docked pill (play/pause, prev/next SECTION, speed cycle 0.8x-2x, minimize, "Stop N of M" progress - sections, never seconds); each .stop is the read-and-skip unit with tables/code/demo boxes replaced by one-line spoken stubs; the reading section is highlighted and scrolled into view (the page follows the voice); sentence-chunking under 200 chars plus a 14s pause/resume keep-alive defeats Chrome's 15-second cutoff; graceful degradation hides the pill when no engine exists. Honest tradeoff to state, not hide: offline local voices sound robotic next to the network "natural" voices. Pre-generated MP3 narration is the opt-in alternative (better voice, ~2.4MB per 10 minutes embedded, goes stale on edits). The player is ADDITIVE: the page must remain fully readable, printable, and demo-able with the pill closed.

ONE CDP READ-ALONG PER MACHINE (v4, learned the hard way twice in one day - once by each session, in both directions): the browser MCP is pinned to one debug port, so when another session's CDP Chrome is alive, you CANNOT safely drive yours - and you must never drive theirs. If the port probe finds a foreign owner: run this read-along in NARRATE-ONLY mode - open the storybook and demo surfaces in a plain no-debug-port window, narrate each stop, and let the operator do the clicking under your direction (which is arguably the most read-along mode of all). Reclaim the port only after the other session's browser is truly gone.

PORT SAFETY (a first-run incident, not a hypothetical): the browser tools attach to whatever Chrome owns the debug port - on a machine running parallel sessions, a hardcoded 9222 attached to a DIFFERENT session's browser with unrelated and sensitive tabs. Before launching: probe whether the intended port is free (`curl -s http://127.0.0.1:<PORT>/json/version`); if anything answers, pick another port (9222, 9223, 9224...) until one is silent. After launching: VERIFY the connected browser is yours before driving anything - list pages and confirm the only tab is the storybook you just opened; if you see unfamiliar tabs, STOP, do not drive, do not read them, and tell the operator which port collided. Never drive a browser you did not launch.

Then drive via the chrome-cdp MCP tools. Open the live product in a SECOND tab. For Basic-auth-gated apps: fetch the credential, base64 it, and set it per-tab with the emulate tool's extraHttpHeaders ({"Authorization": "Basic <b64>"}) - never credentials in the URL, never the operator's own profile. Navigate the storybook between stops by setting location.hash to the stop anchor.

Demo driving rules (the pictures must move):
- STAGE DIRECTION FIRST: bring the demo tab to the FRONT (activate it) BEFORE driving it, and say so in the narration ("eyes on the browser") - CDP happily drives background tabs and the operator sees nothing (a first-audience finding: the whole Stop 2 demo ran invisibly behind the storybook tab). Switch back to the storybook tab only when the demo beat is done.
- Type inputs character by character (~30ms apart) via the page's own input element + input events, then click the real submit control - the operator watches the question write itself.
- Wait for completion by polling for the page's own done-signal (an actions row, a terminal element), never a fixed sleep.
- Never screenshots as the medium; the DOM is the medium. Real clicks on real elements.
- If a demo depends on state (a session, browsed topics), build that state live as part of the show.
- DEMO-PREP BOUND (v3): at most ONE polish pass on a demo's data. A battle-test run spent four successive queries hunting a "cleaner" example while the operator waited between stops - the first real result was already good. Real data is allowed to look real; a slightly messy authentic example beats a polished hunt, and authenticity IS the aesthetic of this format.
- RENDERER AIM RULE (v3): before launching a desktop renderer (Obsidian, a notebook app), verify it will open TO the content (vault registered, file association, protocol target) - a renderer that opens to a blank canvas reads as a broken demo and costs an operator round-trip. If you cannot verify the aim, skip the launch and go straight to the artifact/HTML fallback.

## Phase 4 : the tour protocol (the state machine the operator loves)

- One stop per assistant message: navigate the storybook to the stop, run the stop's live demo, then narrate in chat - what they just watched, the one thing to notice, in storyteller voice. Keep each stop's chat message tight; the page carries the depth.
- END EVERY MESSAGE with the same parking line shape: "Say **go** for Stop N+1 - <one-clause teaser>, or ask me anything." That line is the bell AND the state pointer. Never advance without "go" (or an unmistakable equivalent).
- INTERJECTIONS ARE THE FEATURE, not a derailment. When the operator diverges: handle it COMPLETELY - investigate with traces, spawn background subagents for research or fixes, file issues in the house format, even hotfix-review-deploy if the finding is live and the operator has standing authorization. Bank every side quest durably (a ticket, a PR, a memory, a doc) and report it tightly. THEN return with the parking line, unchanged. The tour never advances during an interjection and never loses its place.
- Parallel side-quest agents get isolated worktrees when more than one writes code (the shared-checkout branch cross-wiring lesson).
- The storybook is LIVING: when an interjection deserves its own chapter ("I don't follow this one - it deserves its own step"), write a new stop into the HTML (a Stop N.5), reload the tab, add it to the nav, and tour it. The operator may also ask for edits to the story itself - honor them.
- If the operator asks a question mid-stop, answer from the gathered material or live traces (production audit records, logs) - real evidence, storyteller framing.
- THE IN-TOUR HONESTY RULE (battle-tested: it changed an operator decision): actually READ the artifacts you demo, during the tour, not from the gathered digest - a live read can surface that a surface is a skeleton, a number is stale, or a claimed capability is unfilled, and when it does, say so on the spot and let it reframe the decisions stop. A tour that discovers a problem is a better tour.
- FATIGUE ADAPTATION (v3): interjection ANSWERS keep the tour's storyteller brevity - the storybook carries depth, chat stays tight. On any fatigue signal ("for tired me", shrinking operator replies, evening hours), compress harder: two-line answers, one action, and move depth INTO the storybook or an artifact instead of the chat. A battle-test operator had to explicitly ask for conciseness mid-interjection; do not make them ask.

## Phase 5 : landing

The final message after the last stop: the decisions list again in one place (the operator acts from ONE list), what was spawned during interjections (tickets, fixes, deploys), and the through-line sentence. Then write a short work note ("read-along landed: scope X to Y, stops toured, side quests spawned, decisions surfaced") - this note is the scope marker the NEXT read-along finds in Phase 0. Leave the browser open for the operator to keep exploring. The storybook doubles as a keepsake - operators print stops to PDF and file them (a first-run behavior, unprompted) - so keep it strictly self-contained: it must render perfectly from file:// and survive printing with no network.

STORYBOOK EXPORT MENU (v4, refined v5) - offer these at landing; the operator picks, never all by default. DESTINATION (v5): exports default to the operator's Downloads folder (NOT the repo - repo placement only on explicit request), and every export confirmation NAMES THE FULL DESTINATION PATH - an operator went hunting in the wrong folder because the confirmation was vague about where the file landed. DISCOVERABILITY (v5, an operator had to ask): mention once, in the FIRST stop's parking message, that "export the storybook" works at any time - and because the storybook lives in the session scratchpad, which dies with the session, proactively drop a durable HTML copy (Downloads or the project's work/ folder, uncommitted) as soon as the operator says they like the tour - never let a loved storybook evaporate on a technicality.

- COMMIT TO THE REPO: the durable answer for anyone who will ever clone the repo - the storybook goes into work/<date>/ (or docs/tours/ if the project keeps a tour shelf) via the house PR discipline. A curious developer's first door into the codebase's story.
- PDF: the storybook already prints cleanly (the keepsake property); produce it headlessly - `chrome --headless=new --print-to-pdf="<out>.pdf" --no-pdf-header-footer "file:///<storybook>"` - for teams and email. PRINT PALETTE (v5): the screen keeps the storybook's visual identity, but the template MUST carry an @media print block that flips to pure black-on-white (white ground, near-black text, mid-gray no lighter than #444 for secondary text, gray borders replacing colored box accents, nav and player hidden) - a dark-background PDF is useless on paper and on monochrome printers. If the output file is locked by an open viewer, write under a -print suffix and say so.
- CLAUDE ARTIFACT: publish the storybook via the Artifact tool for a shareable link when the audience has no repo access. It already satisfies artifact constraints (fully self-contained); strip any live-app demo links that would dead-end for outsiders, and apply the artifact restraint rule from Phase 3.
- MARKDOWN TWIN (v5) - the post-processing substrate, and the recommended durable format: RE-EMIT the storybook content as clean Markdown from the same source, never html-to-markdown conversion (the storybook is generated; the generator writes both renderings). Mapping: stop = ## heading with the kicker as an italic eyebrow; the box vocabulary becomes labeled blockquotes - "> **BENEFIT - <label>:**", "> **DILEMMA - <label>:**", demos as italic asides - so a one-line grep harvests all benefit rows for the project's positioning/feature-benefit ledger (the green boxes ARE proto-ledger entries); tables stay Markdown tables. HTML is the experience; Markdown is the substrate for tutorials, ledger extraction, Obsidian, and any future processing - and it lands in ANY folder, git-versioned or not.

TRANSCRIPT EXPORT (v3): offer to save the session as a shareable Markdown transcript - operators want to share good runs with the skill's maker and with colleagues. When they say VERBATIM, extract from the session's own on-disk log (the .jsonl transcript Claude Code writes), never a from-memory paraphrase - a battle-test operator rejected the paraphrase and asked for the real record. Render operator/assistant turns verbatim, tool calls as compact one-line markers (never raw outputs - they hold megabytes and can hold cross-session data). Scrub before it travels: no secrets, no cross-session specifics, no client or engagement context; sensitive incidents told generically (the shape of the bug, not the contents of the other browser).

## Why this works (keep these properties when adapting)

- Ranked storytelling beats chronology; dilemmas teach more than wins; numbers are the plot twists.
- The story and the evidence sit in adjacent tabs - claims are watched, not trusted.
- The strict parking line makes divergence safe: the operator can wander because convergence is guaranteed.
- The decisions sweep converts "you asked me things somewhere and I never saw them" into one highlighted list.
- Side quests are banked in durable artifacts before the story resumes, so the tour itself leaves the project better than it found it.
