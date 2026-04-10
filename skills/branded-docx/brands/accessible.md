# Accessible - Large Print Theme for Low-Vision Readers

A standalone theme for printed documents intended for elderly or visually impaired readers. Based on the Jasmina Homes visual architecture (Poppins headings, Georgia body, navy/red palette) but stripped of all real estate branding, logos, and signature blocks. The result is a clean, high-contrast, large-print document that looks professional without being tied to any business identity.

---

## BRAND Tokens

```javascript
const BRAND = {
  dark:       "232323",   // dark charcoal
  light:      "FFFFFF",   // pure white
  midGray:    "8A8780",   // warm gray - timestamps, metadata
  lightGray:  "EDEAE0",   // warm cream-gray - dividers, zebra rows
  accent:     "0C2749",   // deep navy - headings, structural elements
  secondary:  "AA1120",   // bridge red - callout borders, emphasis
  tertiary:   "A3D4F2",   // sky blue - soft highlights
  heading:    "Poppins",  // geometric sans - clear, modern
  body:       "Georgia",  // editorial serif - high readability at large sizes
};
```

### Cover Page Tokens

```javascript
const COVER = {
  barColor: BRAND.secondary,
  categoryColor: BRAND.secondary,
  categorySpacing: 0,
  categoryCaps: false,
  titleSpacing: 0,
};
```

---

## No Logo, No Signature, No Defaults

```javascript
const logoDefault = "off";
```

This theme has no logo, no signature block, and no default contact info. It is a content-only theme. If the user explicitly asks for a signature block, ask them for the details.

---

## Typography - Accessible Size Scale

Every size is designed so that NO readable element falls below 14pt (sz=28). The heading-to-body ratio is compressed to ~1.6x to prevent visual overwhelm in documents with many sections.

```javascript
const brandStyles = {
  default: {
    document: { run: { font: BRAND.body, size: 28, color: BRAND.dark } }
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 44, bold: true, color: BRAND.accent },
      paragraph: {
        spacing: { before: 240, after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.secondary, space: 6 } },
        outlineLevel: 0
      }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 36, bold: true, color: BRAND.accent },
      paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 28, bold: true, color: BRAND.midGray },
      paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 2 }
    },
    {
      id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.heading, size: 24, color: BRAND.midGray, italics: false },
      paragraph: { spacing: { before: 40, after: 160 } }
    },
    {
      id: "Callout", name: "Callout", basedOn: "Normal", next: "Normal",
      run: { font: BRAND.body, size: 28, color: BRAND.dark },
      paragraph: {
        spacing: { before: 160, after: 160 },
        indent: { left: 720 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: BRAND.secondary, space: 12 } }
      }
    }
  ]
};
```

---

## Typography Reference

| Element           | Font          | Size (pt) | docx sz | Notes                              |
|-------------------|---------------|-----------|---------|--------------------------------------|
| Cover title       | Poppins Bold  | 36        | 72      | Largest element - landmark           |
| Cover category    | Poppins Bold  | 14        | 28      | Speaker/author name, same as body    |
| Cover subtitle    | Poppins       | 18        | 36      | Document type, italicized            |
| Cover date        | Poppins       | 14        | 28      | Same as body                         |
| Cover metadata    | Poppins       | 12        | 24      | Source, duration                     |
| H1 section heading| Poppins Bold  | 22        | 44      | Reduced - many sections, less shout  |
| H2                | Poppins Bold  | 18        | 36      | Standard proportion                  |
| H3 subheading     | Poppins Bold  | 14        | 28      | Same size as body; bold only         |
| Body text         | Georgia       | 14        | 28      | The floor - nothing smaller          |
| Timestamp labels  | Poppins       | 14        | 28      | Same as body, gray color             |
| Bullets           | Georgia       | 14        | 28      | Same as body                         |
| Callout text      | Georgia       | 14        | 28      | Same as body, indented + red border  |
| Table data        | Georgia       | 14        | 28      | Same as body (not reduced)           |
| Table header      | Poppins Bold  | 14        | 28      | Same as body, white on dark          |
| Summary heading   | Poppins Bold  | 28        | 56      | Landmark, stands out from section H1 |
| Footer            | Poppins       | 10        | 20      | Structural chrome, OK to be smaller  |
| Header            | Poppins       | 10        | 20      | Structural chrome                    |

### The accessible ratio

Standard themes use a 2.4x heading-to-body ratio (26pt / 11pt). This theme uses 1.6x (22pt / 14pt). When body text is already large, the reader navigates by color and bold weight, not by size contrast. Oversized headings waste paper and feel aggressive.

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

### 1. Nothing below 14pt
Every element the reader might actually read must be at least 14pt (sz=28). The only exceptions are header and footer chrome. If you catch yourself setting a size below 28, stop and reconsider.

### 2. Cover page is content-first
The cover should tell the reader WHAT this is about and WHO is involved. Lead with the speaker, author, or subject name as the category line. The document type (transcript, report, summary) goes in the subtitle.

**Cover page order:**
```
[red accent bar]
[Speaker / Author / Subject]     <- category line, 14pt, red
[Topic title]                    <- main title, 36pt, dark
[Document type]                  <- subtitle, 18pt, gray italic
---
[Date]                           <- 14pt, gray
[Source / Duration]              <- 12pt, gray
```

### 3. Section headings: wayfinding, not shouting
22pt headings on 14pt body. Bold + navy + red bottom border provides clear separation without overwhelming. In documents with 15+ sections, this matters. Spacing above headings is kept tight (240 DXA, not the standard 480) to avoid wasting vertical space on every section break.

### 4. No dividers
Do NOT generate horizontal rule dividers between sections. The H1's own red bottom border provides all the separation needed. Dividers at 14pt body text become thick visual barriers that waste paper. Remove them entirely.

### 5. Timestamps at body size
Timestamps are not metadata to be hidden. The reader may use them to find content in a video or recording. Keep them at body size (14pt) in warm gray (BRAND.midGray).

### 6. Generous spacing
Do not tighten spacing to save pages. More pages is fine. Use the standard spacing rhythm (multiples of 120 DXA). Cramped text defeats the purpose.

### 7. High contrast
Dark charcoal (232323) on white is the default. Never use light gray text for body content. Gray is only for timestamps, metadata, and structural elements.

---

## Spacing Rhythm

Same as Jasmina Homes base, with slightly more generous after-heading spacing:

- Tight: 80 before, 80 after
- Normal: 120 before, 120 after
- After H1: 200 after (slightly more than standard 160)
- After H3: 120 after (slightly more than standard 80)
- Section gap: 240 before H1 (compact - no wasted space above headings)
- Table cell margins: 80 DXA top/bottom (more breathable)

---

## Color Reference

Identical to Jasmina Homes. High-contrast navy + red works well for low vision.

| Role       | Hex      | Use                                     |
|------------|----------|-----------------------------------------|
| Dark       | 232323   | Body text, strong backgrounds           |
| Light      | FFFFFF   | Page background                         |
| Mid Gray   | 8A8780   | Timestamps, metadata, H3               |
| Light Gray | EDEAE0   | Table zebra rows                       |
| Accent     | 0C2749   | H1/H2 headings, table headers          |
| Secondary  | AA1120   | Callout borders, bullet accents, bar   |
| Tertiary   | A3D4F2   | Soft highlights                         |
| Info tint  | F0F2F8   | Faint info callout background           |
| Alert tint | FDF5F5   | Faint alert callout background          |

---

## Common Mistakes

- Setting any readable text below sz=28 (14pt) - the whole point of this theme
- Using 26pt headings from the standard theme (too large for accessible ratio)
- Putting the document production type ("Segmented Transcript") as the cover category instead of the content subject
- Adding divider lines between sections (the H1 red bottom border is enough; no dividers in this theme)
- Reducing margins to fit more text (white space aids readability)
- Including logo or signature block (this theme is brand-neutral)
- Using light gray for body text (reserve gray for timestamps and metadata only)

---

## Font Requirements

Same as Jasmina Homes: **Poppins** (headings) and **Georgia** (body).

Georgia is built into Windows and macOS. Poppins must be installed:

- **Windows:** Download from [Google Fonts](https://fonts.google.com/specimen/Poppins), extract, select all .ttf files, right-click > "Install for all users". Restart Word.
- **Mac:** Download from Google Fonts, unzip, double-click each .ttf, click "Install Font". Restart Word.

---

## Print Tips

For best results with low-vision readers:

- Print on **28-32lb Natural White or Cream paper** for warmth and thickness
- Keep page background WHITE in Word (no toner waste)
- The navy + red palette pops beautifully on cream paper
- Consider **single-sided printing** so pages lie flat and are easier to hold
- **Spiral binding** or **large binder clips** are easier for elderly readers than staples
