# REMAX — RE/MAX Real Estate Brand Identity

RE/MAX brand system: red-white-blue color palette, bold sans-serif typography, navy accent, Montserrat headings, Arial body. Derived from the 2025 Brand Evolution: Brand Standards U.S. & Canada supplement.

---

## BRAND Tokens

```javascript
const BRAND = {
  dark:       "000000",   // black — primary text, dark backgrounds
  light:      "FFFFFF",   // white — page tone (print-friendly, saves toner)
  midGray:    "232323",   // dark charcoal — captions, metadata, secondary text
  lightGray:  "F0F0F0",   // light gray — table zebra rows, subtle dividers
  accent:     "0C2749",   // bridge blue (deep navy) — primary accent
  secondary:  "AA1120",   // bridge red — secondary accent, action items
  tertiary:   "A3D4F2",   // sky blue — tertiary accent, soft highlights
  heading:    "Montserrat", // headings, labels, captions (free Google Font)
  body:       "Arial",    // body paragraphs, long-form text
};
```

### Default Contact Info

These are example defaults for the repo maintainer. Replace with your own or override at generation time.

```javascript
const DEFAULTS = {
  name: "Jasmina Zivkovic",
  title: "Sales Representative",
  phone: "647-273-5318",
  email: "info@jasminahomes.ca",
  company: "RE/MAX Your Community Realty Inc."
};
```

### Why Bridge colors, not Primary?

RE/MAX Primary Red (`#FF1200`) and Primary Blue (`#0043FF`) are designed for signage and digital screens at high saturation. For printed and Word documents, the Bridge gradations (`#AA1120`, `#0C2749`) provide better readability and a more professional appearance. The brand guide explicitly states these gradations "help create contrast among the Brand Colors."

### Extended palette (for reference, not in BRAND tokens)

| Name | Hex | Use |
| ---- | --- | --- |
| Primary Red | `FF1200` | Signage, high-impact digital |
| Primary Blue | `0043FF` | Signage, high-impact digital |
| Bridge Red | `AA1120` | Document accent bars, callouts |
| Bridge Blue | `0C2749` | Headings, table headers, cover elements |
| Dark Red | `660000` | Hover states, deep emphasis |
| Dark Blue | `000E35` | Deep backgrounds |
| Sky Blue | `A3D4F2` | Soft highlights, tertiary accent |
| Cream | `F7F5EE` | Subtle accents (not used as page bg — white for print) |
| Dark Charcoal | `232323` | Secondary text |
| White | `FFFFFF` | White text on dark backgrounds |

---

## brandStyles

```javascript
const brandStyles = {
  default: {
    document: { run: { font: BRAND.body, size: 22, color: BRAND.dark } }
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 52, bold: true, color: BRAND.accent },
      paragraph: {
        spacing: { before: 480, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.secondary, space: 6 } },
        outlineLevel: 0
      }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 36, bold: true, color: BRAND.accent },
      paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 26, bold: true, color: BRAND.dark },
      paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 2 }
    },
    {
      id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.heading, size: 16, color: BRAND.midGray, italics: false },
      paragraph: { spacing: { before: 40, after: 160 } }
    },
    {
      id: "Callout", name: "Callout", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.body, size: 22, color: BRAND.dark },
      paragraph: {
        spacing: { before: 120, after: 120 },
        indent: { left: 720 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: BRAND.secondary, space: 12 } }
      }
    }
  ]
};
```

### Brand-specific style notes

- H1 uses navy heading with a **red** bottom border (not accent) — the two-color interplay is core to RE/MAX identity
- Callout blocks use red left border (secondary) to echo the "action bar" pattern from RE/MAX signage
- H2 uses navy (accent) without a border — cleaner hierarchy
- H3 uses black — third level fades to neutral

---

## Numbering Config

```javascript
numbering: {
  config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } },
        run: { font: BRAND.body, color: BRAND.secondary } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
  ]
}
```

---

## Design Principles

- **Bold and direct.** RE/MAX is not subtle — use strong contrasts, all-caps headings where appropriate. Navy headers on white feel authoritative.
- **Red is for action.** Use Bridge Red only for callout labels, accent bars, and emphasis elements. One or two red elements per page maximum. Red on red backgrounds is never permitted.
- **One sans-serif family.** Montserrat for structure, Arial for reading. Both are clean sans-serifs that pair naturally. Never use serif fonts in RE/MAX documents.
- **White space matters.** The brand guide emphasizes clean, uncluttered layouts. Generous spacing between sections.

---

## Color Reference

| Role | Hex | Use |
| ---- | --- | --- |
| Dark | `000000` | All body text, strong backgrounds |
| Light | `FFFFFF` | Page tone, white background (print-friendly) |
| Dark Charcoal | `232323` | Captions, metadata, subdued text |
| Light Gray | `F0F0F0` | Table zebra rows, subtle dividers |
| **Accent** | `0C2749` | H1/H2 headings, table headers, cover elements |
| **Secondary** | `AA1120` | Action bars, callout labels, bullet accents |
| Tertiary | `A3D4F2` | Soft highlights, info boxes |

## Typography Reference

| Element | Font | Fallback | Size (pt) | docx units |
| ------- | ---- | -------- | --------- | ---------- |
| Cover title | Montserrat Bold | Arial Bold | 36 | 72 |
| H1 | Montserrat Bold | Arial Bold | 26 | 52 |
| H2 | Montserrat Bold | Arial Bold | 18 | 36 |
| H3 | Montserrat Bold | Arial Bold | 13 | 26 |
| Body | Arial | Calibri | 11 | 22 |
| Caption | Montserrat | Arial | 9 | 18 |
| Footer | Montserrat | Arial | 8 | 16 |

---

## Spacing Rhythm

Use multiples of 120 DXA (~1/12 inch):

- Tight: 80 before, 80 after
- Normal: 120 before, 120 after
- Loose (after headings): 160 after
- Section gap: 360-480 before major headings

---

## Document Archetypes

**Market Report / Listing Presentation** — Cover page with large navy title + red accent top bar + subtitle + date. H1 per section (navy, red bottom border), H2 per topic. Arial 11pt body. Callouts with left red border for key statistics.

**Property Brief / CMA** — No cover page. Title is first H1. Header with document title + page number. 2-3 levels max. Data-heavy with branded tables.

**Agent Marketing Flyer** — Bold cover treatment. Large headings, minimal body text. Red accent bars for calls-to-action.

---

## Common Mistakes

- Using Primary Red/Blue instead of Bridge colors in documents (too vivid for print)
- Using Gotham without a license (use Montserrat instead — it's free and 85% match)
- Mixing serif fonts into RE/MAX documents (brand is strictly sans-serif)
- Using red for body text or large text blocks (red is for accents only)
- Overcrowding — RE/MAX brand emphasizes clean, spacious layouts
- Using the REMAX logotype as text (always use the official logo image, never type "REMAX" as styled text)

---

## Logo

**File:** `brands/remax-logo.png` (bundled, 400x245px, transparent background)

The logo is optional — use it alongside agent signature blocks. Typical placement: end of document or cover page, logo to the left of contact lines.

```javascript
// Signature block: logo left, contact info right (borderless table)
function signatureWithLogo(name, title, phone, email) {
  const logoData = fs.readFileSync(path.join(__dirname, "brands", "remax-logo.png"));
  const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

  const contactLines = [
    new Paragraph({
      spacing: { before: 0, after: 40 },
      children: [new TextRun({ text: name, font: BRAND.heading, size: 22, bold: true, color: BRAND.dark })]
    }),
    title ? new Paragraph({
      spacing: { before: 0, after: 40 },
      children: [new TextRun({ text: title, font: BRAND.body, size: 20, color: BRAND.midGray })]
    }) : null,
    new Paragraph({
      spacing: { before: 0, after: 40 },
      children: [new TextRun({ text: phone, font: BRAND.body, size: 20, color: BRAND.dark })]
    }),
    email ? new Paragraph({
      spacing: { before: 0, after: 0 },
      children: [new ExternalHyperlink({
        children: [new TextRun({ text: email, style: "Hyperlink", font: BRAND.body, size: 20 })],
        link: `mailto:${email}`
      })]
    }) : null,
  ].filter(Boolean);

  return new Table({
    width: { size: 5000, type: WidthType.DXA },
    columnWidths: [1800, 3200],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders: noBorders, width: { size: 1800, type: WidthType.DXA },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new ImageRun({
              type: "png", data: logoData,
              transformation: { width: 120, height: 74 },
              altText: { title: "REMAX Logo", description: "REMAX Your Community Realty", name: "remax-logo" }
            })]
          })]
        }),
        new TableCell({
          borders: noBorders, width: { size: 3200, type: WidthType.DXA },
          verticalAlign: VerticalAlign.CENTER,
          children: contactLines
        })
      ]
    })]
  });
}
```

All sizes are starting points — the user can resize the logo and adjust column widths directly in Word.

---

## Font Requirements

This brand requires **Montserrat** (headings) and **Arial** (body).

Arial is built into Windows, macOS, and most Linux distributions. Montserrat is a free Google Font that closely matches Gotham (the official RE/MAX typeface) and works across both MS Word and Google Docs:

- **Google Docs:** Already available in the font picker — just select "Montserrat".
- **Windows:** Download from [Google Fonts](https://fonts.google.com/specimen/Montserrat), extract, select all .ttf files, right-click > "Install for all users". Restart Word.
- **macOS:** Download from Google Fonts, unzip, double-click each .ttf, click "Install Font". Restart Word.
- **Linux:** `sudo apt install fonts-montserrat` or download manually from Google Fonts.

If Montserrat is missing, Word silently falls back to Arial. The document opens fine but headings lose their character. If you have a Gotham license, change the `heading` token back to `"Gotham"` for an exact brand match.
