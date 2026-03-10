---
title: "Fix variable font PDF rendering: Montserrat hairline thin in Word export"
date: 2026-03-09
category: ui-bugs
tags:
  - branded-docx
  - fonts
  - variable-fonts
  - pdf-rendering
  - montserrat
  - metropolis
  - microsoft-word
component: skills/branded-docx
severity: high
symptoms:
  - "Montserrat Bold headings render as hairline thin weight in Word PDF exports despite appearing correct in Word"
  - "PDF exported from Word shows weight 100 (Thin) instead of 700 (Bold) for variable font headings"
  - "Arial body text renders correctly in PDF but Montserrat headings do not"
root_causes:
  - "Variable font PDF rendering bug: Word's PDF export engine does not resolve the weight axis of variable fonts correctly, defaulting Montserrat-VariableFont_wght.ttf to weight 100 (Thin) instead of 700 (Bold)"
resolution_type: workaround
version: 2.2.0
see_also:
  - "../logic-errors/cover-token-architecture-prose-vs-code.md"
---

# Variable Font PDF Rendering: Montserrat Hairline Thin in Word Export

## Problem

Montserrat Bold headings rendered as hairline thin in Word-exported PDFs, despite looking correct in Word's on-screen display. The body font (Arial) rendered correctly.

## Investigation

- Confirmed Montserrat installed as variable font files: `Montserrat-VariableFont_wght.ttf`
- Variable fonts contain all weights (100-900) in a single file via a continuous weight axis
- Word's layout engine handles variable fonts correctly for on-screen display
- Word's PDF export engine does **not** resolve the weight axis — defaults to weight 100 (Thin)
- Arial rendered correctly because it's installed as traditional static font files (one `.ttf` per weight)

## Root Cause

Microsoft Word's PDF export engine does not properly handle variable font weight axes. When embedding the font in PDF, it picks the lightest weight (100/Thin) instead of the specified Bold (700). This is a known limitation of Word's PDF renderer — not a docx-js generation issue, not a font issue, but a Word export pipeline issue.

**Key distinction**: The same variable font renders correctly in:
- Word on-screen display
- Google Docs PDF export (cloud engine handles variable fonts)
- Web browsers

It only fails in Word's "Save As PDF" / "Export to PDF" code path.

## Solution

Switched heading font from **Montserrat** (variable font) to **Metropolis** (static TTFs):

- **Metropolis** is a free, open-source geometric sans-serif that closely matches Gotham (the official RE/MAX typeface, ~95% match)
- Distributed as **static `.ttf` files** (one per weight), completely bypassing the variable font bug
- Changed the `heading` token in `remax.md` from `"Montserrat"` to `"Metropolis"`

### Dual-Platform Rule

Documented in `remax.md` Font Requirements:

| Platform | Heading Font | Why |
|----------|-------------|-----|
| **Word** | Metropolis (static TTFs) | Bypasses variable font PDF bug |
| **Google Docs** | Montserrat (Google Font) | Cloud PDF engine handles variable fonts; Metropolis unavailable in Docs font picker |

To switch: change the `heading` token from `"Metropolis"` to `"Montserrat"`.

### Installation

Metropolis static TTFs installed to `C:\Users\danie\AppData\Local\Microsoft\Windows\Fonts\`:
- `Metropolis-Regular.otf`
- `Metropolis-Bold.otf`
- `Metropolis-RegularItalic.otf`
- `Metropolis-BoldItalic.otf`

Source: [github.com/chrismsimpson/Metropolis](https://github.com/chrismsimpson/Metropolis)

## Verification

RE/MAX v3 generated with Metropolis — Bold renders correctly in both Word display and PDF export.

## Files Changed

- `skills/branded-docx/brands/remax.md` — `heading` token changed from `"Montserrat"` to `"Metropolis"`, Font Requirements section rewritten with dual-platform rule, Typography Reference table updated

## Prevention

### Design Principle

**Never trust the Word canvas as the final proof.** Word's on-screen rendering and its PDF export are two different code paths with different font handling. Always verify the export format that the end user will receive.

### Font Selection Rules

1. **Default to static font files** for any workflow that involves Word's PDF export. Treat variable fonts as unsupported in this pipeline.
2. **When selecting a font for a new brand**, verify the font's file type before committing. Check for "Variable" or "VF" in the filename, or inspect the font's `fvar` table.
3. **Maintain a vetted font list** of fonts verified through the full pipeline (Word render + Word PDF export + direct PDF viewer).

### Detection

- **PDF export verification**: After any font change, export to PDF and visually inspect. Word preview alone is insufficient.
- **Weight comparison test**: Render a test string at weight 400 and 700 in the exported PDF. If they look identical, the variable font axis is not being resolved.
- **Font type check**: Inspect installed font files — if a font contains a `fvar` axis (variable font marker), emit a warning for Word workflows.

### Best Practices

1. **Prefer static fonts in automated document pipelines** — variable fonts are a web/design-tool technology with inconsistent Office support
2. **Document font substitution chains** — for each brand, specify a primary font and a known-good fallback
3. **Treat font installation as a testable step** — verify the expected family and weight are available to the rendering engine, not just installed

## Related

- [COVER token architecture](../logic-errors/cover-token-architecture-prose-vs-code.md) — the other half of the v2.2.0 RE/MAX brand fix
- [Table cell text clipping](docx-table-cell-text-clipping.md) — another Word rendering vs docx-js issue
- [Multi-brand architecture refactor](../integration-issues/refactor-single-brand-to-pluggable-multi-brand-architecture.md) — documents the original Montserrat font decision
