# Font fidelity: making brand fonts render true, everywhere

This is the single source of truth for font handling across the branded skills. It is identical in `branded-docx` and `branded-pptx`; keep the two copies in sync (see CLAUDE.md). Brand files and SKILL.md point here instead of restating the rules in their own words.

## The principle

A document or deck declares a font by name. The skill always produces a correct *file*; whether it *looks* right depends on the machine that renders or opens it. There are three distinct problems, and they need different fixes:

1. Generation, font ABSENT. The named font is not on the rendering machine at all, so the renderer substitutes a different typeface. Example: Georgia is a proprietary Microsoft font, not redistributable, absent from Linux containers (the claude.ai sandbox). LibreOffice silently substitutes Liberation or DejaVu, and the "Georgia body" never renders as Georgia.
2. Generation, font WRONG CUT. The font exists but only as a variable font, and the renderer misreads the weight axis. Example: a bare `Montserrat[wght].ttf` is read by LibreOffice and some Office installs as "Montserrat Thin", so headings render thin and the QA preview lies.
3. Distribution, recipient's machine. Even when generation renders true, the person who opens the file may not have the font. This is solved only by embedding (below), never by anything done on the generating machine.

Both generation problems share one cure: make the named font available on the rendering machine, as a usable static cut, before generating, and fail loudly if you cannot.

## Preflight (generation side): run before generating, fail loud

1. Confirm the brand font resolves to a real static cut (Regular and Bold at minimum). On Linux, `fc-match "<Family>:weight=bold"` must return that family, not a substitute.
2. If only a variable font is available, instance static cuts with fontTools (`instantiateVariableFont`). A variable file alone is the single most common cause of "the fonts do not fill the boxes": renderers default its weight axis to the thinnest master.
3. Install the static cuts (Linux: copy to `~/.fonts/` then `fc-cache -f`; macOS/Windows: install the .ttf files).
4. Verify resolution again. If the font still does not resolve, STOP with a non-zero exit and a clear message. Never mask a font install with `|| true`: a swallowed failure means the file renders wrong while the script reports success.
5. Only then trust the QA preview. If the brand font is substituted, the preview's text-fit is unreliable; install the font so the preview tells the truth, and still leave about 10% height slack on heading boxes.

`scripts/setup/font_preflight.py` implements steps 1 to 4 and exits non-zero when a font cannot be made available. Use it, or follow the same fail-loud shape inline.

## Substitution policy: metric-compatible only

When a font genuinely cannot be installed (a proprietary face on a headless Linux box), substitute only a *metric-compatible* replacement: one with the same em size, vertical metrics, and per-glyph advance widths, so line breaks and pagination are unchanged. A mere look-alike is not good enough; different advance widths reflow the text and move every line break.

The proven pair for this repo's serif brands:

| Proprietary font | Metric-compatible open substitute | Licence |
|------------------|-----------------------------------|---------|
| Georgia | **Gelasio** | OFL |
| Arial | Arimo | Apache |
| Times New Roman | Tinos | Apache |
| Courier New | Cousine | Apache |

Measured evidence for Georgia (fontTools, against the real Georgia, 2026-06-18): Gelasio matches Georgia at unitsPerEm 2048, x-height 0.481 em, cap-height 0.693 em, with 0.00% mean and 0.00% max advance-width difference across the ASCII charset, so a paragraph occupies the identical width. Lora, a look-alike proposed earlier, differed by up to 14.46% per glyph and made the same text 5.74% wider, moving line breaks. Use Gelasio, not Lora.

Gelasio ships from Google Fonts as a variable font only (`ofl/gelasio/Gelasio[wght].ttf`), so it must be instanced into static cuts exactly like any other variable font (see Preflight step 2).

### Headless Georgia substitution recipe (Linux / claude.ai sandbox)

```bash
# 1. Fetch Gelasio (variable) and instance static Regular + Bold cuts named plainly "Gelasio".
python scripts/setup/font_preflight.py --family Georgia --substitute Gelasio \
  --source-url "https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf" \
  --weights 400,700 --alias   # --alias writes the fontconfig Georgia->Gelasio mapping below

# Equivalent manual fontconfig alias, if you prefer to do it by hand:
cat > ~/.config/fontconfig/conf.d/99-georgia-gelasio.conf <<'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias binding="strong"><family>Georgia</family><prefer><family>Gelasio</family></prefer></alias>
</fontconfig>
EOF
fc-cache -f
fc-match "Georgia:weight=bold"   # MUST resolve to Gelasio; if it does not, stop and fix.
```

On a machine that has real Georgia (most Windows and macOS), nothing substitutes and Georgia renders directly. The substitution only engages where Georgia is absent.

## Distribution (recipient side): embedding, before it leaves your machine

Installing the font on the generating machine makes the file render true *there*. It does nothing for whoever opens it next. For anything you send outside your own machine, embed the fonts or ship a PDF:

- PDF embeds and subsets fonts automatically. For a send-only deliverable, exporting to PDF is the simplest guarantee. Verify with `pdffonts file.pdf`: every row should read `yes yes` under emb/sub.
- .pptx: pptxgenjs cannot embed fonts. Embed in PowerPoint (File, Options, Save, "Embed fonts in the file", choose "Embed all characters") or via a LibreOffice export, or send the deck as PDF.
- .docx: Word embeds via File, Options, Save, "Embed fonts in the file". Only embeddable fonts (most OFL/Apache faces, including Gelasio and Montserrat) travel this way; some proprietary fonts forbid embedding.

A correct file on a font-less machine, with no embedding, is the rough result the reader sees. Embedding is the only thing that makes it travel.

## Pitfalls (each of these has burned a real session)

1. Editing a brand file's "Fallback" column and assuming it changed rendering. That column is a human-readable note; no code reads it. The font actually applied is the `BRAND.body` / `BRAND.heading` token in the JavaScript.
2. `apt-get install -y <pkg> || true`. The `|| true` swallows a wrong package name or a failed install, so the font never lands and the render is still wrong while the script "succeeds." Make font installs fail loud.
3. Reaching for a look-alike (Lora) instead of a metric-compatible substitute (Gelasio). Looks similar, reflows differently.
4. Trusting the QA preview when the font is substituted or present only as a variable cut. Install the static cut first; then the preview tells the truth.
5. Assuming pptxgenjs (or any generator) can embed fonts. It cannot; embedding happens in the Office app or via PDF.
6. Confusing the generation-side fix with the distribution-side fix. Both are needed; neither replaces the other.

## Verification (do not trust, test)

- Reproduce absence: render on a box without the brand font, confirm the wrong typeface, apply the fix, confirm the right one.
- Metric check (for any substitution): compare unitsPerEm, x-height, cap-height, and per-glyph advance widths against the original; a true drop-in is near 0% difference.
- Embedding check: `pdffonts deliverable.pdf` shows emb=yes sub=yes for every row.
- Distribution check: open the file on a second machine without the brand font; the embedded or PDF path renders true, the bare path reflows.
