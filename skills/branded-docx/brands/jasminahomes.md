# Jasmina Homes — PropTech Luxury Brand Identity

A hybrid brand combining the modern, data-dense layout architecture of Anthropic's Coral system (Poppins headings, Georgia body, tight spacing rhythm) with the authoritative luxury color palette of RE/MAX Bridge colors (deep navy, bridge red, warm neutrals). The result reads like a high-end analytical real estate practice — dense like a tech company's reports, colored like a luxury property brand.

---

## BRAND Tokens

```javascript
const BRAND = {
  dark:       "232323",   // dark charcoal — softer than pure black, premium feel
  light:      "FFFFFF",   // pure white — no toner trap (use cream paper for physical warmth)
  midGray:    "8A8780",   // warm gray — captions, metadata, secondary text
  lightGray:  "EDEAE0",   // warm cream-gray — table zebra rows, subtle dividers
  accent:     "0C2749",   // bridge blue (deep navy) — H1/H2 headings, structural elements
  secondary:  "AA1120",   // bridge red — action bars, borders, emphasis
  tertiary:   "A3D4F2",   // sky blue — soft highlights, tertiary accent
  heading:    "Poppins",  // headings, labels, captions (geometric sans — modern tech feel)
  body:       "Georgia",  // body paragraphs, quotes, long-form (editorial serif — luxury feel)
};
```

### Default Contact Info

These are defaults for the brand owner. Override at generation time as needed.

```javascript
const DEFAULTS = {
  name: "Jasmina Zivkovic",
  title: "Sales Representative",
  phone: "647-273-5318",
  email: "info@jasminahomes.ca",
  company: "RE/MAX Your Community Realty Inc."
};
```

### Cover Page Tokens

```javascript
const COVER = {
  barColor: BRAND.secondary,       // red bar at top (RE/MAX signage heritage)
  categoryColor: BRAND.secondary,  // red category text
  categorySpacing: 0,              // no extra spacing — modern, tech-forward
  categoryCaps: false,             // normal case — clean and contemporary
  titleSpacing: 0,                 // no extra spacing — dense, analytical feel
};
```

### Why this hybrid works

The Poppins + Georgia combination is the "PropTech Luxury" move. Poppins (geometric sans-serif) gives headings a modern, data-driven authority — the same feeling you get reading an AI company's research paper. Georgia (editorial serif) gives body text the rich, trustworthy weight of a Wall Street Journal feature or a wealth management report. Mapped onto RE/MAX's navy and red Bridge palette, the overall impression is: "This agent runs her practice like a tech company, but her brand commands the room like a legacy real estate giant."

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
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: BRAND.secondary, space: 12 } }
      }
    }
  ]
};
```

### Brand-specific style notes

- H1 uses navy heading with a **red** bottom border — the RE/MAX two-color interplay (accent structure, secondary emphasis) adapted from the original RE/MAX brand
- Callout blocks use red left border (secondary) to echo the "action bar" pattern from RE/MAX signage
- H2 uses navy (accent) without a border — cleaner hierarchy
- H3 uses warm gray — third level fades to neutral, reducing visual weight
- **No letter spacing** on headings — unlike the full RE/MAX brand, this hybrid deliberately omits the `characterSpacing: 40` luxury tracking in favor of Coral's tighter, more data-dense headings

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

- **Dense and authoritative.** This brand merges Coral's analytical density with RE/MAX's commanding color presence. Pack information tightly — the typography and spacing handle the hierarchy.
- **Red is for action.** Use Bridge Red only for callout borders, accent bars, bullet markers, and emphasis elements. One or two red elements per page maximum. Red on red backgrounds is never permitted.
- **One serif, one sans.** Georgia for reading, Poppins for structure. Never mix within a paragraph. This contrast is the brand's signature — it signals "modern analysis meets editorial authority."
- **White space first.** Generous `spacing.before` and `spacing.after` on every element. Never crowd content.
- **Dense tables, airy prose.** Use 9.5pt Georgia (size 19) for table data cells — tighter than body text, giving tables professional financial-document density. Body prose stays at 11pt. Table cell top/bottom margins should be ~48 DXA (slightly more breathable than Coral's raw density).
- **Tonal color.** Navy (accent) for authority and structure, red (secondary) for action and emphasis, sky blue (tertiary) for positive findings or soft highlights. Use the luxury-adjusted callout tints for background shading — never saturated colors.

---

## Color Reference

| Role | Hex | Use |
| ---- | --- | --- |
| Dark | `232323` | All body text, strong backgrounds (dark charcoal, not pure black) |
| Light | `FFFFFF` | Page tone, white background (print on cream paper for warmth) |
| Mid Gray | `8A8780` | Captions, metadata, subdued text |
| Light Gray | `EDEAE0` | Table zebra rows, subtle dividers (warm cream-gray) |
| **Accent** | `0C2749` | H1/H2 headings, table headers, cover elements (Bridge Blue) |
| **Secondary** | `AA1120` | Action bars, callout borders, bullet accents (Bridge Red) |
| Tertiary | `A3D4F2` | Soft highlights, info boxes |
| Info tint | `F0F2F8` | Faint ice blue background for info/emphasis callouts |
| Success tint | `E8F0EA` | Faint sage green background for positive/success callouts |
| Alert tint | `FDF5F5` | Faint blush/rose background for award/caution callouts |

### Why these tints?

Standard highlight colors (bright green, neon yellow, vivid red) clash horribly with the navy/red palette and look cheap. These tints are desaturated and gray-shifted — they read as "luxury stationery" rather than "colored highlighter." Each tint uses its parent color as a base but is washed out with white to the point where it barely registers as a color — just enough to create visual separation without fighting the Bridge palette.

---

## Typography Reference

| Element | Font | Fallback | Size (pt) | docx units |
| ------- | ---- | -------- | --------- | ---------- |
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
- Table cell margins: ~48 DXA top/bottom (20% more breathable than Coral's baseline)

---

## Document Archetypes

**Market Report / Listing Presentation** — Cover page with large navy title + red accent top bar + subtitle + date. H1 per section (navy, red bottom border), H2 per topic. Georgia 11pt body. Callouts with left red border for key statistics. Dense tables for comparable sales data.

**Property Brief / CMA** — No cover page. Title is first H1. Header with document title + page number. 2-3 levels max. Data-heavy with branded tables. Use sage tint for positive highlights (strong appreciation, above-market metrics).

**Executive Summary** — One page. Large H1, no chapter structure. Callout blocks for key points. Use ice blue tint for analytical emphasis.

---

## Common Mistakes

- Using saturated highlight colors instead of the luxury-adjusted tints (they clash with navy/red)
- Using Metropolis, Montserrat, or Arial for headings (this brand uses Poppins — keep the tech feel)
- Forgetting that body text is Georgia, not Arial (the serif/sans contrast is intentional)
- Using accent color on more than 20% of text elements (it loses its power)
- Table borders thicker than 1pt (looks aggressive)
- Using Poppins for body text (it is a display font, not a reading font)
- Forgetting spacing before H1 (always breathe before section starts)
- Page backgrounds (Word renders them unreliably; use physical cream paper instead)
- Using Primary Red (`FF1200`) or Primary Blue (`0043FF`) instead of Bridge colors (too vivid for print)

---

## Logo

**File:** `brands/remax-logo.png` (bundled, 400x245px, transparent background)

```javascript
const logoDefault = "on"; // Include logo + signature block automatically on every document
```

**Logo is ON by default for this brand.** Every document should include the RE/MAX logo alongside a signature block at the end of the document, using the `DEFAULTS` contact info. The user does not need to ask for it — it is included automatically. Only omit the logo if the user explicitly says "no logo", "without logo", or "skip the logo."

Typical placement: end of document, logo to the left of contact lines.

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

## Print Tips

For luxury printouts that match the digital warmth of this brand:

- **Keep page background WHITE in Word.** Never set a cream page color — the printer will spray a fine toner dusting across every page, tripling cost and making paper feel wavy.
- **Buy the color instead.** Use 28-32lb (105-120gsm) "Natural White" or "Cream" paper (e.g., Hammermill Premium, Mohawk Superfine). The physical paper provides the luxury warmth; the digital document stays clean.
- **The combination:** White background in Word + cream heavyweight paper = the Bridge Blue and Bridge Red pop beautifully, and the document feels substantial in a client's hands.

---

## Font Requirements

This brand requires **Poppins** (headings) and **Georgia** (body). Read [`references/font-fidelity.md`](../references/font-fidelity.md) for the full font doctrine; the brand-specific notes follow.

**Georgia on a headless box.** Georgia is a proprietary Microsoft font, absent from Linux containers (CI, the claude.ai sandbox); rendered to PDF there it substitutes to a default serif and the editorial-serif feel is lost. Substitute **Gelasio**, the metric-compatible open replacement (matches Georgia at unitsPerEm 2048, x-height 0.481 em, cap-height 0.693 em, 0.00% advance-width difference, verified 2026-06-18, so pagination is unchanged). Not Lora or another look-alike. One command (instances static cuts, installs, aliases Georgia, fails loud if it cannot):

```bash
python scripts/setup/font_preflight.py --family Georgia --substitute Gelasio \
  --source-url "https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf" \
  --weights 400,700 --alias
```

Georgia is built into Windows and macOS. Poppins must be installed:

- **Windows:** Download from [Google Fonts](https://fonts.google.com/specimen/Poppins), extract, select all .ttf files, right-click > "Install for all users". Restart Word.
- **Mac:** Download from Google Fonts, unzip, double-click each .ttf, click "Install Font". Restart Word.
- **Linux:** `mkdir -p ~/.fonts && cd ~/.fonts && for w in Regular Bold SemiBold Italic BoldItalic; do curl -Lo "Poppins-${w}.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-${w}.ttf"; done && fc-cache -fv`
- **Google Docs:** Poppins is available in the Google Docs font picker. Georgia is a default font. Both work natively — no installation needed, and PDF exports render correctly.

If Poppins is missing, Word silently falls back to Arial. The document opens fine but headings lose their character.

**Before sending a jasminahomes document outside your machine,** embed the fonts or export to PDF (PDF embeds and subsets automatically) so a recipient without Poppins or Georgia still sees the design. See the font-fidelity reference, "Distribution".
