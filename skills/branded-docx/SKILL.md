---
name: branded-docx
description: "Creates Word (.docx) documents styled with Anthropic's visual identity: coral accent (#D97757), near-black text (#141413), off-white tone (#FAF9F5), Poppins headings, Georgia body text. Use whenever the user wants a polished, professional Word document, report, brief, memo, or playbook that looks like it came from Anthropic. Triggers include: 'branded report', 'professional Word doc', 'Anthropic style', 'styled document', 'polished report', 'make it look professional', or any .docx request where visual quality matters. All base DOCX technical rules still apply - read them from the docx skill if in doubt."
---

# Branded DOCX - Anthropic Visual Identity

This skill extends the base `docx` skill with Anthropic's design system. Follow all technical rules from the base DOCX skill (fonts, lists, tables, page size, etc.). This file adds the brand layer on top.

---

## Bundled resources - read these when relevant

| Path | What it is | When to read |
|------|------------|--------------|
| `references/brand-system.md` | Full color/type/layout system with copy-paste templates | Always - read before generating any document |
| `references/setup-and-prerequisites.md` | Node.js, docx npm, font install instructions for Windows/Mac/Linux | When user hits a setup error or asks how to install fonts |
| `scripts/setup/install-fonts-windows.ps1` | One-click Windows font installer - right-click > Run with PowerShell | Point users here for Windows font setup |
| `assets/branded-sample.docx` | Pre-generated sample showing the full brand system in action | Tell users to open this to preview the output before committing |

---

## First-time setup (tell the user if this is their first document)

Before the first document generates correctly, the user needs:
1. Node.js installed - check with `node --version`
2. `npm install -g docx` run once
3. Poppins font installed - see `scripts/setup/install-fonts-windows.ps1` (Windows) or `references/setup-and-prerequisites.md` (Mac/Linux)

Full details and troubleshooting: `references/setup-and-prerequisites.md`

---

Read `references/brand-system.md` for full design system details and copy-paste templates.

---

## Brand Tokens (Quick Reference)

### Colors (use without `#` in docx-js)

| Role | Hex | Use |
|------|-----|-----|
| Dark | `141413` | Primary text, dark backgrounds |
| Light | `FAF9F5` | Subtle section backgrounds |
| Mid Gray | `B0AEA5` | Captions, secondary text |
| Light Gray | `E8E6DC` | Table rows, dividers |
| **Coral** | `D97757` | H1 headings, accent bars, key callouts |
| Blue | `6A9BCC` | Secondary accent, links |
| Green | `788C5D` | Tertiary accent |

### Typography

| Element | Font | Fallback | Size |
|---------|------|----------|------|
| Title / H1 | Poppins | Arial | 28-36pt |
| H2 | Poppins | Arial | 18pt |
| H3 | Poppins | Arial | 13pt |
| Body | Georgia | Times New Roman | 11pt |
| Caption / Label | Poppins | Arial | 9pt |

---

## Mandatory Style Overrides

Always override the default docx style block with this brand configuration:

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, LevelFormat, PageNumber, TabStopType, TabStopPosition,
        PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo } = require('docx');

const BRAND = {
  dark:       "141413",
  light:      "FAF9F5",
  midGray:    "B0AEA5",
  lightGray:  "E8E6DC",
  coral:      "D97757",
  blue:       "6A9BCC",
  green:      "788C5D",
  heading:    "Poppins",
  body:       "Georgia",
};

const brandStyles = {
  default: {
    document: { run: { font: BRAND.body, size: 22, color: BRAND.dark } }
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: BRAND.heading, size: 52, bold: true, color: BRAND.coral },
      paragraph: {
        spacing: { before: 480, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.coral, space: 6 } },
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
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: BRAND.coral, space: 12 } }
      }
    }
  ]
};
```

---

## Document Structure Patterns

### Page Setup (always use these exact values)

```javascript
sections: [{
  properties: {
    page: {
      size: { width: 12240, height: 15840 },           // US Letter
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }  // 1" all sides
    }
  },
  headers: { default: brandHeader("Document Title") },
  footers: { default: brandFooter() },
  children: [ /* content */ ]
}]
```

### Branded Header

```javascript
function brandHeader(title) {
  return new Header({
    children: [
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BRAND.coral, space: 4 } },
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: title, font: BRAND.heading, size: 16, color: BRAND.midGray }),
          new TextRun({ children: [new PositionalTab({ alignment: PositionalTabAlignment.RIGHT, relativeTo: PositionalTabRelativeTo.MARGIN, leader: "none" })], font: BRAND.heading, size: 16, color: BRAND.midGray }),
          new TextRun({ children: [PageNumber.CURRENT], font: BRAND.heading, size: 16, color: BRAND.coral }),
        ]
      })
    ]
  });
}
```

### Branded Footer

```javascript
function brandFooter() {
  return new Footer({
    children: [
      new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: BRAND.lightGray, space: 4 } },
        children: [
          new TextRun({ text: "Confidential", font: BRAND.heading, size: 14, color: BRAND.midGray })
        ]
      })
    ]
  });
}
```

### Cover Page Pattern

```javascript
function coverPage(title, subtitle, date) {
  return [
    new Paragraph({
      border: { top: { style: BorderStyle.SINGLE, size: 48, color: BRAND.coral, space: 0 } },
      spacing: { before: 0, after: 2880 },
      children: []
    }),
    new Paragraph({
      children: [new TextRun({ text: title, font: BRAND.heading, size: 72, bold: true, color: BRAND.dark })],
      spacing: { before: 0, after: 240 }
    }),
    subtitle ? new Paragraph({
      children: [new TextRun({ text: subtitle, font: BRAND.body, size: 28, color: BRAND.midGray, italics: true })],
      spacing: { before: 0, after: 480 }
    }) : null,
    new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BRAND.lightGray, space: 8 } },
      spacing: { before: 0, after: 240 }, children: []
    }),
    date ? new Paragraph({
      children: [new TextRun({ text: date, font: BRAND.heading, size: 20, color: BRAND.midGray })],
      spacing: { before: 0, after: 0 }
    }) : null,
  ].filter(Boolean);
}
```

### Section Divider

```javascript
function sectionDivider() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: BRAND.lightGray, space: 1 } },
    spacing: { before: 360, after: 360 },
    children: []
  });
}
```

### Callout / Highlight Block

```javascript
new Paragraph({
  style: "Callout",
  children: [
    new TextRun({ text: "Key insight: ", font: BRAND.heading, size: 22, bold: true, color: BRAND.coral }),
    new TextRun({ text: "Your callout text here.", font: BRAND.body, size: 22, color: BRAND.dark })
  ]
})
```

### Branded Table

```javascript
function brandTable(headers, rows, contentWidth = 9360) {
  const colWidth = Math.floor(contentWidth / headers.length);
  const border = { style: BorderStyle.SINGLE, size: 1, color: BRAND.lightGray };
  const borders = { top: border, bottom: border, left: border, right: border };

  return new Table({
    width: { size: contentWidth, type: WidthType.DXA },
    columnWidths: headers.map(() => colWidth),
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map(h => new TableCell({
          borders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: { fill: BRAND.dark, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 160 },
          children: [new Paragraph({
            children: [new TextRun({ text: h, font: BRAND.heading, size: 18, bold: true, color: "FFFFFF" })]
          })]
        }))
      }),
      ...rows.map((row, i) => new TableRow({
        children: row.map(cell => new TableCell({
          borders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: { fill: i % 2 === 0 ? "FFFFFF" : BRAND.lightGray, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 160 },
          children: [new Paragraph({
            children: [new TextRun({ text: String(cell), font: BRAND.body, size: 20, color: BRAND.dark })]
          })]
        }))
      }))
    ]
  });
}
```

---

## Minimal Full Document Example

```javascript
const fs = require('fs');
const doc = new Document({
  styles: brandStyles,
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } },
          run: { font: BRAND.body, color: BRAND.coral } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: brandHeader("Report Title") },
    footers: { default: brandFooter() },
    children: [
      ...coverPage("Report Title", "Subtitle or tagline", "March 2026"),
      new Paragraph({ pageBreakBefore: true,
        heading: HeadingLevel.HEADING_1, children: [new TextRun("Section One")] }),
      new Paragraph({ children: [new TextRun({ text: "Body copy goes here.", font: BRAND.body, size: 22 })] }),
      sectionDivider(),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => fs.writeFileSync("output.docx", buf));
```

---

## Design Principles (apply to every document)

- **White space first.** Generous `spacing.before` and `spacing.after` on every element. Never crowd content.
- **Coral is precious.** Use `#D97757` only for H1, key callout labels, and accent bars. Not for decoration.
- **One serif, one sans.** Georgia for reading, Poppins for structure. No mixing within a paragraph.
- **Tables earn their place.** If it fits in prose, write prose. Tables for genuine comparisons only.
- **Validate after creation.** Always run `python scripts/office/validate.py output.docx`.

---

## Installation Note

This skill wraps the base `docx` skill. If validation or unpacking scripts are unavailable, install with:
```bash
npm install -g docx
```
