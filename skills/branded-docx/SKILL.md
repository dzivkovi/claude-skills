---
name: branded-docx
description: "Creates Word (.docx) documents styled with a brand identity from pluggable theme files. Use whenever the user wants a branded, professional Word document, report, brief, memo, or playbook. Triggers include: 'branded report', 'coral docx', 'coral report', 'remax report', 'professional Word doc', 'Anthropic style', 'styled document', 'polished report', 'make it look professional', 'convert this markdown', 'with logo', 'add signature block', or any .docx request where visual quality matters. Reads brand files from brands/ to apply the correct theme. Logos and signature blocks are optional and off by default. All base DOCX technical rules still apply - read them from the docx skill if in doubt."
metadata:
  author: Daniel Zivkovic
  version: 2.0.0
---

# Branded DOCX - Pluggable Brand Themes

This skill extends the base `docx` skill with pluggable brand themes. Follow all technical rules from the base DOCX skill (fonts, lists, tables, page size, etc.). This file adds the brand layer on top.

## Brand Selection

1. List files in `brands/` to see available brands.
2. If the user names a brand matching a filename (e.g., "coral report" matches `brands/coral.md`), read that file.
3. If only one brand file exists, use it without asking.
4. If multiple brands exist and the request is ambiguous, list available brands and ask.
5. Read the selected brand file. Use its `BRAND` tokens, `brandStyles`, and design principles for all document generation.

---

## NODE_PATH Preamble

Every generated script must start with this so globally-installed npm packages resolve regardless of working directory:

```javascript
const { execSync } = require('child_process');
if (!process.env.NODE_PATH) {
  process.env.NODE_PATH = execSync('npm root -g').toString().trim();
  require('module').Module._initPaths();
}
```

---

## Markdown-to-DOCX Conversion Rules

When the user provides markdown, apply these mappings automatically:

| Markdown element | Branded DOCX equivalent |
|-----------------|------------------------|
| First `#` heading | Cover page title (heading font, bold, dark) + accent top bar |
| First `>` blockquote after `#` | Cover page subtitle (body font italic, mid gray) |
| Any date-like line in first 10 lines | Cover page date (heading font, mid gray) |
| `##` heading | H1 section heading (heading font bold, accent color, bottom border) |
| `###` heading | H2 sub-heading (heading font bold, dark) |
| `####` heading | H3 sub-heading (heading font bold, dark) |
| Regular paragraph | Body text (body font 11pt, dark) |
| `> blockquote` (body) | Callout block (left accent border, indented) |
| `- ` or `* ` bullet list | Bulleted list (accent bullet dot, body font) |
| `1.` numbered list | Numbered list (body font) |
| `---` horizontal rule | Section divider (light gray bottom border) |
| `| table |` | Branded table (dark header row, alternating light gray rows) |
| `**bold**` | Bold TextRun. If text ends with `:`, use accent color + heading font |
| `*italic*` | Italic TextRun |
| `` `code` `` | Heading font, mid gray |
| Fenced code block | Indented block, heading font 9pt, light gray background |

### Cover page detection

If the markdown begins with a `#` title, treat the document as having a cover page. Extract:
- Title: the `#` text
- Subtitle: first blockquote or italicised line after the title
- Date: any date pattern (e.g. "March 2026", "2026-03-06") in the first 10 lines

If no cover page signals are found, start with H1 directly.

### When no markdown is provided

Generate the document from the user's description. Ask for content if none is given.

### Logo usage

Logos are **off by default**. Only include a brand logo when the user explicitly asks for it (e.g., "add the logo", "include a signature block", "with branding"). Brand files may bundle a `*-logo.png` file alongside their `.md` — check the brand file's Logo section for the filename, recommended sizes, and placement guidance. If no logo file exists for the active brand, skip silently.

### Default contact info

Brand files may include a `DEFAULTS` object with contact details (name, title, phone, email). When generating signature blocks or contact sections, use these defaults if the user hasn't specified their own info. User-provided values always override defaults. If the brand file has no `DEFAULTS`, ask the user for contact info when needed. Do not add a website line to signature blocks unless the source document explicitly mentions one.

---

## Helper Function Templates

These reference `BRAND.*` keys defined in the brand file. Copy them into generated scripts.

### Page Setup

```javascript
sections: [{
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
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
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BRAND.accent, space: 4 } },
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: title, font: BRAND.heading, size: 16, color: BRAND.midGray }),
          new TextRun({ children: [new PositionalTab({ alignment: PositionalTabAlignment.RIGHT, relativeTo: PositionalTabRelativeTo.MARGIN, leader: "none" })], font: BRAND.heading, size: 16, color: BRAND.midGray }),
          new TextRun({ children: [PageNumber.CURRENT], font: BRAND.heading, size: 16, color: BRAND.accent }),
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

### Cover Page

```javascript
function coverPage(title, subtitle, date) {
  return [
    new Paragraph({
      border: { top: { style: BorderStyle.SINGLE, size: 48, color: BRAND.accent, space: 0 } },
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

### Callout Block

```javascript
new Paragraph({
  style: "Callout",
  children: [
    new TextRun({ text: "Key insight: ", font: BRAND.heading, size: 22, bold: true, color: BRAND.accent }),
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

## Setup

1. Node.js installed (`node --version`)
2. `npm install -g docx`
3. Check your brand file for required fonts

All base DOCX technical rules apply — read the `docx` skill for details on lists, images, hyperlinks, page breaks, and XML editing.
