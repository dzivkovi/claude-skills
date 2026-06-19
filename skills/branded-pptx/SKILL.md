---
name: branded-pptx
description: "Creates PowerPoint (.pptx) decks styled with a brand identity from pluggable theme files (coral, magma, and more over time). Use whenever the user wants a branded, professional slide deck - leadership decks, talk slides, pitch decks, listing presentations, or any .pptx where visual quality matters. Triggers: 'branded deck', 'coral slides', 'coral pptx', 'magma deck', 'magma slides', 'magma pptx', 'my brand deck', 'in my style', 'styled presentation', 'polished deck', 'make slides look professional', 'turn this into slides', 'my usual theme'. Reads brands/ to apply the theme. This is a brand layer on top of Anthropic's base pptx skill - all base pptx technical rules still apply."
metadata:
  author: Daniel Zivkovic
  version: 0.3.0
---

# Branded PPTX - Pluggable Brand Themes

This skill extends Anthropic's base `pptx` skill with pluggable brand themes, the same way `branded-docx` extends the base `docx` skill. Install the base skill separately (`/plugin marketplace add anthropics/skills`, then the `document-skills` plugin); nothing from it is bundled here. Follow all of its technical rules (pptxgenjs API, the QA loop, the file-corruption pitfalls). This file adds the brand layer on top.

The governing design idea, borrowed from the base skill and worth restating: a deck is spatial composition, not flowing text. Brand tokens give you palette and type for free, but the layout decision on each slide is yours to make. Distil; do not pour paragraphs onto slides.

---

## Preflight: why two runs of this skill can look very different

A skill encodes the process, not the finished pixels. The same SKILL.md yields a sharp deck on one machine and a rough one on another, and the cause is almost always environment, not taste. Confirm all three before generating. Skip this and the deck ships with substituted fonts and unspotted overflow.

### 1. The brand font must be installed AS STATIC CUTS

This is the single most common cause of "the fonts don't fill the boxes." The deck names the brand font (e.g. Montserrat). If the machine that GENERATES, or the machine that OPENS the deck, lacks it, the app substitutes a font with different widths: text reflows and boxes overflow. A bare **variable** font (`Montserrat[wght].ttf`) is read by LibreOffice and some Office installs as "Montserrat Thin", so headings render thin and the QA preview lies. Install **static** Regular and Bold cuts named plainly "Montserrat".

Run the preflight, which instances static cuts from a variable font and FAILS LOUD if the font cannot be made available (never silently substitutes):

```bash
python scripts/setup/font_preflight.py --family Montserrat \
  --source-url "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf" \
  --weights 400,700
```

See [`references/font-fidelity.md`](references/font-fidelity.md) for the full doctrine, including substituting a metric-compatible face when a proprietary font is absent (Gelasio for Georgia, never a look-alike like Lora).

If the font is missing on the user's own machine, the deck is correct but renders as a substitute. Either tell them to install Montserrat (free under OFL), or embed it before sending (see Distribution, below). A correct file on a font-less machine is the rough result they will see.

### 2. The QA render tools must be present

LibreOffice (`soffice`) and Poppler (`pdftoppm`) are what let you SEE a slide and catch overflow. Absent, you generate blind and ship first-draft defects. Install them first (`brew install libreoffice poppler`, or apt), not after.

### 3. Then run the QA loop for real

The polish lives in the loop, not the templates. See the Definition of Done below.

---

## Brand Selection

1. List files in `brands/` to see available brands.
2. If the user names a brand matching a filename (e.g. "coral deck" matches `brands/coral.md`), read that file.
3. If only one brand file exists, use it without asking.
4. If multiple brands exist and the request is ambiguous, list them and ask.
5. Read the selected brand file. Use its `BRAND` tokens, slide palette roles, type scale, and motif for everything that follows.

---

## NODE_PATH Preamble

Every generated script starts with this so a globally-installed `pptxgenjs` resolves regardless of working directory:

```javascript
const { execSync } = require('child_process');
if (!process.env.NODE_PATH) {
  process.env.NODE_PATH = execSync('npm root -g').toString().trim();
  require('module').Module._initPaths();
}
const pptxgen = require('pptxgenjs');
```

---

## Markdown-to-Slides Mapping

When the user provides markdown, apply these mappings. Slides are not documents: distil body prose to the point, and push the full wording plus any speaker notes into Presenter View with `addNotes()`.

| Markdown element | Branded slide equivalent |
|------------------|--------------------------|
| First `#` heading | Title slide: `BRAND.dark` background, accent eyebrow, white title, sub-line |
| `##` heading | New content slide; the heading becomes the slide title with an accent eyebrow above it |
| `###` heading | Section header inside a slide, or a card label |
| Regular paragraph | Distil to a short line, a card, or a callout. Full text goes to `addNotes()` |
| `> blockquote` | Speaker note via `addNotes()` - never rendered on the slide face |
| `- ` / `* ` bullets | A bullet block (`bullet: true`) or, better, distilled into a card grid |
| `\| table \|` | Branded table (dark header row, zebra body) |
| ` ```mermaid ` | Recreate as native shapes. Render EVERY edge, including back-edges: a loop such as `G --> B` is a real return arrow drawn back into node B, not a caption. Flattening a loop to a text label is the most common way these diagrams lose their meaning. If 7+ nodes won't fit one row, wrap to a two-row racetrack so the return arrow stays visible. |
| `**Label:**` | Accent-coloured label run, then body run |

### Text fidelity vs. distillation

For documents, preserve wording verbatim. For slides, the opposite: distil onto the slide, preserve the user's exact wording in the notes. Preserve specific metaphors and any carefully-worded attributions exactly, even when distilling around them.

---

## Helper Function Templates

Copy these into generated scripts. They reference `BRAND.*` from the active brand file. Layout coordinates assume `LAYOUT_16x9` (10 x 5.625 inches), 0.5" margins, content width 9".

### Setup constants and a shadow factory

PptxGenJS mutates option objects in place, so shadows MUST come from a factory (never share one object across calls, or the second shape corrupts).

```javascript
const W = 10, MX = 0.5, CW = W - 2 * MX;
const softShadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.10 });
```

### Eyebrow + title (every content slide)

```javascript
function eyebrow(slide, text) {
  slide.addText(text, { x: MX, y: 0.40, w: CW, h: 0.3, margin: 0,
    fontFace: BRAND.heading, fontSize: 12, bold: true, color: BRAND.accent, charSpacing: 2 });
}
function slideTitle(slide, text, onDark) {
  slide.addText(text, { x: MX, y: 0.70, w: CW, h: 0.95, margin: 0,
    fontFace: BRAND.heading, fontSize: 28, bold: true, color: onDark ? BRAND.white : BRAND.dark, valign: "top" });
}
```

### Title / closing slide (dark bookend)

```javascript
function bookend(pres, eyebrowText, titleText, subText) {
  const s = pres.addSlide();
  s.background = { color: BRAND.dark };
  s.addText(eyebrowText, { x: MX, y: 1.55, w: CW, h: 0.35, margin: 0,
    fontFace: BRAND.heading, fontSize: 13, bold: true, color: BRAND.accent, charSpacing: 2 });
  s.addText(titleText, { x: MX, y: 2.0, w: CW, h: 1.4, margin: 0,
    fontFace: BRAND.heading, fontSize: 40, bold: true, color: BRAND.white });
  if (subText) s.addText(subText, { x: MX, y: 3.5, w: CW, h: 0.4, margin: 0,
    fontFace: BRAND.body, fontSize: 14, color: "CFCFCF" });
  return s;
}
```

### Callout bar (the accent-tint emphasis strip)

```javascript
function calloutBar(slide, text, y) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y, w: CW, h: 0.62, rectRadius: 0.06,
    fill: { color: BRAND.accentTint }, line: { type: "none" } });
  slide.addText(text, { x: MX + 0.25, y, w: CW - 0.5, h: 0.62, margin: 0,
    fontFace: BRAND.body, fontSize: 13, bold: true, color: BRAND.dark, valign: "middle" });
}
```

### Numbered card (the motif)

```javascript
function numberedCard(slide, x, y, w, h, n, head, bodyText) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06,
    fill: { color: BRAND.lightGray }, line: { color: BRAND.lightGray, width: 1 }, shadow: softShadow() });
  slide.addShape(pres.shapes.OVAL, { x: x + 0.25, y: y + 0.23, w: 0.5, h: 0.5, fill: { color: BRAND.accent } });
  slide.addText(String(n), { x: x + 0.25, y: y + 0.23, w: 0.5, h: 0.5, margin: 0,
    fontFace: BRAND.heading, fontSize: 18, bold: true, color: BRAND.white, align: "center", valign: "middle" });
  slide.addText(head, { x: x + 0.25, y: y + 0.83, w: w - 0.5, h: 0.55, margin: 0,
    fontFace: BRAND.heading, fontSize: 14, bold: true, color: BRAND.dark, valign: "top" });
  slide.addText(bodyText, { x: x + 0.25, y: y + 1.37, w: w - 0.5, h: h - 1.5, margin: 0,
    fontFace: BRAND.body, fontSize: 11, color: BRAND.dark, valign: "top" });
}
```

### Flow diagram (native shapes — for mermaid sources)

```javascript
function flowBox(slide, x, y, w, h, label, highlight) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06,
    fill: { color: highlight ? BRAND.accent : BRAND.lightGray },
    line: { color: highlight ? BRAND.accent : BRAND.lightGray, width: 1 }, shadow: softShadow() });
  slide.addText(label, { x: x + 0.06, y, w: w - 0.12, h, margin: 0,
    fontFace: BRAND.heading, fontSize: 10.5, bold: true, color: highlight ? BRAND.white : BRAND.dark,
    align: "center", valign: "middle" });
}
function arrow(slide, x, y, w) {
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: BRAND.accent, width: 2, endArrowType: "triangle" } });
}
```

### Big stat callout

```javascript
function stat(slide, x, y, w, value, label) {
  slide.addText(value, { x, y, w, h: 1.0, margin: 0,
    fontFace: BRAND.heading, fontSize: 60, bold: true, color: BRAND.accent, align: "center" });
  slide.addText(label, { x, y: y + 1.0, w, h: 0.5, margin: 0,
    fontFace: BRAND.heading, fontSize: 12, color: BRAND.midGray, align: "center" });
}
```

### Branded table

```javascript
function brandTable(slide, headers, rows, x, y, w, colW) {
  const head = headers.map(h => ({ text: h, options: { fill: { color: BRAND.dark }, color: BRAND.white,
    bold: true, fontFace: BRAND.heading, fontSize: 11 } }));
  const body = rows.map((r, i) => r.map(c => ({ text: String(c), options: {
    fill: { color: i % 2 === 0 ? BRAND.white : BRAND.lightGray }, color: BRAND.dark,
    fontFace: BRAND.body, fontSize: 11 } })));
  slide.addTable([head, ...body], { x, y, w, colW, valign: "middle",
    border: { pt: 0.5, color: BRAND.lightGray }, margin: [4, 8, 4, 8] });
}
```

### Speaker notes

```javascript
slide.addNotes(fullProseAndAnyBlockquoteNotesForThisSlide);
```

---

## Layout discipline (from the base skill, restated as brand rules)

- Vary layouts across slides: card grid, two-column, flow, stat, table. Do not repeat one layout.
- Left-align body and lists; centre only titles.
- Strong size contrast: titles 28pt+ above 13-15pt body.
- No accent bars, no underlines beneath titles, no edge stripes on cards. Use tint or shadow to set a card apart.
- Never ship text that overflows its box.

## pptxgenjs pitfalls that corrupt files (do not violate)

- Hex colours never start with `#`.
- Never encode opacity in an 8-char hex; use the `opacity` property.
- Bullets use `bullet: true`, never a unicode "•".
- Fresh shadow object per shape (use the `softShadow()` factory).

---

## QA: Definition of Done (not optional)

The templates give a reasonable first draft. The sharpness comes from rendering every slide and fixing what you see. Do not deliver until this passes.

1. Render the whole deck to images:

```bash
python <base-pptx-skill>/scripts/office/soffice.py --headless --convert-to pdf out.pptx
rm -f slide-*.jpg && pdftoppm -jpeg -r 110 out.pdf slide
```

2. Look at EVERY slide. Check text bounds first: no run may cross or overflow its shape; no card may touch a callout or a neighbour; a title that wraps must not crowd the line beneath it.
3. Fix by nudging coordinates or reducing font size, then re-render the affected slides. Expect one or two genuine defects on the first pass (a wrapped title, a card grid run too tight). Fixing them is the job, not an extra step.
4. Hidden slides are dropped from PDF export, so to QA an appendix, render a temporary copy with `hidden` turned off.
5. If the brand font is not installed as static cuts (Preflight 1), the preview substitutes and its text-fit is unreliable; install the font so the preview tells the truth, and still add ~10% height slack on heading boxes.

Declare done after seeing every slide render clean, never after merely generating.

---

## Distribution: before the deck leaves your machine

Installing the brand font on your machine makes the deck render true for YOU. It does nothing for whoever you send it to: without the font, their PowerPoint substitutes and the text reflows, the exact rough look the Preflight fixed on your end. pptxgenjs CANNOT embed fonts, so close the gap one of two ways:

- Embed in PowerPoint: File, Options, Save, "Embed fonts in the file", choose "Embed all characters". The .pptx now carries Montserrat and travels self-contained.
- Or send a PDF (export embeds and subsets fonts automatically). Verify with `pdffonts deck.pdf`: every row should read `yes yes`.

See [`references/font-fidelity.md`](references/font-fidelity.md), "Distribution", for the full rule. A deck that looks perfect on your screen but was never embedded is the single most common way the brand breaks on someone else's laptop.

## Setup

1. Node.js (`node --version`)
2. `npm install -g pptxgenjs`
3. For the QA render only: LibreOffice (`soffice`) and Poppler (`pdftoppm`). On macOS: `brew install libreoffice poppler`. The `docx` skill never needed these; the slide QA loop does.
4. Run the font preflight (`scripts/setup/font_preflight.py`) so the brand font is installed as static cuts and the QA preview is trustworthy (see Preflight 1). This is the step that most often gets skipped and is the usual reason a deck looks rough.

All base `pptx` technical rules apply - read that skill for images, charts, masters, and XML editing.
