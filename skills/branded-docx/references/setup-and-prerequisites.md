# Prerequisites and Setup

This document covers everything you need before your first branded document generates correctly.

---

## Quick checklist

- [ ] Node.js installed (`node --version` in terminal to check)
- [ ] `docx` npm package installed (`npm install -g docx`)
- [ ] Poppins font installed on your machine
- [ ] Georgia font installed (Windows built-in, usually already present)

---

## 1. Node.js

The skill generates `.docx` files via a JavaScript script. Node.js is required.

Check: open a terminal and run:
```
node --version
```

If you get a version number (e.g. `v20.11.0`), you are set.
If you get "command not found", download and install from: https://nodejs.org (choose the LTS version)

---

## 2. docx npm package

```bash
npm install -g docx
```

Run once. Verify with:
```bash
npm list -g docx
```

---

## 3. Fonts (Poppins + Georgia)

Branded documents use two fonts:

| Font | Role | Status |
|------|------|--------|
| Georgia | Body text (all paragraphs) | Windows built-in - likely already present |
| Poppins | Headings, labels, captions | Must be installed manually |

**Why this matters:** If Poppins is missing, Word silently falls back to Arial. The document still opens and reads fine, but headings lose their character. Install once and forget about it.

### Windows - automated install

A PowerShell script is bundled with this skill at `scripts/setup/install-fonts-windows.ps1`.

Steps:
1. Open File Explorer and navigate to the `scripts/setup/` folder inside the skill directory
2. Right-click `install-fonts-windows.ps1`
3. Choose "Run with PowerShell"
4. If Windows shows a security prompt, click **Yes**
5. The script prints what it found, downloads what is missing, and exits
6. Restart Word if it was already open

The script downloads only from Google's official GitHub repository (`raw.githubusercontent.com/google/fonts`) and installs per-user if it cannot write system-wide.

### Mac - manual install

1. Go to https://fonts.google.com/specimen/Poppins
2. Click "Download family" (top right)
3. Unzip the downloaded file
4. Select all `.ttf` files, right-click, choose "Open" (or double-click each and click "Install Font")
5. Restart Word

### Linux

```bash
mkdir -p ~/.fonts
cd ~/.fonts
for weight in Regular Bold SemiBold Italic BoldItalic; do
  curl -Lo "Poppins-${weight}.ttf" \
    "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-${weight}.ttf"
done
fc-cache -fv
```

---

## 4. Validating after document generation

After Claude generates a `.docx` file using this skill, it runs:

```bash
python scripts/office/validate.py output.docx
```

This checks that the XML inside the file is well-formed and Word will open it without repair prompts. If validation fails, Claude will unpack, fix, and repack automatically before handing you the file.

You do not need to run this yourself - it is part of the skill's generation flow.

---

## What to expect (sample output)

A sample document is bundled in `assets/branded-sample.docx`. Open it to see exactly what the brand system looks like before asking Claude to generate your first real document.

What you will see:
- Cover page with coral accent bar, large Poppins title, Georgia subtitle
- Chapter heading in coral with underline border
- Body copy in Georgia, generous line spacing
- Left-bordered callout block with coral label
- Data table with near-black header row, alternating light gray rows
- Header with document title left, page number right (in coral)
- Footer with light rule and muted label

If the sample looks correct on your machine (fonts rendering, colours matching), you are ready to go.

---

## Troubleshooting

**Headings look like Arial, not Poppins**
Poppins is not installed. Run the setup script above and restart Word.

**Document opens with a repair prompt**
Usually caused by an incomplete generation. Ask Claude to regenerate - it validates automatically.

**Georgia body text looks different from the sample**
Georgia renders slightly differently across Windows versions and display DPI settings. This is expected and does not affect the brand integrity.
