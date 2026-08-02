---
name: markdown-to-pdf
description: "Convert Markdown into a plain, internal-grade PDF with clickable links (including timestamped video deep-links), real tables, locally rendered Mermaid diagrams, and light header/footer stamps (Page N of M, version and date, author contact line). Use when the user wants to print or share a Markdown doc as a PDF that should read as a working document, not a branded deliverable: briefings, architecture notes, internal memos, work notes, docs with Mermaid diagrams or comparison tables. Triggers: 'markdown to pdf', 'print this markdown', 'make a PDF of this doc/briefing/note', 'PDF with mermaid diagrams', 'render the tables properly in PDF', 'internal PDF, not the branded one', 'plain PDF for the team'. NOT for polished client-facing documents (use branded-docx or brief-creator) and not for e-reader output (use markdown-to-epub, the reading/Kindle sibling)."
metadata:
  version: 0.1.0
---

# markdown-to-pdf

Turn a Markdown file into a plain, print-grade PDF where every hyperlink stays clickable, pipe tables become real tables, and ```mermaid fences are rendered locally (no network) and embedded as diagrams. Output reads as an internal working document: no cover page, no table of contents, no brand tokens. For the polished branded look use `branded-docx`; for e-reader output use `markdown-to-epub`.

## Why this exists

Three converters were converged into this one. A reportlab briefing renderer had clickable links but printed tables as raw pipe characters. A headless-Chrome print script had beautiful tables and Mermaid but produced PDFs with zero /URI link annotations (measured; no Chrome flag fixes it). This skill keeps the winning half of each: one reportlab engine with links everywhere (including inside table cells), tables, Mermaid via local mermaid-cli, and the proven header/footer stamp scheme (Page N of M top-left, version and date top-right, author contact centered in the footer).

## Step 0 - dependencies

The script carries a PEP 723 header, so `uv run` resolves Python deps (markdown, reportlab, pillow) automatically. Without uv: `pip install "markdown>=3.6" "reportlab>=4" pillow` and run with plain `python`.

mermaid-cli is required ONLY when the document contains mermaid fences: `npm install -g @mermaid-js/mermaid-cli`. Documents without diagrams never touch it.

## Usage

```bash
uv run "<SKILL_DIR>/scripts/print_markdown.py" doc.md
uv run "<SKILL_DIR>/scripts/print_markdown.py" architecture.md --author "jane.doe@example.com" --docversion v1.0.3
uv run "<SKILL_DIR>/scripts/print_markdown.py" notes.md --accent "#0b5394"
```

| Flag | Default | Meaning |
|---|---|---|
| `--out` | `<stem>.pdf` beside the source | Output path |
| `--author` | `daniel@magmainc.ca` | Footer contact line; pass `''` to suppress |
| `--docversion` | empty | Version label in the top-right header |
| `--date` | today | Date shown top-right; pass the document's own date for briefings |
| `--accent` | `#c96442` | Link and h2 color; `#0b5394` gives a conservative internal-blue look |

REBRAND: the two defaults worth changing are `DEFAULT_AUTHOR` and `DEFAULT_ACCENT` at the top of the script, or just pass the flags.

## Verify (do this for link-heavy documents)

```bash
python -c "from pypdf import PdfReader; r=PdfReader('doc.pdf'); print(sum(1 for p in r.pages for a in (p.get('/Annots') or []) if a.get_object().get('/A')))"
```

A link-bearing document must report a nonzero count. `assets/sample.md` exercises every supported construct (links in table cells, nested lists, code wrap, two Mermaid diagram types); render it after install and walk its bottom checklist.

## Limitations (known, by design)

- Wide Mermaid sequence diagrams (aspect ratio above ~2, common at 5+ participants) are structurally illegible at portrait body width in every renderer; split the diagram or accept reference scale. Not fixable here.
- Standard PDF base-14 fonts: exotic Unicode glyphs (arrows, box drawing) may not render; standard punctuation is safe.
- Supported Markdown is the working-document subset: h1-h4, paragraphs, nested lists, pipe tables, fenced code, mermaid fences, blockquotes, rules, bold/italic/code/links, bare URLs (autolinked). YAML front matter and HTML comments are stripped.

## Do not build

The single script is the whole engine. Do NOT add: a cover page, TOC, brand tokens (that is branded-docx territory), a config file, or an HTML intermediate for styling. Header/footer flexibility stays as-is: the three stamp slots are deliberate.
