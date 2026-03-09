---
title: Refactor single-brand DOCX skill into multi-brand architecture with pluggable brand files
date: 2026-03-07
category: integration-issues
severity: medium
tags: [multi-brand, docx-generation, skill-architecture, brand-tokens, typography, font-substitution, montserrat, gotham, remax, anthropic, signature-block, contact-info]
components: [branded-docx, brands/, SKILL.md]
root_cause: Single-brand hardcoded skill could not scale to support multiple brand identities with distinct typography, color tokens, and contact defaults
resolution: Refactored coral-docx into branded-docx with a brands/ directory containing one .md config per brand, standardized on 9 BRAND token keys, added DEFAULTS contact blocks, and selected Montserrat as free Gotham substitute
---

## Problem

The original `coral-docx` skill was hardcoded to Anthropic's coral visual identity. Every design token (colors, fonts, spacing) was baked directly into SKILL.md, making it impossible to add a second brand without duplicating the entire skill. When a RE/MAX brand was needed, two additional problems surfaced:

- **Gotham is commercial** -- RE/MAX officially uses Gotham (Hoefler&Co), which requires a paid license and is unavailable in Google Docs
- **No contact defaults** -- signature blocks required manual entry every time, even though each brand has a consistent author

## Root Cause

The architecture was tightly coupled to one brand's tokens. SKILL.md served as both the rendering engine (markdown-to-DOCX conversion rules, helper functions, page setup) and the brand definition (colors, fonts, design principles). There was no separation between "how to build a branded document" and "which brand to apply."

## Solution

### Pluggable architecture: SKILL.md engine + brands/*.md

The skill was split into two layers:

- **`SKILL.md`** (v2.0.0) -- brand-agnostic engine with markdown-to-DOCX conversion rules, helper function templates, cover page logic, and brand selection algorithm. All templates reference `BRAND.*` keys.
- **`brands/*.md`** -- one file per brand. Each is a self-contained definition with tokens, styles, design principles, color/typography references, logo guidance, and font installation instructions.

### Brand selection algorithm

1. List files in `brands/` to discover available brands
2. If the user names a brand matching a filename (e.g., "coral report" matches `brands/coral.md`), read that file
3. If only one brand file exists, use it without asking
4. If multiple brands exist and the request is ambiguous, list available brands and ask

### The 9 standardized BRAND token keys

| Key | Purpose |
|-----|---------|
| `dark` | Primary text, dark backgrounds |
| `light` | Page tone, section backgrounds |
| `midGray` | Captions, metadata, secondary text |
| `lightGray` | Table zebra rows, subtle dividers |
| `accent` | Primary accent color |
| `secondary` | Secondary accent |
| `tertiary` | Tertiary accent |
| `heading` | Heading font family |
| `body` | Body font family |

### DEFAULTS contact block

Brand files include an optional `DEFAULTS` object for auto-populating signature blocks:

```javascript
const DEFAULTS = {
  name: "Jane Smith",
  title: "Sales Representative",
  phone: "555-123-4567",
  email: "jane@example.com",
  brokerage: "RE/MAX Example Realty Inc."
};
```

User-provided values always override defaults. Brand-specific keys (like `brokerage`) are permitted beyond the base set.

### Font decision: Montserrat

| Font | Gotham Match | Google Docs Native | Verdict |
|------|-------------|-------------------|---------|
| Metropolis | 95% | No | Best match but worst ecosystem |
| **Montserrat** | **85%** | **Yes** | Best balance -- free, widely used RE/MAX substitute |
| Figtree | 80% | Yes | Modern but least like Gotham |

The brand file notes: "If you have a Gotham license, change the `heading` token back to `'Gotham'`."

### Bridge colors vs Primary for RE/MAX print

RE/MAX Primary Red (`#FF1200`) and Primary Blue (`#0043FF`) are for signage and screens. For documents, Bridge gradations provide better readability:

- Bridge Blue `#0C2749` (deep navy) as `accent`
- Bridge Red `#AA1120` as `secondary`

### Design policies

- **Website suppressed by default**: "Do not add a website line to signature blocks unless the source document explicitly mentions one."
- **Logos off by default**: Only included when user explicitly requests it.

## Key Files

| File | Role |
|------|------|
| [SKILL.md](skills/branded-docx/SKILL.md) | Brand-agnostic engine |
| [coral.md](skills/branded-docx/brands/coral.md) | Anthropic/Coral brand (Poppins + Georgia) |
| [remax.md](skills/branded-docx/brands/remax.md) | RE/MAX brand (Montserrat + Arial) |

## Prevention & Best Practices

**Adding a new brand checklist:**

1. Create `brands/<name>.md` with all 9 BRAND token keys as 6-digit hex (no shorthand)
2. Choose fonts that are free, cross-platform, and ideally native in Google Docs
3. Add `DEFAULTS` block only if the brand has a consistent author -- omit rather than leave empty
4. Include logo path only if a logo file exists in `brands/` -- skip silently otherwise
5. Add Font Requirements section with install instructions for Windows, macOS, Linux, and Google Docs

**Common mistakes:** RGB tuples instead of hex strings, copy-pasting another brand and leaving stale font names, specifying fonts without fallback guidance, adding website to DEFAULTS (bloats signatures).

**Testing:** Generate a test DOCX with H1, H2, body text, bulleted list, and a table. Open in both Word and Google Docs. Verify heading font renders (not falling back to Calibri), accent color appears on borders/headers, and contrast ratios are readable.

## Related Documents

- [coral-docx-rename-and-node-path-fix.md](coral-docx-rename-and-node-path-fix.md) -- earlier rename from branded-docx to coral-docx and the NODE_PATH preamble fix
- [skill-building-best-practices.md](../../skill-building-best-practices.md) -- references branded-docx as an example skill
