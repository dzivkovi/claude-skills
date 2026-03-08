# Anthropic Brand System - Reference

## Sources

Derived from Anthropic's official brand-guidelines skill (anthropics/skills GitHub),
Geist agency case study, and visual analysis of Anthropic's published PDFs.

---

## Color System

### Primary Palette

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| Dark | `#141413` | 20, 20, 19 | All body text, strong backgrounds |
| Light | `#FAF9F5` | 250, 249, 245 | Page tone, section backgrounds |
| Mid Gray | `#B0AEA5` | 176, 174, 165 | Captions, metadata, subdued text |
| Light Gray | `#E8E6DC` | 232, 230, 220 | Table zebra rows, subtle dividers |

### Accent Palette

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| Coral (primary) | `#D97757` | 217, 119, 87 | H1 headings, callout labels, accent bars |
| Blue (secondary) | `#6A9BCC` | 106, 155, 204 | Secondary accents, data highlights |
| Green (tertiary) | `#788C5D` | 120, 140, 93 | Tertiary accents, positive indicators |

**Rule:** Use coral sparingly. One or two coral elements per page maximum.
If everything is coral, nothing is.

---

## Typography System

### Font Roles

```
Poppins   -> Structure: headings, labels, captions, UI text, callout prefixes
Georgia   -> Reading: all body paragraphs, quotes, long-form content
```

### Size Scale (in docx-js half-points: 1pt = 2 units)

| Role | pt | docx units | Notes |
|------|----|------------|-------|
| Display / Cover title | 36pt | 72 | Poppins Bold |
| H1 | 26pt | 52 | Poppins Bold, Coral |
| H2 | 18pt | 36 | Poppins Bold, Dark |
| H3 | 13pt | 26 | Poppins Bold, Dark |
| Body | 11pt | 22 | Georgia, Dark |
| Caption / Label | 9pt | 18 | Poppins, Mid Gray |
| Footer | 8pt | 16 | Poppins, Mid Gray |

---

## Layout System

### Margins

Standard: 1 inch all sides (1440 DXA).
Dense (data-heavy): 0.75 inch sides (1080 DXA).

### Spacing Rhythm

Use multiples of 120 DXA (approximately 1/12 inch):
- Tight: 80 before, 80 after
- Normal: 120 before, 120 after
- Loose (after headings): 160 after
- Section gap: 360-480 before major headings

### Content Width (at 1" margins, US Letter)

Full width: 9360 DXA
Two column (equal): 4680 DXA each
Two column (60/40): 5616 / 3744 DXA

---

## Document Archetypes

### Report / Playbook (most common)
- Cover: Large title + coral top-bar + subtitle + date
- Section structure: H1 per chapter (coral, with bottom border), H2 per topic
- Body: Georgia 11pt, generous line spacing (276-288 DXA = 1.25-1.3 line)
- Tables: Dark header row, alternating light gray rows
- Callouts: Left coral border, indented

### Brief / Memo (shorter)
- No cover page - title is first H1
- Header with document title + page number
- 2-3 levels of hierarchy maximum

### Executive Summary
- One-page format
- Large H1 title, no chapter structure
- Use callout blocks for key points instead of bullet lists where possible

---

## What the Anthropic PDFs Actually Do

Observed patterns from "The Code Modernization Playbook", "Skills Guide", and "Constitution":

1. **Chapter openers** use a full-width dark (or coral) accent bar at the top of the page.
2. **Chapter numbers** are often set in coral or a muted tone, separate from the chapter title.
3. **Content width** is constrained - wide margins signal quality and breathing room.
4. **Tables** have a dark (#141413) header row with white text, no gridlines on outer edges.
5. **Pull quotes / callouts** use a thick left border in coral, no background shading.
6. **Footers** are minimal: document title left, page number right, separated by a light rule.
7. **Body font** is a warm serif (Tiempos/Lora equivalent) - never a cold sans for long paragraphs.
8. **Bullet points** use a coral dot, indented generously.

---

## Common Mistakes to Avoid

- Using `#D97757` on more than 20% of text elements (coral loses its power)
- Table borders thicker than 1pt (makes tables look aggressive)
- Using Poppins for body text (it is a display/UI font, not a reading font)
- Forgetting spacing before H1 (Anthropic docs always breathe before section starts)
- Adding page backgrounds (Word does not render them reliably across platforms)
- Nested tables or tables as layout dividers (see base docx skill rules)
