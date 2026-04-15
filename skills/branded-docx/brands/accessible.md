# Accessible — High-Readability Theme for Glasses Wearers

A WCAG-informed brand system optimised for readability across vision abilities: deep blue accent, near-black text, white page, Arial headings, Verdana body. Every color pair exceeds WCAG AA contrast (4.5:1 for body text, 3:1 for large text). No meaning conveyed by color alone.

> **Calibration note.** This theme is tuned for adult readers with reading glasses (age-related presbyopia) — comparable to the iPhone "Medium" text size. It is **not** a large-print theme for low-vision or visually impaired readers. If a reader genuinely cannot read standard print, build a dedicated 16–18pt large-print theme — do not inflate the sizes below. The sizes here have been print-tested and calibrated; both oversizing (wastes paper, titles look shouty) and undersizing (strains glasses-corrected vision) break the theme.

---

## BRAND Tokens

```javascript
const BRAND = {
  dark:       "1B1B1F",   // near-black, softer than pure #000 but still AAA on white
  light:      "FFFFFF",   // pure white page — maximum contrast base
  midGray:    "545467",   // metadata, captions (7.2:1 on white — AAA)
  lightGray:  "E6E6EF",   // table zebra rows, subtle dividers
  accent:     "005EA6",   // deep blue — 7.1:1 on white (AAA), colorblind-safe
  secondary:  "7B5EA7",   // muted purple — distinguishable from blue under all color-vision types
  tertiary:   "2E7D32",   // forest green — positive/success indicators
  heading:    "Arial",    // universal sans-serif, every OS
  body:       "Verdana",  // wider letterforms, designed for on-screen and print readability
};
```

### Brand-Neutral — No Defaults

```javascript
// This theme is deliberately brand-neutral:
// no logo, no signature block, no default contact info.
// If a signature block is requested, ask the user for the details.
const logoDefault = "off";
```

### Cover Page Tokens

```javascript
const COVER = {
  barColor: BRAND.accent,          // blue bar at top
  categoryColor: BRAND.accent,     // blue category text
  categorySpacing: 40,             // slight letter spacing for category
  categoryCaps: true,              // uppercase category for structure
  titleSpacing: 0,                 // no extra title spacing
};
```

---

## brandStyles

Body text is 12pt (size 24) — one point larger than typical — for improved readability. Line spacing uses `line: 276` (1.15x) for comfortable reading without wasting vertical space.

```javascript
const brandStyles = {
  default: {
    document: { run: { font: BRAND.body, size: 24, color: BRAND.dark } },
    paragraph: { spacing: { line: 276 } }
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 48, bold: true, color: BRAND.accent },
      paragraph: {
        spacing: { before: 480, after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.accent, space: 8 } },
        outlineLevel: 0
      }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 32, bold: true, color: BRAND.dark },
      paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 24, bold: true, color: BRAND.midGray },
      paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 2 }
    },
    {
      id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.heading, size: 18, color: BRAND.midGray, italics: false },
      paragraph: { spacing: { before: 40, after: 160 } }
    },
    {
      id: "Callout", name: "Callout", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.body, size: 24, color: BRAND.dark },
      paragraph: {
        spacing: { before: 120, after: 120 },
        indent: { left: 720 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: BRAND.accent, space: 12 } }
      }
    }
  ]
};
```

---

## Numbering Config

```javascript
numbering: {
  config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } },
        run: { font: BRAND.body, color: BRAND.accent } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
  ]
}
```

---

## Design Principles

- **Contrast is king.** Every text element exceeds WCAG AA minimum. Body text on white exceeds AAA (7:1+). Never rely on color alone to convey meaning.
- **Verdana for reading.** Its wide letterforms, open counters and generous spacing were designed for legibility. Use for all body text, table data, and extended reading.
- **Arial for structure.** Clean and universally available. Headings, labels, metadata.
- **12pt body baseline.** One point above convention pays large dividends for sustained reading comfort.
- **Generous spacing.** 1.15x line height, ample paragraph spacing. Let content breathe.
- **Accent is structural.** Deep blue marks H1 headings, callout borders, bullet dots, and the cover bar. Nothing more. If blue is everywhere, the structure dissolves.
- **Tables earn their place.** Table data at 10pt Verdana (size 20) for density; headers at 9.5pt Arial Bold. Still larger than most brand systems.

---

## Color Reference

| Role | Hex | Contrast on White | WCAG Level | Use |
|------|-----|-------------------|------------|-----|
| Dark | `1B1B1F` | 17.4:1 | AAA | All body text |
| Mid Gray | `545467` | 7.2:1 | AAA | Captions, metadata |
| Light Gray | `E6E6EF` | 1.3:1 | — | Table zebra, dividers (decorative only) |
| **Accent** | `005EA6` | 7.1:1 | AAA | H1, callout labels, accent bars |
| Accent tint | `EBF3FA` | — | — | Callout backgrounds (decorative) |
| Secondary | `7B5EA7` | 5.4:1 | AA | Data highlights |
| Tertiary | `2E7D32` | 5.9:1 | AA+ | Positive indicators |
| Warning tint | `FFF8E1` | — | — | Warning callout backgrounds |

## Typography Reference

| Element | Font | Size (pt) | docx units |
|---------|------|-----------|------------|
| Cover title | Arial Bold | 32 | 64 |
| Cover category | Arial Bold | 20 | 40 |
| H1 | Arial Bold | 24 | 48 |
| H2 | Arial Bold | 16 | 32 |
| H3 | Arial Bold | 12 | 24 |
| Body | Verdana | 12 | 24 |
| Table data | Verdana | 10 | 20 |
| Table header | Arial Bold | 9.5 | 19 |
| Caption | Arial | 9 | 18 |
| Footer | Arial | 8.5 | 17 |

---

## Spacing Rhythm

Multiples of 120 DXA:
- Tight: 80 / 80
- Normal: 120 / 120
- Loose (after headings): 200 after
- Section gap: 360–480 before major headings

---

## Document Archetypes

**Report / Transcript** — Cover page with accent top bar + category + title + date. H1 per major section (blue, bottom border), H2 per subsection. Verdana 12pt body. Callouts with left blue border + faint tint.

**Brief / Memo** — No cover. Title is first H1. Header line + page number. 2–3 heading levels max.

---

## Common Mistakes

Guardrails against drift in either direction — this theme fails when oversized *or* undersized.

- **Don't push body above 12pt (sz 24).** Wastes paper and toner, and titles feel shouty once everything scales up with it.
- **Don't push H1 above 24pt (sz 48).** The previous version of this theme had 22–26pt headings that the user had to shrink manually in Word. Don't regress.
- **Don't push the cover title above 32pt (sz 64).** 36pt was the specific element that triggered manual reduction in the prior version.
- **Don't drop body below 12pt.** This is the comfort floor for glasses-corrected vision — smaller defeats the purpose of the theme.
- **Don't add a `DEFAULTS` contact block.** This theme is deliberately brand-neutral.
- **Don't add horizontal divider lines (`<hr>`, `---`) between sections.** H1's blue bottom border is the separator. Dividers at this body size become thick visual barriers that waste vertical space.
- **Don't use the saturated red/orange from older brand variants.** Those print muddy on home inkjets and bleed — the reason this palette exists.
- **Don't reduce margins to fit more text.** White space carries comfort; cramped pages fight the reader.
- **Don't use light gray for body text.** Gray is for metadata and captions only.

---

## Print Tips

Calibrated to this theme's blue palette — do not substitute old cream-paper advice from other brand themes.

- **Keep Word page background white.** Never set a page color — home printers spray a fine toner dusting over every page, triple the cost, and the paper warps as it dries.
- **Use bright white paper, not cream.** Blue accents (`#005EA6`) pop on white; cream dulls them. The palette was chosen around white stock.
- **28–32lb paper weight** (105–120gsm) if the reader handles the document often. Heavier paper is easier to grip and less flimsy for older hands.
- **Single-sided printing.** No show-through, pages lie flat, easier to read and to hold open.
- **Binding:** spiral or large binder clips beat staples for documents the reader keeps open on a table.
- **Print at 100% — never "Fit to page".** Word silently shrinks text when fitting, which quietly defeats the entire sizing calibration.

---

## Font Requirements

Both **Arial** and **Verdana** are pre-installed on Windows, macOS, and most Linux distributions. No additional font installation required — this is intentional for an accessibility-first theme.
