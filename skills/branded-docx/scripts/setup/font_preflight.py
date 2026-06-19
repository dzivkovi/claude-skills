#!/usr/bin/env python3
"""Font preflight: ensure a brand font is available as usable STATIC cuts before generating.

It fails LOUD (non-zero exit) when a font cannot be made available, so a render never
silently proceeds with a substituted typeface. See references/font-fidelity.md for the doctrine.

Examples:
  # Verify the brand font is present as static cuts (exit 0) or fail (non-zero):
  python font_preflight.py --family Montserrat

  # Headless substitution: instance static Gelasio for an absent Georgia, install + alias (Linux):
  python font_preflight.py --family Georgia --substitute Gelasio \
      --source-url "https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf" \
      --weights 400,700 --alias

  # Instance into a directory without installing (for testing / CI):
  python font_preflight.py --family Gelasio --source-url <url> --out-dir /tmp/f --no-install
"""
import argparse, os, platform, shutil, subprocess, sys, tempfile, urllib.request

def log(msg): print(f"[font-preflight] {msg}", file=sys.stderr)
def die(msg, code=2):
    log(f"FAIL: {msg}")
    sys.exit(code)

def font_dirs():
    sys_name = platform.system()
    if sys_name == "Windows":
        return [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
                os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")]
    if sys_name == "Darwin":
        return [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts"]
    return [os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
            "/usr/share/fonts", "/usr/local/share/fonts"]

def resolves_static(family):
    """True only if `family` is available as a non-variable (static) face on this machine."""
    from fontTools.ttLib import TTFont
    # Linux: trust fontconfig first (matches what LibreOffice will do).
    if platform.system() == "Linux" and shutil.which("fc-match"):
        out = subprocess.run(["fc-match", "-f", "%{family}|%{variable}", f"{family}:weight=bold"],
                             capture_output=True, text=True).stdout
        fam, _, var = out.partition("|")
        if family.lower() not in fam.lower():
            return False
        return var.strip().lower() not in ("true", "1")
    # Windows/macOS: scan font dirs for a static face whose family name matches.
    for d in font_dirs():
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.lower().endswith((".ttf", ".otf", ".ttc")):
                continue
            try:
                f = TTFont(os.path.join(d, fn), fontNumber=0, lazy=True)
                names = {f["name"].getDebugName(1) or "", f["name"].getDebugName(16) or ""}
                if any(family.lower() == (n or "").lower() for n in names) and "fvar" not in f:
                    return True
            except Exception:
                continue
    return False

def instance_static(src, family, weights, out_dir):
    """Instance static cuts at each weight from a variable font; return list of paths."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    os.makedirs(out_dir, exist_ok=True)
    made = []
    names = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}
    for w in weights:
        sub = names.get(w, str(w))
        bold = w >= 700
        f = TTFont(src)
        if "fvar" not in f:
            die(f"{src} is not a variable font; cannot instance weight {w}")
        instantiateVariableFont(f, {"wght": w}, inplace=True)
        n = f["name"]
        for nid, val in [(1, family), (2, sub), (4, f"{family} {sub}"), (6, f"{family}-{sub}"),
                         (16, family), (17, sub)]:
            n.setName(val, nid, 3, 1, 0x409); n.setName(val, nid, 1, 0, 0)
        o, h = f["OS/2"], f["head"]
        if bold: o.fsSelection = (o.fsSelection & ~0x40) | 0x20; h.macStyle |= 0x01
        else:    o.fsSelection = (o.fsSelection & ~0x20) | 0x40; h.macStyle &= ~0x01
        out = os.path.join(out_dir, f"{family}-{sub}.ttf")
        f.save(out); made.append(out)
        log(f"instanced {family} {sub} ({w}) -> {out}")
    return made

def install(paths):
    target = font_dirs()[0]
    os.makedirs(target, exist_ok=True)
    for p in paths:
        shutil.copy2(p, os.path.join(target, os.path.basename(p)))
        log(f"installed {os.path.basename(p)} -> {target}")
    if platform.system() == "Linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=False)

def write_alias(family, substitute):
    if platform.system() != "Linux":
        log(f"alias is Linux-only; on this OS install {substitute} so {family} substitutes naturally")
        return
    conf_dir = os.path.expanduser("~/.config/fontconfig/conf.d")
    os.makedirs(conf_dir, exist_ok=True)
    path = os.path.join(conf_dir, f"99-{family.lower()}-{substitute.lower()}.conf")
    with open(path, "w") as fh:
        fh.write('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n'
                 f'  <alias binding="strong"><family>{family}</family>'
                 f'<prefer><family>{substitute}</family></prefer></alias>\n</fontconfig>\n')
    if shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=False)
    log(f"wrote alias {family} -> {substitute} ({path})")

def fetch(url):
    fd, tmp = tempfile.mkstemp(suffix=".ttf"); os.close(fd)
    log(f"downloading {url}")
    urllib.request.urlretrieve(url, tmp)
    return tmp

def main():
    ap = argparse.ArgumentParser(description="Ensure a brand font is available as static cuts; fail loud if not.")
    ap.add_argument("--family", required=True, help="Brand font family name as the document declares it")
    ap.add_argument("--substitute", help="Metric-compatible substitute family when --family is absent (e.g. Gelasio for Georgia)")
    ap.add_argument("--source-url", help="URL of the variable font to instance (the family or its substitute)")
    ap.add_argument("--source-file", help="Local variable font to instance instead of downloading")
    ap.add_argument("--weights", default="400,700", help="Comma-separated weights to instance (default 400,700)")
    ap.add_argument("--alias", action="store_true", help="Write a fontconfig alias family->substitute (Linux)")
    ap.add_argument("--out-dir", help="Where to write instanced cuts (default: a temp dir)")
    ap.add_argument("--no-install", action="store_true", help="Instance only; do not install into the font path")
    args = ap.parse_args()

    weights = [int(w) for w in args.weights.split(",") if w.strip()]
    target_family = args.substitute or args.family

    # 1. Already available as static cuts? Then we are done.
    if resolves_static(args.family) or (args.substitute and resolves_static(args.substitute)):
        log(f"OK: {args.family} resolves to a static cut on this machine; nothing to do.")
        return 0

    # 2. Not available. We need a source to make it available, else fail loud.
    if not (args.source_url or args.source_file):
        die(f"{args.family} is not available as static cuts and no --source-url/--source-file was given. "
            f"Provide a metric-compatible substitute source (e.g. Gelasio for Georgia) or install the font.")

    src = args.source_file or fetch(args.source_url)
    out_dir = args.out_dir or tempfile.mkdtemp(prefix="font-preflight-")
    made = instance_static(src, target_family, weights, out_dir)

    if args.no_install:
        log(f"instanced {len(made)} cut(s) into {out_dir} (not installed, --no-install).")
        return 0

    install(made)
    if args.substitute and args.alias:
        write_alias(args.family, args.substitute)

    # 3. Verify, and FAIL LOUD if the font still does not resolve.
    if not (resolves_static(args.family) or resolves_static(target_family)):
        die(f"after install, neither {args.family} nor {target_family} resolves to a static cut. "
            f"Do not generate: the render would substitute a wrong typeface.")
    log(f"OK: {target_family} is now installed as static cuts and resolves.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
