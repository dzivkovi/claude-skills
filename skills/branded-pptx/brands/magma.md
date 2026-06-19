# Magma Inc. (PPTX) - the magmainc.ca identity for slides

Magma Inc.'s own brand, from the kit at magmainc.ca: one typeface (Montserrat), a navy signature, two reds chosen by background, cool near-white surfaces. The feel to aim for is a precision instrument for serious people: confident, calm, restrained. Less is more.

Colours and type here match the Magma `docx` brand exactly, so decks and documents stay one identity. This file adds the slide-only parts: palette roles per slide type, the point-based type scale, the motif, and the font-QA caveat.

> The base PowerPoint capability is Anthropic's `pptx` skill (source-available, installed separately via `/plugin marketplace add anthropics/skills`). Nothing from it is copied here; this is the brand layer only.

---

## BRAND Tokens

```javascript
const BRAND = {
  navy:     "0C2749",  // signature: bookend backgrounds, headings, table header, the numbered-circle motif
  charcoal: "23211E",  // body text on light surfaces (warm near-black)
  cream:    "F8FAFC",  // content slide background (cool near-white)
  white:    "FFFFFF",  // card surface
  stone:    "EDF2F5",  // card border, table zebra, dividers (one shade cooler than cream)
  midGray:  "6B7785",  // captions, metadata (a derived cool slate, not a core brand colour)
  redLight: "AA1120",  // Bridge Red: red ON LIGHT (eyebrow, callout label, the one CTA)
  redDark:  "E2412F",  // Signal Red: red ON NAVY/dark (eyebrow + accents on bookends)
  sky:      "A3D4F2",  // soft highlight
  skyTint:  "EAF4FB",  // faint info/callout fill on light
  subNavy:  "B8C6D6",  // light slate for sub-text on the navy field
  font:     "Montserrat", // ONE typeface, all weights. 700 headings, 600 labels, 400 body. Do not substitute.
};
```

### DEFAULTS (contact)

```javascript
const DEFAULTS = {
  name: "Daniel Zivkovic", title: "AI Architect", company: "Magma Inc.",
  email: "daniel@magmainc.ca", website: "magmainc.ca"
};
```

---

## The load-bearing rule: two reds, chosen by surface

This is the single most-broken rule in the brand, so the helpers take an `onDark` flag and pick the red:

```javascript
const RED = (onDark) => (onDark ? BRAND.redDark : BRAND.redLight);
```

- On **light** slides (cream/white), red is **Bridge Red `AA1120`** (the deep one).
- On the **navy** field (bookends, navy cards), red is **Signal Red `E2412F`** (the brighter one).
- Never put `AA1120` on `0C2749`; the deep red goes muddy on navy. Every supplied logo and card already obeys this.

---

## Slide palette roles

One colour carries 60-70% of the weight: `navy` on bookends, `cream` on content. Navy is the signature and the rare "this is the decision" device. Red is a spice, not a base.

- **Title + closing slides (bookends):** `navy` background, white title, `redDark` eyebrow, `subNavy` sub-text. Place the dark logo lockup here (see Logo). These are the 1-2 navy beats of the deck.
- **Content slides:** `cream` background, `navy` title, `redLight` eyebrow, `charcoal` body.
- **Cards:** `white` fill, `stone` 1px border, soft shadow. They lift gently off the cream field. Never an edge stripe or accent bar.
- **Red discipline:** about two red moments per content slide, typically the eyebrow kicker and one callout label. Everything structural (numbered circles, flow arrows, highlighted nodes, table headers) is `navy`, not red.

---

## Type scale (points; Montserrat throughout)

| Element | Weight | Size |
|---------|--------|------|
| Title-slide headline | Bold 700 | 32-36 |
| Slide title | Bold 700 | 24-26 |
| Eyebrow / kicker | Bold 700 | 12 (uppercase, `charSpacing: 2`) |
| Section header / card head | Bold 700 | 13-19 |
| Body | Regular 400 | 11-13 |
| Caption / footnote | Regular 400 | 10-11 |
| Big stat callout | Bold 700 | 54-72 |

Montserrat carries hierarchy by weight, not by a second face. Headings 700, labels 600, body 400. Keep leading generous so all-sans body stays easy to read.

---

## Motif (pick one, repeat it)

Numbered **navy circles** (a filled `navy` oval with a white numeral) as the repeated structural element across list and step slides. Pair with white cards, stone borders, soft shadows. The motif is navy on purpose: making the circles red would blow the two-reds-per-page budget.

Never: accent bars, underlines beneath titles, vertical sidebar stripes, thin colour strips on a card edge.

---

## Design principles

- **Less is more.** Generous white space; don't fill every inch. Restraint is the brand.
- **Navy is rare emphasis.** Bookends and the occasional navy card or table header. Never wall-to-wall navy on a content slide.
- **Red is a spice.** ~2 reds per slide, surface-correct. If everything is red, nothing is.
- **One typeface.** Montserrat for everything; hierarchy by weight.
- **Every slide earns a visual.** A card grid, a flow, a stat, a table. Never a plain title-plus-bullets slide.
- **Stone is the quiet alternator** for bands and dividers when sections sit side by side.

---

## Logo

Bundled, off by default (include when asked or for a title/closing slide). Use the supplied files; never recolor, stretch, rotate, or rebuild the wordmark.

- **`brands/magma-logo-dark.png`** (white word + signal-red arcs + white dot): for the **navy** bookend slides. Place top-left of the title slide at roughly 1.25 x 1.25 inches.
- **`brands/magma-logo-white.png`** (navy word + bridge-red arcs): for any **light** slide.
- Pick the mark by slot shape per the brand kit: this **square lockup** suits a slide title block. The radar mark alone is favicon-grade only, not the company logo in a square slot.

---

## Font QA caveat

Montserrat is the brand and is free to embed (SIL OFL). For the LibreOffice QA render, install static Montserrat cuts (Regular + Bold), not only the variable font: LibreOffice may read a variable `Montserrat[wght].ttf` as "Montserrat Thin" and render headings in the wrong weight. With static Regular/Bold installed, the preview is trustworthy; still add ~10% height slack on Montserrat boxes, since width differs slightly from the substitute on a machine that lacks it. On the opening machine, install Montserrat so PowerPoint renders true (the kit bundles the files). Run `scripts/setup/font_preflight.py` to instance and install the static cuts in one fail-loud step; see [`../references/font-fidelity.md`](../references/font-fidelity.md) for the full doctrine and for embedding the deck before you send it.
