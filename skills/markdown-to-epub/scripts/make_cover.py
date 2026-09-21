#!/usr/bin/env python3
"""Make a branded EPUB cover image (PNG) for markdown-to-epub.

Composes a portrait cover: brand background + a square logo (which may itself carry
the wordmark, as the Magma logo does) + title + optional subtitle + a bottom block
with author and a DATE stamp (so multiple same-month versions are distinguishable).
Text is Montserrat when available. Defaults are the Magma identity; this is a
TEMPLATE - rebrand by swapping the logo (--logo / assets/<your-logo>.png) and the
colors (--bg / --title-color / --accent).

LAYOUT IS MEASURED, NOT FIXED (rewritten 2026-09-19 after a 7-word title produced a
cover with four separate defects on a Kindle: a 4-line title that pushed the subtitle
into the accent rule, an author line wider than the canvas clipped at both edges, and
a subtitle whose trailing month read as a duplicate of the date stamp). Every text
block now shrinks to fit its box, the bottom block's position is derived from its own
measured height rather than a hardcoded fraction of the page, and the middle block is
centered in whatever space is left. A title that cannot fit at the minimum size is
reported rather than drawn over something else.

Pandoc cannot build an image cover, so this is a distinct asset step, not a
conversion wrapper. Dependency: Pillow (pip install pillow). The core markdown->epub
conversion works without it; only covers need it.

Exit codes: 0 = wrote the cover; 2 = Pillow missing (prints install guidance).

Titles: short ones look better and the fitter cannot invent room. Four words or fewer
is the sweet spot at the default size; put the explanation in --subtitle, which is
what it is for.

Example:
  python make_cover.py --title "Marketing Skills Mastery" \
    --subtitle "Corey Haines - a practitioner's guide" --date 2026-07-21 --out cover.png
Then: pandoc note.md -f markdown+autolink_bare_uris -t epub3 \
        --epub-cover-image=cover.png --css ../epub.css -o note.epub
"""
import argparse, os, re, sys

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

_FONT_CACHE = {}

def load_font(bold, size):
    key = (bool(bold), int(size))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    primary = "Montserrat-Bold.ttf" if bold else "Montserrat-Regular.ttf"
    for candidate in (primary, "arialbd.ttf" if bold else "arial.ttf",
                      "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        p = find_font(candidate)
        if p:
            f = ImageFont.truetype(p, size)
            _FONT_CACHE[key] = f
            return f
    note("Montserrat not found; using Pillow's default face (off-brand). Install Montserrat for the branded look.")
    try:
        f = ImageFont.load_default(size=size)
    except TypeError:
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f

def wrap(draw, text, font, max_w):
    """Greedy wrap. A single word wider than the box gets its own line rather than
    being dropped, so the fitter below sees the overflow and shrinks."""
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

def fits(draw, lines, font, max_w):
    return all(draw.textlength(ln, font=font) <= max_w for ln in lines)

def fit_block(draw, text, bold, start, minimum, max_w, max_lines):
    """Largest size in [minimum, start] that wraps `text` into at most `max_lines`
    lines, each inside `max_w`. Returns (font, lines, hit_floor)."""
    size = int(start)
    minimum = max(8, int(minimum))
    while size >= minimum:
        font = load_font(bold, size)
        lines = wrap(draw, text, font, max_w)
        if len(lines) <= max_lines and fits(draw, lines, font, max_w):
            return font, lines, False
        size -= 2
    font = load_font(bold, minimum)
    return font, wrap(draw, text, font, max_w), True

def fit_one_line(draw, text, bold, start, minimum, max_w):
    """Largest size that keeps `text` on ONE line inside max_w. The old code never
    did this, which is how an author credit ended up clipped at both canvas edges."""
    size = int(start)
    minimum = max(8, int(minimum))
    while size >= minimum:
        font = load_font(bold, size)
        if draw.textlength(text, font=font) <= max_w:
            return font, False
        size -= 2
    return load_font(bold, minimum), True

def block_height(lines, font):
    return line_height(font) * len(lines)

def draw_centered(draw, lines, font, y, W, fill):
    lh = line_height(font)
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text(((W - w) / 2, y), ln, font=font, fill=fill)
        y += lh
    return y

_MONTHS = ("january february march april may june july august september october "
           "november december").split()

def subtitle_repeats_date(subtitle, date):
    """The 2026-09-19 defect: a caller ended the subtitle with 'September 2026' while
    the stamp read '2026-09-17', so the cover showed what looked like two dates. Warn,
    do not edit the caller's text."""
    if not subtitle:
        return False
    tail = subtitle.lower()[-24:]
    year = date[:4]
    if year and year in tail and any(m in tail for m in _MONTHS):
        return True
    return bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", subtitle))

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
    ap.add_argument("--title-scale", type=float, default=0.072,
                    help="Starting title size as a fraction of width. Lowered from 0.085 on "
                         "2026-09-19; the fitter shrinks from here, so raise it only for very short titles.")
    ap.add_argument("--title-max-lines", type=int, default=3)
    ap.add_argument("--subtitle-max-lines", type=int, default=2)
    a = ap.parse_args()

    date = a.date
    if not date:
        from datetime import date as _date
        date = _date.today().isoformat()

    if subtitle_repeats_date(a.subtitle, date):
        note("the subtitle appears to carry its own date while --date also stamps one; "
             "the cover will show both. Drop the date from --subtitle.")

    W, H = a.width, a.height
    img = Image.new("RGB", (W, H), a.bg)
    draw = ImageDraw.Draw(img)
    margin = int(W * 0.09)
    max_w = W - 2 * margin

    # ---- bottom block first: its height decides where the middle block may end ----
    author_font, author_floor = fit_one_line(draw, a.author, True, int(W * 0.040), int(W * 0.024), max_w)
    if author_floor:
        note(f"author credit is too long to fit on one line even at the minimum size: {a.author!r}")
    date_font = load_font(False, int(W * 0.032))
    gap_rule_author = int(H * 0.020)
    gap_author_date = int(H * 0.004)
    bottom_h = gap_rule_author + line_height(author_font) + gap_author_date + line_height(date_font)
    bottom_margin = int(H * 0.055)
    rule_y = H - bottom_margin - bottom_h

    # ---- middle block: logo + title + subtitle, measured then centered ----
    top = int(H * 0.085)
    avail = rule_y - int(H * 0.035) - top

    logo_img, logo_w, logo_h = None, 0, 0
    if a.logo and os.path.isfile(a.logo):
        logo_img = Image.open(a.logo).convert("RGBA")
        logo_w = int(W * 0.62)
        logo_h = int(logo_w * logo_img.height / logo_img.width)
    else:
        note(f"logo not found at {a.logo}; skipping it.")

    gap_logo_title = int(H * 0.045)
    gap_title_sub = int(H * 0.022)

    def measure(title_scale, logo_scale):
        lh = int(logo_h * logo_scale)
        tf, tl, tfloor = fit_block(draw, a.title, True, int(W * title_scale),
                                   int(W * 0.040), max_w, a.title_max_lines)
        total = (lh + gap_logo_title if lh else 0) + block_height(tl, tf)
        sf = sl = None
        if a.subtitle:
            sf, sl, _ = fit_block(draw, a.subtitle, False, int(W * 0.036),
                                  int(W * 0.024), max_w, a.subtitle_max_lines)
            total += gap_title_sub + block_height(sl, sf)
        return total, lh, tf, tl, tfloor, sf, sl

    title_scale, logo_scale = a.title_scale, 1.0
    total, lh, tf, tl, tfloor, sf, sl = measure(title_scale, logo_scale)
    # Shrink the logo before the type: the wordmark survives scaling better than a
    # title does, and a cramped title is what made the Kindle cover unreadable.
    while total > avail and logo_scale > 0.55:
        logo_scale -= 0.05
        total, lh, tf, tl, tfloor, sf, sl = measure(title_scale, logo_scale)
    while total > avail and title_scale > 0.042:
        title_scale -= 0.004
        total, lh, tf, tl, tfloor, sf, sl = measure(title_scale, logo_scale)

    if total > avail:
        note("title and subtitle do not fit even at the minimum sizes; shorten the title "
             "(four words or fewer is the sweet spot) or move words into --subtitle.")
    if tfloor:
        note(f"title hit the minimum size and still wraps past {a.title_max_lines} lines: {a.title!r}")

    y = top + max(0, (avail - total) // 2)
    if lh and logo_img is not None:
        lw = int(logo_w * logo_scale)
        resized = logo_img.resize((lw, lh), Image.LANCZOS)
        img.paste(resized, ((W - lw) // 2, y), resized)
        y += lh + gap_logo_title
    y = draw_centered(draw, tl, tf, y, W, a.title_color)
    if sl:
        y += gap_title_sub
        y = draw_centered(draw, sl, sf, y, W, a.subtitle_color)

    # ---- bottom block ----
    draw.line([(margin, rule_y), (W - margin, rule_y)], fill=a.accent, width=6)
    ay = rule_y + gap_rule_author
    w = draw.textlength(a.author, font=author_font)
    draw.text(((W - w) / 2, ay), a.author, font=author_font, fill=a.title_color)
    ay += line_height(author_font) + gap_author_date
    w = draw.textlength(date, font=date_font)
    draw.text(((W - w) / 2, ay), date, font=date_font, fill=a.accent)

    out_dir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(out_dir, exist_ok=True)
    img.save(a.out)
    note(f"wrote {a.out} ({W}x{H}) title={a.title!r} lines={len(tl)} "
         f"title_px={tf.size} date={date}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
