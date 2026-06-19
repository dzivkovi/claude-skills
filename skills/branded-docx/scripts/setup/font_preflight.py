#!/usr/bin/env python3
"""Font preflight: ensure a brand font is available as usable STATIC cuts before generating.

It fails LOUD (non-zero exit) when a font cannot be made available, so a render never
silently proceeds with a substituted typeface. See references/font-fidelity.md for the doctrine.

Exit codes: 0 = the font resolves; 2 = it cannot be made available (hard fail);
3 = static cuts were instanced but need a manual OS install (Windows) before they resolve.

Examples:
  python font_preflight.py --family Montserrat
  python font_preflight.py --family Georgia --substitute Gelasio \
      --source-url "https://raw.githubusercontent.com/google/fonts/main/ofl/gelasio/Gelasio%5Bwght%5D.ttf" \
      --weights 400,700 --alias
  python font_preflight.py --family Gelasio --source-url <url> --out-dir /tmp/f --no-install  # test/CI
"""
import argparse, os, platform, shutil, subprocess, sys, tempfile, urllib.request
from xml.sax.saxutils import escape as xml_escape

SFNT_MAGIC = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf", b"wOFF", b"wOF2")

def log(msg): print(f"[font-preflight] {msg}", file=sys.stderr)
def die(msg, code=2):
    log(f"FAIL: {msg}")
    sys.exit(code)

def safe_name(value, what):
    """A font family name, not a path. Reject separators / traversal so it cannot redirect a write."""
    if value is None:
        return
    if "/" in value or "\\" in value or os.sep in value or (os.altsep and os.altsep in value) or ".." in value:
        die(f"invalid {what} {value!r}: expected a font family name, not a path")

def font_dirs():
    sys_name = platform.system()
    if sys_name == "Windows":
        return [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
                os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")]
    if sys_name == "Darwin":
        return [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts"]
    return [os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
            "/usr/share/fonts", "/usr/local/share/fonts"]

def resolves_static(family, expect=None):
    """True only if a query for `family` resolves to usable STATIC Regular AND Bold cuts.

    `expect` covers the Linux alias case: after aliasing Georgia->Gelasio, a query for Georgia
    must resolve to Gelasio, so we check the resolved family equals `expect`, not `family`.
    """
    want = expect or family
    from fontTools.ttLib import TTFont
    # Linux: fontconfig is authoritative (it is what LibreOffice consults). fc-match always
    # returns its BEST match and never fails: an absent family yields a substitute with a
    # different name, and a weight with no real cut is served by the nearest file. So require
    # an exact family match, a non-variable face, AND that regular and bold resolve to DIFFERENT
    # files (same file for both => only one weight is really installed).
    if platform.system() == "Linux" and shutil.which("fc-match"):
        def face(weight):
            out = subprocess.run(["fc-match", "-f", "%{family}|%{variable}|%{file}", f"{family}:weight={weight}"],
                                 capture_output=True, text=True).stdout
            parts = (out.split("|") + ["", "", ""])[:3]
            fam, var, path = parts
            fam_ok = any(want.strip().lower() == p.strip().lower() for p in fam.split(","))
            return fam_ok, (var.strip().lower() not in ("true", "1")), path.strip()
        rfam, rstatic, rfile = face("regular")
        bfam, bstatic, bfile = face("bold")
        return rfam and bfam and rstatic and bstatic and rfile and rfile != bfile
    # Windows/macOS: scan font dirs for static faces named `want`; require both a regular-weight
    # and a bold-weight cut (a partial install must not pass).
    found_regular = found_bold = False
    for d in font_dirs():
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.lower().endswith((".ttf", ".otf", ".ttc")):
                continue
            try:
                f = TTFont(os.path.join(d, fn), fontNumber=0, lazy=True)
                if "fvar" in f:
                    continue
                names = {f["name"].getDebugName(1) or "", f["name"].getDebugName(16) or ""}
                if not any(want.lower() == (n or "").lower() for n in names):
                    continue
                ws = f["OS/2"].usWeightClass
                if ws <= 500: found_regular = True
                if ws >= 600: found_bold = True
            except Exception:
                continue
    return found_regular and found_bold

def instance_static(src, family, weights, out_dir):
    """Instance static cuts at each weight from a variable font; return list of paths."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    os.makedirs(out_dir, exist_ok=True)
    made = []
    names = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}
    for w in weights:
        sub = names.get(w, str(w))
        f = TTFont(src)
        if "fvar" not in f:
            die(f"{src} is not a variable font; cannot instance weight {w}")
        # Pin wght to the request and every other axis to its default, so a multi-axis font
        # still produces a fully static instance.
        location = {a.axisTag: a.defaultValue for a in f["fvar"].axes}
        location["wght"] = w
        instantiateVariableFont(f, location, inplace=True)
        if "fvar" in f:
            die(f"instancing left an 'fvar' table in the {family} {sub} cut; not static")
        n = f["name"]
        for nid, val in [(1, family), (2, sub), (4, f"{family} {sub}"), (6, f"{family}-{sub}"),
                         (16, family), (17, sub)]:
            n.setName(val, nid, 3, 1, 0x409); n.setName(val, nid, 1, 0, 0)
        o, h = f["OS/2"], f["head"]
        o.usWeightClass = w
        o.fsSelection &= ~0x60  # clear BOLD (0x20) and REGULAR (0x40)
        if w == 400:   o.fsSelection |= 0x40; h.macStyle &= ~0x01      # REGULAR
        elif w >= 700: o.fsSelection |= 0x20; h.macStyle |= 0x01       # BOLD
        else:          h.macStyle &= ~0x01                              # intermediate: neither bit
        out = os.path.join(out_dir, f"{family}-{sub}.ttf")
        f.save(out); made.append(out)
        log(f"instanced {family} {sub} ({w}) -> {out}")
    return made

def install(paths):
    """Copy cuts into the user font path. Returns True if the OS auto-registers them (Linux/macOS),
    False on Windows where an explicit per-user install is required."""
    sys_name = platform.system()
    if sys_name == "Windows":
        return False
    target = font_dirs()[0]
    os.makedirs(target, exist_ok=True)
    for p in paths:
        shutil.copy2(p, os.path.join(target, os.path.basename(p)))
        log(f"installed {os.path.basename(p)} -> {target}")
    if sys_name == "Linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=False)
    return True

def write_alias(family, substitute):
    """Map family->substitute via fontconfig (Linux only). Returns True if an alias was written."""
    if platform.system() != "Linux":
        log(f"alias is Linux-only; on this OS install {substitute} or set the brand font to it directly")
        return False
    conf_dir = os.path.expanduser("~/.config/fontconfig/conf.d")
    os.makedirs(conf_dir, exist_ok=True)
    path = os.path.join(conf_dir, f"99-{family.lower()}-{substitute.lower()}.conf")
    with open(path, "w") as fh:
        fh.write('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n'
                 f'  <alias binding="strong"><family>{xml_escape(family)}</family>'
                 f'<prefer><family>{xml_escape(substitute)}</family></prefer></alias>\n</fontconfig>\n')
    if shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=False)
    log(f"wrote alias {family} -> {substitute} ({path})")
    return True

def fetch(url):
    fd, tmp = tempfile.mkstemp(suffix=".ttf"); os.close(fd)
    log(f"downloading {url}")
    try:
        urllib.request.urlretrieve(url, tmp)
    except Exception as e:
        die(f"could not download {url}: {e}")
    with open(tmp, "rb") as fh:
        magic = fh.read(4)
    if magic not in SFNT_MAGIC:
        die(f"downloaded file from {url} is not a font (leading bytes {magic!r}); an error page, perhaps?")
    return tmp

def main():
    ap = argparse.ArgumentParser(description="Ensure a brand font is available as static cuts; fail loud if not.")
    ap.add_argument("--family", required=True, help="Brand font family name as the document declares it")
    ap.add_argument("--substitute", help="Metric-compatible substitute family when --family is absent (e.g. Gelasio for Georgia)")
    ap.add_argument("--source-url", help="URL of the variable font to instance (the family or its substitute)")
    ap.add_argument("--source-file", help="Local variable font to instance instead of downloading")
    ap.add_argument("--weights", default="400,700", help="Comma-separated weights to instance (default 400,700)")
    ap.add_argument("--alias", action="store_true", help="Write a fontconfig alias family->substitute (Linux). Requires --substitute.")
    ap.add_argument("--out-dir", help="Where to write instanced cuts (default: a temp dir)")
    ap.add_argument("--no-install", action="store_true", help="Instance only; do not install into the font path")
    args = ap.parse_args()

    safe_name(args.family, "--family")
    safe_name(args.substitute, "--substitute")
    if args.alias and not args.substitute:
        die("--alias requires --substitute (it maps --family to the substitute)")

    weights = [int(w) for w in args.weights.split(",") if w.strip()]
    target_family = args.substitute or args.family

    # 1. Declared font already present as static Regular+Bold cuts? Then we are done.
    if resolves_static(args.family):
        log(f"OK: {args.family} resolves to static cuts on this machine; nothing to do.")
        return 0

    # 2. Not available. We need a source to make it available, else fail loud.
    if not (args.source_url or args.source_file):
        die(f"{args.family} is not available as static cuts and no --source-url/--source-file was given. "
            f"Provide a metric-compatible substitute source (e.g. Gelasio for Georgia) or install the font.")

    # 3. Ensure the target's static cuts exist (skip instancing if already installed).
    if args.substitute and resolves_static(args.substitute):
        log(f"{target_family} already installed; skipping instancing.")
    else:
        src = args.source_file or fetch(args.source_url)
        out_dir = args.out_dir or tempfile.mkdtemp(prefix="font-preflight-")
        made = instance_static(src, target_family, weights, out_dir)
        if args.no_install:
            log(f"instanced {len(made)} cut(s) into {out_dir} (not installed, --no-install).")
            return 0
        if not install(made):
            die(f"instanced {len(made)} static cut(s) of {target_family} in {out_dir}. On Windows, install "
                f"them now (select the .ttf files, right-click > Install for all users), then re-run this "
                f"preflight to confirm. Until installed, {args.family} will not render as designed.", code=3)

    # 4. Alias so the declared family resolves to the substitute (Linux only).
    alias_written = write_alias(args.family, args.substitute) if (args.substitute and args.alias) else False

    # 5. Verify, and FAIL LOUD. In substitute mode the DECLARED family must resolve (via the alias),
    #    not merely the substitute being installed.
    if args.substitute:
        if alias_written:
            ok = resolves_static(args.family, expect=target_family)
        else:
            ok = resolves_static(args.family)  # no alias: the declared family must already resolve
        detail = f"{args.family} (via {target_family})" if alias_written else args.family
        if not ok and not alias_written:
            die(f"{target_family} is installed but {args.family} still does not resolve. On Linux, re-run "
                f"with --alias to map {args.family} to {target_family}; on Windows/macOS, set the brand "
                f"font token to {target_family} directly, or install the real {args.family}.")
    else:
        ok = resolves_static(args.family)
        detail = args.family
    if not ok:
        die(f"after setup, {detail} does not resolve to static cuts. "
            f"Do not generate: the render would substitute a wrong typeface.")
    log(f"OK: {detail} is installed as static cuts and resolves.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
