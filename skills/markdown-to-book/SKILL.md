---
name: markdown-to-book
description: "Bundle a COLLECTION of markdown files (a docs folder, numbered chapters, a research series) into one book published in three lockstep editions sharing one basename: a single-file .md agent edition with provenance frontmatter (the context handoff for another AI agent), an .epub reading edition (Kindle/TTS, via the markdown-to-epub recipe), and a .pdf print edition (via the markdown-to-pdf recipe). Use whenever the user wants to share a multi-file markdown corpus as ONE artifact - with their team, their Kindle, or another agent. Triggers: 'bundle these chapters', 'make a book from this folder', 'turn this folder into one file', 'context bundle', 'single file for my agent', 'markdown to context', 'markdown to agent', 'share this with an agent at work', 'rebuild the book', 'the three editions', 'epub and pdf and markdown of this folder'. Also use when a previously built book's source chapters changed and the editions must be rebuilt in lockstep. NOT for converting one markdown file (use markdown-to-epub or markdown-to-pdf directly) and not for branded client deliverables (use branded-docx / brief-creator)."
compatibility: Requires the markdown-to-epub and markdown-to-pdf skills installed alongside (same library); their scripts and stylesheets are called directly.
metadata:
  version: 0.1.0
---

# markdown-to-book

One source folder of markdown chapters, three published editions, one basename:

| Edition | Audience | What makes it that edition |
|---|---|---|
| `.md` | An AI agent (context handoff) | Single concatenated file, provenance frontmatter, Mermaid kept as live fences (machine-readable source beats a picture) |
| `.epub` | A human reading or listening (Kindle, TTS) | Cover, combined TOC, Mermaid rendered to PNG |
| `.pdf` | A human printing or skimming | Page/version/date stamps, Mermaid rendered as vector |

They are editions of one book, never three documents. **The lockstep rule: any edit to a source chapter invalidates all three; rebuild all three in the same session, or say plainly which ones are stale.** Filenames never carry version suffixes in a repo - git history is the version axis; note content changes concisely in the intro's "Edition notes" block instead. Version-suffixed names belong only in throwaway locations (Downloads) where generations coexist as loose files.

## Step 0 - scope check and dependencies

A single markdown file needs no bundling: hand it to `markdown-to-epub` or `markdown-to-pdf` directly and stop here. This skill earns its keep when there are multiple files whose value depends on order and togetherness.

**Sibling-skill dependency (check FIRST):** the EPUB and PDF steps call the `markdown-to-epub` and `markdown-to-pdf` skills' own scripts and stylesheet (`make_cover.py`, `epub.css`, `print_markdown.py`). Verify both skill folders exist (`~/.claude/skills/<name>/` or the project's `.claude/skills/`) before starting. If one is missing, say so and point at the same library this skill ships from - do not reimplement its conversion inline; a hand-rolled fallback is exactly the drift these skills exist to prevent. The `.md` agent edition has no such dependency and can always be built.

The bundling script is stdlib-only Python. The EPUB step needs pandoc; the PDF step resolves its own deps via `uv run`; Mermaid rendering (only if fences exist) needs mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`). Check pandoc with the markdown-to-epub skill's preflight before the EPUB step.

## Step 1 - determine the reading order

The bundle is only as good as its order. Rules of thumb: a `README.md`/`index.md` becomes the introduction (first); numbered files (`01-*.md`, `02-*.md`) follow their numbers; otherwise propose an order and confirm with the user rather than guessing silently. Every file needs a meaningful `# H1` - those become the TOC entries.

## Step 2 - bundle

```bash
python "<SKILL_DIR>/scripts/bundle.py" \
  --title "Search Relevance Field Notes" \
  --thread "everything learned tuning the search stack, bundled so the next engineer or agent starts where we stopped" \
  --intro-retitle "Introduction: why this book exists" \
  --basename my-book \
  --out-dir <scratch>/book-build \
  README.md 01-chapter.md 02-chapter.md ...
```

The script does the deterministic work identically for all three editions:
- **Strips repo-local link targets, keeps the link text** (web URLs and `#anchors` stay clickable). In a standalone file, relative links are dead links; the text still names the referenced chapter, which is what a linear reader (human or agent) actually needs.
- Optionally retitles the first file's H1 (`--intro-retitle`) so a folder README reads as a book introduction.
- Writes `parts/NN-<name>.md` (preprocessed per-file copies, for the EPUB's `--file-scope` build), `<basename>.md` (the agent edition, with provenance frontmatter), and `<basename>-print.md` (same body, no frontmatter, input for the PDF renderer).

The provenance frontmatter is the agent-to-agent handoff contract: title, build date, origin (repo@commit when the sources are in git), the exact source files in order, and the one-line `--thread` saying why this bundle exists. A receiving agent reads that header and knows what it holds, where it came from, and whether it might be stale - without any A2A protocol ceremony. Keep `--thread` neutral if the bundle might leave the machine (no client names in artifacts that travel).

## Step 3 - Mermaid (only if the sources have ```mermaid fences)

The `.md` edition keeps fences as-is. For the EPUB, render each fence to PNG (`mmdc -i d.mmd -o d.png -b white -w 1400 -s 2`) and swap an image reference into the affected `parts/` copy only. The PDF renderer draws fences itself as vector - feed it the fence, not the PNG.

**Validate the render, don't assume it.** mermaid diagrams are the historical breakage point of this pipeline: a non-zero mmdc exit means broken syntax; a clean exit can still mean an unreadable diagram. The first time a given diagram is built (or after editing it), downscale the PNG under 2000px and actually look at it with the Read tool - node labels legible, edge labels present, structure intact. `\n` inside node labels renders literally; use `<br/>` and quoted labels.

## Step 4 - EPUB and PDF editions

Follow the sibling skills - this skill adds nothing to their mechanics:
- **EPUB**: the `markdown-to-epub` recipe - cover via its `make_cover.py` (title, subtitle, date), then pandoc epub3 over the `parts/` files in order with `--file-scope --toc --toc-depth=2`, metadata title/author, its `epub.css`. Verify after building: cover-image item present in content.opf, diagram `<img>` present, zero `href="*.md"` leftovers.
- **PDF**: the `markdown-to-pdf` recipe on `<basename>-print.md` (it renders Mermaid locally and stamps page/version/date; pick the stamp preset by audience).

## Step 5 - deliver and record

- Canonical copies: if the sources live in a repo, the three editions belong beside them (same folder, one basename) so git carries the editions together - commit only on the user's go.
- Sharing copies: also drop copies in Downloads when the user is sending them somewhere (Kindle, Dropbox, a colleague); suffix these with a version label if older generations already sit there.
- Name every output path explicitly in the reply.
- If this book will be rebuilt in future sessions, leave a short pointer in the project's scoped CLAUDE.md: which folder is the source, the exact bundle.py invocation, and the lockstep rule - so the next session (or another agent) rebuilds instead of reinventing.

## Do not build

The two sibling skills own conversion; pandoc owns concatenation-with-TOC. Do not add: an EPUB/PDF post-processor, a config system, per-project forks of bundle.py (flags cover the variation), or a custom A2A metadata spec beyond the frontmatter block - the header is deliberately small enough that every model reads it without documentation.
