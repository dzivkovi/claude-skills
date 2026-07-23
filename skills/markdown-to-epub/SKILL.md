---
name: markdown-to-epub
description: >
  Convert one or more Markdown files into a clickable, text-to-speech-friendly
  EPUB for e-readers (Kindle), with an optional branded cover. Use when the user
  wants an EPUB or ebook from markdown, a briefing or research note as EPUB, or
  wants to aggregate several markdown artifacts into a single self-contained
  topical EPUB "book" with an intro and a table of contents (common after a long
  session or deep research that produced many markdown files that are painful to
  jump between in a chat UI, and that the user wants to read or listen to on the
  go). Preserves clickable links, including timestamped video deep-links, and
  generates a navigable table of contents. Triggers: "make an epub", "turn this
  into an ebook", "epub for kindle", "convert this briefing to epub", "bundle
  these markdowns into a book", "combine these notes into one ebook", "make me an
  ebook of the artifacts you just created".
metadata:
  version: 0.2.0
---

# markdown-to-epub

Turn Markdown into a clickable + listenable EPUB, optionally with a branded cover.
The engine is `pandoc`; this skill is the recipe, one stylesheet, and a cover
generator. Keep the conversion itself scriptless (see "Do not build").

## Why EPUB
It keeps links clickable (including `...&t=<seconds>` video deep-links) and is
text-to-speech readable on Kindle. Print and PDF are neither. A cover image makes
it show as a real book in the Kindle library instead of a blank placeholder.

## Step 0 - preflight the core dependency (pandoc)
Pandoc is the ONE required dependency. Before converting, run:
```bash
python "<SKILL_DIR>/scripts/setup/pandoc_preflight.py"
```
Exit 0 = ready. Exit 2 = missing: it prints the OS-specific install command
(winget/choco/scoop, brew, apt/dnf/pacman) and https://pandoc.org/installing.html.
Relay that and stop; do not auto-install a system package. (The cover step below
additionally needs Pillow; the core conversion does not.)

## Convert from the Markdown SOURCE, never from PDF or DOCX
Markdown holds the real links and headings. PDF->EPUB is lossy. If only a PDF/DOCX
exists, convert THAT to markdown first (`pandoc in.docx -o in.md`) as a last resort.

## Branded cover (optional; default ON for briefings and shared reading books)
Pandoc cannot compose a titled cover, so `scripts/make_cover.py` (Pillow) builds a
portrait PNG: brand background + logo + title + subtitle + author + a DATE stamp
(so multiple same-month versions are distinguishable). Defaults are the Magma
identity (navy `#0C2749`, the bundled `assets/magma-square-1024-dark.png`, Montserrat,
Signal Red date). Then pass the PNG to pandoc via `--epub-cover-image`.
```bash
python "<SKILL_DIR>/scripts/make_cover.py" \
  --title "Marketing Skills Mastery" \
  --subtitle "Corey Haines - a practitioner's guide" \
  --date 2026-07-21 \
  --out "/tmp/cover.png"
# then add to the pandoc call:  --epub-cover-image="/tmp/cover.png"
```
- The DATE is a real ask: it defaults to today (YYYY-MM-DD) and is meant to
  distinguish versions across a month. Pass the document's own date for briefings.
- Cover is a build intermediate; write it to a temp path, not next to the .epub.
- Needs Pillow: `pip install pillow`. If absent, make_cover.py exits 2 with that
  message; build the EPUB WITHOUT `--epub-cover-image` (core still works).
- REBRAND (this is a template): swap `--logo <your-square-logo.png>` (a square PNG
  that may include your wordmark, as Magma's does) and override `--bg`,
  `--title-color`, `--subtitle-color`, `--accent`. Others drop their own logo into
  `assets/` and pass it; nothing else changes.

## Single file
```bash
pandoc "note.md" \
  -f markdown+autolink_bare_uris \
  -t epub3 \
  --toc --toc-depth=2 \
  --metadata author="Daniel Zivkovic" \
  --metadata lang="en" \
  --epub-cover-image="/tmp/cover.png" \
  --css "<SKILL_DIR>/epub.css" \
  -o "note.epub"
```
- `+autolink_bare_uris` turns bare `https://...` URLs into clickable `<a>` anchors
  (the `&` becomes `&amp;` in XHTML - correct, resolves on Kindle).
- Title: pandoc reads the YAML front-matter `title:` if present (the Kindle library
  title). Else add `--metadata title="..."`.
- Drop `--epub-cover-image` to skip the cover.

## Many files -> one book (the aggregation case)
Pandoc concatenates inputs in argument order, then builds ONE combined TOC. No
script needed - this native behavior IS the book builder.
```bash
pandoc "intro.md" "artifact-1.md" "artifact-2.md" \
  -f markdown+autolink_bare_uris \
  -t epub3 \
  --file-scope \
  --toc --toc-depth=2 \
  --metadata title="<topic> - a reading book (<date>)" \
  --metadata author="Daniel Zivkovic" \
  --metadata lang="en" \
  --epub-cover-image="/tmp/cover.png" \
  --css "<SKILL_DIR>/epub.css" \
  -o "<topic>-book.epub"
```
- `--file-scope` isolates each file's heading/footnote IDs so unrelated artifacts do
  not collide. OMIT it only if links BETWEEN the bundled files must resolve.
- TOC entries come from HEADINGS, not filenames: each artifact needs a meaningful
  `# H1`.
- `intro.md` is optional (first, for real introductory prose); a title page from
  `--metadata title=/author=` is generated by default without it.

## Output
Write the `.epub` next to the source (same basename) unless told otherwise.

## Verify (do for link-heavy briefings)
```bash
unzip -q -o out.epub -d _check
grep -rhoE 'href="https://www.youtube.com/watch\?v=[A-Za-z0-9_-]+&amp;t=[0-9]+"' _check | wc -l   # == source link count
grep -oE '<item[^>]*properties="cover-image"[^>]*/>' _check/EPUB/content.opf                       # cover present
```

## Delivery
The user sends the `.epub` to Kindle themselves (Send-to-Kindle email/app). Do not
attempt to push it anywhere.

## Do not build
Native pandoc covers the conversion. The ONLY two code files are asset/environment
helpers, not conversion logic: `scripts/setup/pandoc_preflight.py` (detects the
dependency) and `scripts/make_cover.py` (composes a cover image pandoc cannot make).
Do NOT add: a conversion wrapper, a Lua filter, a file-discovery framework, a config
system, an EPUB post-processor, or a Calibre dependency. Add conversion code only
after native multi-input demonstrably fails a real case. The stylesheet and the cover
are enhancements; links click and TTS reads without either.
