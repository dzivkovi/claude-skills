#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Prepare a Markdown file for publishing to Confluence Cloud via the Atlassian MCP.

The Atlassian MCP accepts `contentFormat: "markdown"` and converts headings, tables,
code blocks, lists, blockquotes, links, and images to native Confluence storage format
on its own. Only two things need doing first, and this script does both:

  1. Mermaid fences become rendered PNG images. Confluence turns a ```mermaid fence
     into a code macro showing the source, not a diagram, unless a Mermaid app is
     installed on the site. Rendering locally avoids that dependency entirely.
  2. The leading H1 is lifted out, because the page title is a separate argument to
     the MCP call rather than part of the body.

Usage:
    uv run prepare_confluence_markdown.py docs/architecture.md
    uv run prepare_confluence_markdown.py docs/architecture.md --out /tmp/page.md
    uv run prepare_confluence_markdown.py docs/architecture.md --images placeholders

Output: a sibling `<name>.confluence.md` (or --out), plus PNGs beside it, plus a
report on stdout naming the title, the body size, and whether the body is small
enough to pass through an MCP tool call comfortably.
"""

from __future__ import annotations

import argparse
import base64
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MERMAID_FENCE = re.compile(r"^```mermaid[^\n]*\n(.*?)^```[ \t]*$", re.DOTALL | re.MULTILINE)
LEADING_H1 = re.compile(r"\A\s*#\s+(?P<title>[^\n]+)\n", re.MULTILINE)

# Every byte of an inlined data URI travels through the MCP tool call, costing roughly
# a token per four bytes of the agent's context. Past this, use placeholders instead.
INLINE_BUDGET_BYTES = 60_000


def find_mmdc() -> str:
    """Locate the mermaid CLI, or exit with an actionable message."""
    for name in ("mmdc", "mmdc.cmd"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit(
        "mermaid-cli (mmdc) not found in PATH.\n"
        "Install it with: npm install -g @mermaid-js/mermaid-cli"
    )


def render_diagrams(text: str, out_dir: Path, stem: str, mode: str) -> tuple[str, list[Path]]:
    """Replace every mermaid fence with an image reference, rendering it to PNG first.

    Three modes, trading body size against manual effort:

      inline       data URI in the body. No attachments, no API token, nothing to do
                   by hand, but the body grows by about 1.35x the PNG bytes and every
                   one of those bytes travels through the MCP tool call.
      placeholders an info panel naming the PNG, which the author drags into the
                   Confluence editor afterwards. Smallest body by far, and the PNGs
                   are already rendered and waiting on disk.
      files        a plain filename reference, for a pipeline that uploads the PNGs
                   as page attachments over the REST API.
    """
    mmdc = find_mmdc()
    written: list[Path] = []
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        png = out_dir / f"{stem}-diagram-{counter}.png"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "diagram.mmd"
            source.write_text(match.group(1).rstrip() + "\n", encoding="utf-8")
            result = subprocess.run(
                [mmdc, "-i", str(source), "-o", str(png), "-b", "white", "-q"],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0 or not png.is_file():
            sys.exit(f"mmdc failed on diagram {counter} (check its mermaid syntax):\n{result.stderr}")
        written.append(png)
        alt = f"diagram {counter}"
        if mode == "inline":
            payload = base64.b64encode(png.read_bytes()).decode("ascii")
            return f"![{alt}](data:image/png;base64,{payload})"
        if mode == "placeholders":
            return f"> **Diagram {counter}.** Drag `{png.name}` in here, then delete this line."
        return f"![{alt}]({png.name})"

    return MERMAID_FENCE.sub(replace, text), written


def split_title(text: str, fallback: str) -> tuple[str, str]:
    """Lift a leading H1 out of the body and return it as the page title."""
    match = LEADING_H1.match(text)
    if not match:
        return fallback, text
    return match.group("title").strip(), text[match.end():].lstrip("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="Markdown file to prepare")
    parser.add_argument("--out", type=Path, default=None, help="Output markdown path")
    parser.add_argument(
        "--images",
        choices=("inline", "placeholders", "files"),
        default="inline",
        help="How rendered diagrams enter the body (default: inline data URIs)",
    )
    parser.add_argument(
        "--keep-title",
        action="store_true",
        help="Leave the leading H1 in the body instead of lifting it out as the title",
    )
    args = parser.parse_args(argv)

    if not args.source.is_file():
        sys.exit(f"Not a file: {args.source}")

    text = args.source.read_text(encoding="utf-8")
    out = args.out or args.source.with_suffix(".confluence.md")
    out.parent.mkdir(parents=True, exist_ok=True)

    body, pngs = render_diagrams(text, out.parent, args.source.stem, mode=args.images)

    title = args.source.stem
    if not args.keep_title:
        title, body = split_title(body, fallback=title)

    out.write_text(body, encoding="utf-8", newline="\n")
    size = len(body.encode("utf-8"))

    print(f"Title:    {title}")
    print(f"Body:     {out}  ({size:,} bytes)")
    print(f"Diagrams: {len(pngs)} rendered ({args.images})")
    for png in pngs:
        print(f"          {png.name}  ({png.stat().st_size:,} bytes)")

    if args.images == "inline" and size > INLINE_BUDGET_BYTES:
        print()
        print(f"WARNING: body is {size:,} bytes, over the {INLINE_BUDGET_BYTES:,} inline budget.")
        print("Every byte travels through the MCP tool call. Rerun with --images placeholders")
        print("and drag the rendered PNGs in afterwards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
