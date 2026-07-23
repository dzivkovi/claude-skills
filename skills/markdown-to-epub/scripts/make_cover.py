#!/usr/bin/env python3
"""Make a branded EPUB cover image (PNG) for markdown-to-epub.

Composes a portrait cover: brand background + a square logo (which may itself carry
the wordmark, as the Magma logo does) + title + optional subtitle + a bottom block
with author and a DATE stamp (so multiple same-month versions are distinguishable).
Text is Montserrat when available. Defaults are the Magma identity; this is a
TEMPLATE - rebrand by swapping the logo (--logo / assets/<your-logo>.png) and the
colors (--bg / --title-color / --accent).

Pandoc cannot build an image cover, so this is a distinct asset step, not a
conversion wrapper. Dependency: Pillow (pip install pillow). The core markdown->epub
conversion works without it; only covers need it.

Exit codes: 0 = wrote the cover; 2 = Pillow missing (prints install guidance).

Example:
  python make_cover.py --title "Marketing Skills Mastery" \
    --subtitle "Corey Haines - a practitioner's guide" --date 2026-07-21 --out cover.png
Then: pandoc note.md -f markdown+autolink_bare_uris -t epub3 \
        --epub-cover-image=cover.png --css ../epub.css -o note.epub
"""
import argparse, os, sys

def note(msg): print(f"[make-cover] {msg}", file=sys.stderr)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    note("Pillow is not installed. Covers need it: pip install pillow "
         "(core markdown->epub still works without a cover).")
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOGO = os.path.normpath(os.path.join(HERE, "..", "assets", "magma-square-1024-dark.png"))

FONT_DIRS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
    os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts",
    os.path.expanduser("~/.local/share/fonts"), os.path.expanduser("~/.fonts"),
    "/usr/share/fonts", "/usr/local/share/fonts",
]

def find_font(filename):
    for d in FONT_DIRS:
        p = os.path.join(d, filename)
        if os.path.isfile(p):
            return p
    for d in ("/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.local/share/fonts")):
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                if filename in files:
                    return os.path.join(root, filename)
    return None

def load_font(bold, size):
    primary = "Montserrat-Bold.ttf" if bold else "Montserrat-Regular.ttf"
    for candidate in (primary, "arialbd.ttf" if bold else "arial.ttf",
                      "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        p = find_font(candidate)
        if p:
            return ImageFont.truetype(p, size)
    note("Montserrat not found; using Pillow's default face (off-brand). Install Montserrat for the branded look.")
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur:
        lines.append(cur)
    return lines

def line_height(font, gap=1.15):
    asc, desc = font.getmetrics()
    return int((asc + desc) * gap)

def draw_centered(draw, lines, font, y, W, fill):
    lh = line_height(font)
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text(((W - w) / 2, y), ln, font=font, fill=fill)
        y += lh
    return y

def main():
    ap = argparse.ArgumentParser(description="Branded EPUB cover image generator (template; Magma defaults).")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--date", default=None, help="Version stamp on the cover (default: today, YYYY-MM-DD).")
    ap.add_argument("--author", default="Daniel Zivkovic")
    ap.add_argument("--logo", default=DEFAULT_LOGO, help="Square logo PNG (may include the wordmark). Swap to rebrand.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bg", default="#0C2749", help="Background hex (default Magma navy).")
    ap.add_argument("--title-color", default="#FFFFFF")
    ap.add_argument("--subtitle-color", default="#A3D4F2")
    ap.add_argument("--accent", default="#E2412F", help="Accent hex for the rule + date (default Signal Red on navy).")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=2560)
    a = ap.parse_args()

    date = a.date
    if not date:
        from datetime import date as _date
        date = _date.today().isoformat()

    W, H = a.width, a.height
    img = Image.new("RGB", (W, H), a.bg)
    draw = ImageDraw.Draw(img)
    margin = int(W * 0.09)
    max_w = W - 2 * margin

    y = int(H * 0.10)
    if a.logo and os.path.isfile(a.logo):
        logo = Image.open(a.logo).convert("RGBA")
        lw = int(W * 0.62)
        lh = int(lw * logo.height / logo.width)
        logo = logo.resize((lw, lh), Image.LANCZOS)
        img.paste(logo, ((W - lw) // 2, y), logo)
        y += lh + int(H * 0.05)
    else:
        note(f"logo not found at {a.logo}; skipping it.")
        y = int(H * 0.22)

    title_font = load_font(True, int(W * 0.085))
    y = draw_centered(draw, wrap(draw, a.title, title_font, max_w), title_font, y, W, a.title_color)

    if a.subtitle:
        y += int(H * 0.02)
        sub_font = load_font(False, int(W * 0.038))
        draw_centered(draw, wrap(draw, a.subtitle, sub_font, max_w), sub_font, y, W, a.subtitle_color)

    by = int(H * 0.88)
    draw.line([(margin, by), (W - margin, by)], fill=a.accent, width=6)
    author_font = load_font(True, int(W * 0.040))
    date_font = load_font(False, int(W * 0.034))
    ay = by + int(H * 0.02)
    w = draw.textlength(a.author, font=author_font)
    draw.text(((W - w) / 2, ay), a.author, font=author_font, fill=a.title_color)
    ay += line_height(author_font) + int(H * 0.004)
    w = draw.textlength(date, font=date_font)
    draw.text(((W - w) / 2, ay), date, font=date_font, fill=a.accent)

    out_dir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(out_dir, exist_ok=True)
    img.save(a.out)
    note(f"wrote {a.out} ({W}x{H}) title={a.title!r} date={date}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
