#!/usr/bin/env python3
"""Bundle ordered markdown files into book-build inputs: per-file parts for the
EPUB build, a single-file agent edition with provenance frontmatter, and a
frontmatter-free print edition for the PDF renderer.

Stdlib only. See the markdown-to-book SKILL.md for the full recipe this serves.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

# Strip repo-local link TARGETS, keep the text. Web URLs and #anchors survive.
# In a standalone bundle a relative link is a dead link; the text still names
# the referenced chapter, which is what a linear reader needs.
LOCAL_LINK = re.compile(r"\[([^\]]+)\]\((?!https?://|#)[^)]+\)")
H1 = re.compile(r"^# .+$", re.MULTILINE)


def git_origin(path: Path) -> str | None:
    """repo-root@short-commit for path, or None when not in git."""
    try:
        root = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
        commit = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        return f"{Path(root).name}@{commit} ({root})"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def preprocess(text: str, retitle: str | None) -> str:
    text = LOCAL_LINK.sub(r"\1", text)
    if retitle:
        text = H1.sub(f"# {retitle}", text, count=1)
    return text.strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sources", nargs="+", help="markdown files in reading order")
    ap.add_argument("--title", required=True)
    ap.add_argument("--thread", required=True,
                    help="one line: why this bundle exists / what it equips the reader for")
    ap.add_argument("--basename", required=True, help="output basename, no extension")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--intro-retitle", default=None,
                    help="replace the FIRST file's H1 (e.g. 'Introduction: why this book exists')")
    ap.add_argument("--builder", default="Claude Code session",
                    help="who/what built this bundle, for the provenance header")
    args = ap.parse_args()

    out = Path(args.out_dir)
    parts_dir = out / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    sources = [Path(s) for s in args.sources]
    missing = [s for s in sources if not s.is_file()]
    if missing:
        sys.exit(f"missing source files: {', '.join(map(str, missing))}")

    bodies: list[str] = []
    part_paths: list[Path] = []
    for i, src in enumerate(sources):
        body = preprocess(src.read_text(encoding="utf-8"),
                          args.intro_retitle if i == 0 else None)
        if not H1.search(body):
            print(f"warning: {src} has no H1; its TOC entry will be poor", file=sys.stderr)
        part = parts_dir / f"{i:02d}-{src.name}"
        part.write_text(body, encoding="utf-8", newline="\n")
        part_paths.append(part)
        bodies.append(body.strip())

    today = dt.date.today().isoformat()
    origin = git_origin(sources[0]) or str(sources[0].parent.resolve())
    consumes = "\n".join(f"    - {s.as_posix()}" for s in sources)
    frontmatter = (
        "---\n"
        f"title: {args.title}\n"
        "edition: agent single-file context handoff (siblings: .epub reading edition, .pdf print edition)\n"
        f"built: {today}\n"
        "provenance:\n"
        f"  created_by: {args.builder}\n"
        f"  origin: {origin}\n"
        "  consumes:\n"
        f"{consumes}\n"
        f"  thread: {args.thread}\n"
        "---\n\n"
    )

    combined = "\n\n".join(bodies) + "\n"
    agent_md = out / f"{args.basename}.md"
    print_md = out / f"{args.basename}-print.md"
    agent_md.write_text(frontmatter + combined, encoding="utf-8", newline="\n")
    print_md.write_text(combined, encoding="utf-8", newline="\n")

    print(f"parts:  {parts_dir}  ({len(part_paths)} files)")
    print(f"agent:  {agent_md}")
    print(f"print:  {print_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
