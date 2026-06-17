# Magma Inc. - the magmainc.ca identity for documents

Magma Inc.'s own brand, from the kit at magmainc.ca: one typeface (Montserrat), Bridge Blue navy as the signature, two reds chosen by background, cool near-white surfaces (Page Cream, Stone). The feel is a precision instrument for serious people: confident, calm, restrained.

This shares its palette family with the `jasminahomes` theme (both descend from the RE/MAX Bridge colours), but Magma is its own identity: a single typeface instead of Poppins + Georgia, cooler neutrals, the radar logo, and the two-reds-by-surface rule.

---

## BRAND Tokens

```javascript
const BRAND = {
  dark:       "23211E",   // body text (Charcoal, warm near-black)
  navy:       "0C2749",   // Bridge Blue: headings, table header, cover bar, the rare dark emphasis band
  light:      "F8FAFC",   // Page Cream: page tone / subtle section backgrounds
  midGray:    "6B7785",   // captions, metadata (derived cool slate, not a core brand colour)
  lightGray:  "EDF2F5",   // Stone: table zebra rows, dividers, card borders
  accent:     "AA1120",   // Bridge Red (deep): emphasis ON LIGHT - eyebrow kicker, callout label, the one CTA
  accentDark: "E2412F",   // Signal Red (bright): red ON NAVY/dark surfaces only
  secondary:  "A3D4F2",   // Sky: soft highlights, info-box backgrounds (used lightly)
  heading:    "Montserrat", // ONE typeface, all weights. 700 headings, 600 labels, 400 body.
  body:       "Montserrat", // same family; hierarchy comes from weight, not a second face.
};
```

### Default Contact Info

```javascript
const DEFAULTS = {
  name: "Daniel Zivkovic", title: "AI Architect", company: "Magma Inc.",
  phone: "416-569-4616", email: "daniel@magmainc.ca"
};
```

### Cover Page Tokens

```javascript
const COVER = {
  barColor: BRAND.navy,          // navy top bar (the signature; one navy beat on the cover)
  categoryColor: BRAND.accent,   // red eyebrow/category (Bridge Red on the light cover)
  categorySpacing: 0,
  categoryCaps: true,            // small tracked caps read as a kicker
  titleSpacing: 0,
};
```

---

## brandStyles

```javascript
const brandStyles = {
  default: {
    document: { run: { font: BRAND.body, size: 22, color: BRAND.dark } }  // 11pt Montserrat Regular, Charcoal
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 48, bold: true, color: BRAND.navy },  // navy headings
      paragraph: {
        spacing: { before: 480, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.lightGray, space: 6 } }, // quiet stone rule, not red
        outlineLevel: 0
      }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 32, bold: true, color: BRAND.navy },
      paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 22, bold: true, color: BRAND.dark },
      paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 2 }
    },
    {
      id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.heading, size: 16, color: BRAND.midGray },
      paragraph: { spacing: { before: 40, after: 160 } }
    },
    {
      id: "Callout", name: "Callout", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.body, size: 22, color: BRAND.dark },
      paragraph: {
        spacing: { before: 120, after: 120 },
        indent: { left: 720 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: BRAND.accent, space: 12 } }  // Bridge Red left border (a red spice)
      }
    }
  ]
};
```

Heading weight is Montserrat Bold (700); the `docx` library renders `bold: true` against the installed Bold cut.

---

## Numbering Config

Bullet dots are **navy** (structural), not red, to keep red as a spice.

```javascript
numbering: {
  config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } },
        run: { font: BRAND.body, color: BRAND.navy } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
  ]
}
```

---

## Design Principles

- **Two reds, by surface.** Bridge Red `AA1120` on light (almost everything in a doc), Signal Red `E2412F` only where red sits on navy (a navy table header label, a navy panel). Never `AA1120` on `0C2749`.
- **Navy is rare emphasis.** Headings, table headers, the cover bar, and at most one full navy panel per page (a key callout or authority statement). Never wall-to-wall navy.
- **Red is a spice.** Roughly two reds per page: the eyebrow/category kicker and one callout label or CTA. Not bullets, not headings.
- **One typeface.** Montserrat for everything; hierarchy by weight (700 / 600 / 400). Keep body leading generous so all-sans long-form stays comfortable.
- **Stone is the quiet alternator.** Use `lightGray` (Stone) for zebra rows, dividers, and section bands, not a hard line.
- **Tables earn their place.** Genuine comparisons only. Dense table data at 9.5pt, airy prose at 11pt.

---

## Color Reference

| Role | Hex | Use |
|------|-----|-----|
| Charcoal (dark) | `23211E` | Body text |
| **Bridge Blue (navy)** | `0C2749` | Headings, table header, cover bar, rare navy band |
| Page Cream (light) | `F8FAFC` | Page tone, section backgrounds |
| Mid Gray | `6B7785` | Captions, metadata |
| Stone (lightGray) | `EDF2F5` | Zebra rows, dividers, card borders |
| **Bridge Red (accent)** | `AA1120` | Emphasis on light: kicker, callout label, CTA |
| Signal Red | `E2412F` | Red on navy/dark only |
| Sky (secondary) | `A3D4F2` | Soft highlights, info boxes |

## Typography Reference

| Element | Weight | Size (pt) | docx units |
|---------|--------|-----------|------------|
| Cover title | Montserrat Bold 700 | 36 | 72 |
| Cover category | Montserrat Bold 700 | 22 | 44 |
| H1 | Montserrat Bold 700 | 24 | 48 |
| H2 | Montserrat Bold 700 | 16 | 32 |
| H3 | Montserrat Bold 700 | 11 | 22 |
| Body | Montserrat Regular 400 | 11 | 22 |
| Table data | Montserrat Regular 400 | 9.5 | 19 |
| Table header | Montserrat Bold 700 | 9 | 18 |
| Caption | Montserrat 400 | 8 | 16 |
| Footer | Montserrat 400 | 8 | 16 |

Brand fallback when Montserrat is genuinely absent: a system sans (`system-ui`), never a serif and never Times. (Word will substitute its default if no sans is mapped; install Montserrat to avoid this.)

---

## Document Archetypes

**Report / Playbook** - Cover with navy top bar + red category kicker + navy title + date. H1 per chapter (navy, quiet stone rule), H2 per topic. Montserrat 11pt body. Callouts with a Bridge Red left border.

**Brief / Memo** - No cover. Title is first H1. Header with document title + navy page number. 2-3 levels.

**Executive Summary** - One page. Large navy H1, callout blocks for the key points, at most one navy panel.

---

## Logo

**File:** `brands/magma-logo.png` (the white/positive square lockup: navy word + bridge-red arcs, for light backgrounds).

Off by default; include when the user asks or for a cover/signature block. Square lockup, so it suits the cover or a signature block; display at roughly 80x80 (cover) or 60x60 (signature). On a navy panel, use the dark/reversed lockup instead (in the `pptx` brand folder, or request it). Never recolor, stretch, rotate, or rebuild the wordmark; use the supplied file.

---

## Font Requirements

This brand requires **Montserrat** (headings and body). It is free to install and embed under the SIL Open Font License 1.1 (the kit bundles `Montserrat-VariableFont_wght.ttf` and the italic, plus `OFL.txt`).

- **Windows / Mac:** install from the kit's `fonts/` folder, or from [Google Fonts](https://fonts.google.com/specimen/Montserrat). Restart Word.
- **Linux:** `mkdir -p ~/.fonts && cp Montserrat-*VariableFont*.ttf ~/.fonts/ && fc-cache -f`

A variable font carries all weights in one file. If an older Word or a print RIP does not understand variable fonts, install the static cuts (Regular, Medium, SemiBold, Bold) from Google Fonts instead. If Montserrat is missing, Word substitutes its default sans and the document loses its character.
