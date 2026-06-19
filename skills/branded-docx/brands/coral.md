# Coral — Anthropic Visual Identity

Anthropic's brand system: coral accent, near-black text, off-white tone, Poppins headings, Georgia body. Derived from Anthropic's official brand guidelines, Geist agency case study, and published PDFs.

---

## BRAND Tokens

```javascript
const BRAND = {
  dark:       "141413",   // primary text, dark backgrounds
  light:      "FAF9F5",   // page tone, subtle section backgrounds
  midGray:    "B0AEA5",   // captions, metadata, secondary text
  lightGray:  "E8E6DC",   // table zebra rows, subtle dividers
  accent:     "CC0000",   // primary accent — warm red (originally D97757 coral)
  secondary:  "6A9BCC",   // secondary accent — blue
  tertiary:   "788C5D",   // tertiary accent — green
  heading:    "Poppins",  // headings, labels, captions
  body:       "Georgia",  // body paragraphs, quotes, long-form
};
```

### Default Contact Info

These are example defaults for the repo maintainer. Replace with your own or override at generation time.

```javascript
const DEFAULTS = {
  name: "Daniel Zivkovic",
  title: "Consultant",
  phone: "416-569-4616",
  email: "daniel@magmainc.ca"
};
```

### Cover Page Tokens

```javascript
const COVER = {
  barColor: BRAND.accent,          // coral bar at top
  categoryColor: BRAND.accent,     // coral category text
  categorySpacing: 0,              // no extra spacing
  categoryCaps: false,             // normal case
  titleSpacing: 0,                 // no extra spacing
};
```

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
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.accent, space: 6 } },
        outlineLevel: 0
      }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 36, bold: true, color: BRAND.dark },
      paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 22, bold: true, color: BRAND.midGray },
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

- **White space first.** Generous `spacing.before` and `spacing.after` on every element. Never crowd content.
- **Accent is precious.** Use coral only for H1 headings, key callout labels, and accent bars. One or two coral elements per page maximum. If everything is coral, nothing is.
- **One serif, one sans.** Georgia for reading, Poppins for structure. Never mix within a paragraph.
- **Tables earn their place.** If it fits in prose, write prose. Tables for genuine comparisons only.
- **Dense tables, airy prose.** Use 9.5pt Georgia (size 19) for table data cells — tighter than body text, giving tables a professional financial-document density. Body prose stays at 11pt.
- **Tonal color.** The secondary (blue) and tertiary (green) accents are available for tonal meaning. Use tertiary for benefits or positive findings, secondary for neutral data highlights, accent for emphasis or caution. This is a creative judgment — adapt the palette to the document's emotional context.

---

## Color Reference

| Role | Hex | Use |
|------|-----|-----|
| Dark | `141413` | All body text, strong backgrounds |
| Light | `FAF9F5` | Page tone, section backgrounds |
| Mid Gray | `B0AEA5` | Captions, metadata, subdued text |
| Light Gray | `E8E6DC` | Table zebra rows, subtle dividers |
| **Accent** | `CC0000` | H1 headings, callout labels, accent bars (originally `D97757` coral) |
| Accent tint | `FFF5F5` | Faint warm background for emphasis callouts (originally `FFF5F0`) |
| Secondary | `6A9BCC` | Secondary accents, data highlights |
| Tertiary | `788C5D` | Tertiary accents, positive indicators |
| Success tint | `F5F8F0` | Faint sage background for positive callouts |

## Typography Reference

| Element | Font | Fallback | Size (pt) | docx units |
|---------|------|----------|-----------|------------|
| Cover title | Poppins Bold | Arial | 36 | 72 |
| Cover category | Poppins Bold | Arial | 22 | 44 |
| H1 | Poppins Bold | Arial | 26 | 52 |
| H2 | Poppins Bold | Arial | 18 | 36 |
| H3 | Poppins Bold | Arial | 11 | 22 |
| Body | Georgia | Times New Roman | 11 | 22 |
| Table data | Georgia | Times New Roman | 9.5 | 19 |
| Table header | Poppins Bold | Arial | 9 | 18 |
| Label | Poppins | Arial | 8.5 | 17 |
| Caption | Poppins | Arial | 9 | 18 |
| Fine print | Georgia Italic | Times New Roman | 7.5 | 15 |
| Footer | Poppins | Arial | 8 | 16 |

---

## Spacing Rhythm

Use multiples of 120 DXA (~1/12 inch):

- Tight: 80 before, 80 after
- Normal: 120 before, 120 after
- Loose (after headings): 160 after
- Section gap: 360-480 before major headings

---

## Document Archetypes

**Report / Playbook** — Cover page with large title + accent top bar + subtitle + date. H1 per chapter (accent, bottom border), H2 per topic. Georgia 11pt body. Callouts with left accent border.

**Brief / Memo** — No cover page. Title is first H1. Header with document title + page number. 2-3 levels max.

**Executive Summary** — One page. Large H1, no chapter structure. Callout blocks for key points.

---

## Common Mistakes

- Using accent color on more than 20% of text elements (it loses its power)
- Table borders thicker than 1pt (looks aggressive)
- Using Poppins for body text (it is a display font, not a reading font)
- Forgetting spacing before H1 (always breathe before section starts)
- Page backgrounds (Word renders them unreliably across platforms)

---

## Logo

**File:** `brands/coral-logo.png` (bundled, 497x502px, transparent background)

A coral starburst mark matching the brand accent color. This is a placeholder — replace with your own logo or remove entirely.

The logo is optional and off by default. Include only when the user explicitly requests a logo or signature block. Typical placement: bottom-left of cover page, or alongside a signature block at end of document. Square aspect ratio — display at roughly 80x80 for cover use, 60x60 for signature use.

---

## Font Requirements

This brand requires **Poppins** (headings) and **Georgia** (body). Read [`references/font-fidelity.md`](../references/font-fidelity.md) for the full font doctrine; the brand-specific notes follow.

**Georgia on a headless box.** Georgia is built into Windows and macOS, but it is a proprietary Microsoft font and is absent from Linux containers (CI, the claude.ai sandbox). Rendered to PDF there, Georgia silently substitutes to a default serif and the body never looks like Georgia. Substitute **Gelasio**, the metric-compatible open replacement: it has Georgia's metrics, so line breaks and pagination are unchanged (the measurements live in the [font-fidelity reference](../references/font-fidelity.md)). Do not use Lora or another look-alike; only a metric-compatible face keeps pagination identical. One command (instances static cuts, installs, aliases Georgia, fails loud if it cannot):

```bash
python scripts/setup/font_preflight.py --family Georgia --substitute Gelasio \
  --source-url "https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf" \
  --weights 400,700 --alias
```

Poppins must be installed:

- **Windows:** Download from [Google Fonts](https://fonts.google.com/specimen/Poppins), extract, select all .ttf files, right-click > "Install for all users". Restart Word.
- **Mac:** Download from Google Fonts, unzip, double-click each .ttf, click "Install Font". Restart Word.
- **Linux:** `mkdir -p ~/.fonts && cd ~/.fonts && for w in Regular Bold SemiBold Italic BoldItalic; do curl -Lo "Poppins-${w}.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-${w}.ttf"; done && fc-cache -fv`

If Poppins is missing, Word silently falls back to Arial. The document opens fine but headings lose their character.

**Before sending a coral document outside your machine,** embed the fonts or export to PDF (PDF embeds and subsets automatically) so a recipient without Poppins or Georgia still sees the design. See the font-fidelity reference, "Distribution".
