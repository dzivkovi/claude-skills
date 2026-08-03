#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown>=3.6,<4", "reportlab>=4,<5", "pillow>=10"]
# ///
"""Print a Markdown document to a plain, internal-grade PDF with clickable links.

One unified renderer that keeps every hyperlink live (including timestamped
video deep-links like ...&t=123), renders GFM pipe tables as real tables,
renders ```mermaid fences locally via mermaid-cli (mmdc, no network), and
stamps a lightweight header/footer: "Page N of M" top-left, version + date
top-right, an author contact line centered in the footer.

Deliberately plain: no cover page, no table of contents, no brand tokens.
This is the internal-document look, not a marketing artifact.

Usage:

    uv run print_markdown.py briefing.md
    uv run print_markdown.py architecture.md \\
        --author "jane.doe@example.com" --docversion v1.0.3
    uv run print_markdown.py notes.md --accent "#0b5394"   # conservative blue links

Output defaults to <source stem>.pdf next to the source file. mermaid-cli is
required only when the document actually contains mermaid fences
(npm install -g @mermaid-js/mermaid-cli).

Provenance: consolidates two earlier private converters (a reportlab briefing
renderer and a headless-Chrome print script) after the Chrome path was measured
to emit zero /URI link annotations; see the repo issue for the decision record.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

DEFAULT_AUTHOR = "daniel@magmainc.ca"  # rebrand: pass --author or edit this line
DEFAULT_ACCENT = "#c96442"  # the one color that signals "clickable"

# Stamp geometry in PDF points, ported from the proven internal print script.
STAMP_MARGIN_X = 43
HEADER_BASELINE_FROM_TOP = 28
FOOTER_BASELINE = 20
STAMP_GRAY = 0.42

MARGIN_PT = 43.2  # 0.6 inch
FRONT_MATTER = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
FENCE = re.compile(r"^```([A-Za-z0-9_+-]*)[ \t]*\n(.*?)\n```[ \t]*$", re.DOTALL | re.MULTILINE)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
TOKEN = "MDPDFBLOCK{n}TOKEN"
TOKEN_RE = re.compile(r"\AMDPDFBLOCK\d+TOKEN\Z")

MONO_SIZE = 8.0
MONO_WRAP_COLS = 100
TABLE_FONT_SIZE = 9.0

# Bare-URL autolink, applied to already-escaped text runs (so & is &amp; here).
BARE_URL = re.compile(r'https?://[^\s<>"]+')


# ---------------------------------------------------------------- pre-passes


def strip_front_matter(text: str) -> str:
    return FRONT_MATTER.sub("", text, count=1)


def find_mmdc() -> str:
    mmdc = shutil.which("mmdc")
    if mmdc is None:
        sys.exit(
            "This document contains mermaid fences but mermaid-cli (mmdc) is not on PATH.\n"
            "Install it with: npm install -g @mermaid-js/mermaid-cli"
        )
    return mmdc


def render_mermaid_png(source_text: str, index: int, workdir: Path, mmdc: str) -> Path:
    """Render one mermaid fence to a scale-3 PNG (~360 DPI at body width)."""

    source = workdir / f"diagram-{index}.mmd"
    target = workdir / f"diagram-{index}.png"
    source.write_text(source_text + "\n", encoding="utf-8")
    result = subprocess.run(
        [mmdc, "-i", str(source), "-o", str(target), "-b", "white", "-s", "3", "-q"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not target.is_file():
        sys.exit(f"mmdc failed on diagram {index} (check its mermaid syntax):\n{result.stderr}")
    return target


def extract_fences(text: str, workdir: Path) -> tuple[str, dict[str, dict]]:
    """Replace every fenced block with a token; return (text, token -> block info).

    Extracting fences BEFORE any other processing protects their content from
    the HTML-comment strip and gives us deterministic code wrapping. Mermaid
    fences become diagram PNGs; everything else becomes a preformatted block.
    """

    blocks: dict[str, dict] = {}
    mmdc: str | None = None
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter, mmdc
        counter += 1
        token = TOKEN.format(n=counter)
        lang, body = match.group(1).lower(), match.group(2)
        if lang == "mermaid":
            if mmdc is None:
                mmdc = find_mmdc()
            blocks[token] = {"kind": "diagram", "path": render_mermaid_png(body, counter, workdir, mmdc)}
        else:
            blocks[token] = {"kind": "code", "text": body}
        return f"\n{token}\n"

    return FENCE.sub(replace, text), blocks


def wrap_code_lines(text: str, columns: int = MONO_WRAP_COLS) -> str:
    """Deterministic hard wrap so long code lines never overflow the frame."""

    wrapped: list[str] = []
    for line in text.split("\n"):
        while len(line) > columns:
            wrapped.append(line[:columns])
            line = line[columns:]
        wrapped.append(line)
    return "\n".join(wrapped)


# ------------------------------------------------------- HTML -> flowables


class FlowableBuilder(HTMLParser):
    """Walk python-markdown's HTML output and emit reportlab flowables.

    Supported: h1-h4, p, ul/ol/li (nested), table/thead/tbody/tr/th/td, hr,
    blockquote, inline strong/em/code/a. Fenced blocks arrive as tokens
    (handled in _flush_paragraph) because they were extracted pre-markdown.
    """

    def __init__(self, styles, blocks, accent: str, frame_width: float):
        super().__init__(convert_charrefs=True)
        from reportlab.platypus import Spacer

        self.styles = styles
        self.blocks = blocks
        self.accent = accent
        self.frame_width = frame_width
        self.story: list = []
        self._spacer = Spacer
        self._runs: list[str] = []
        self._block: str | None = None
        self._list_stack: list[dict] = []
        self._pending_li: list[tuple[int, str, str]] = []
        self._table: dict | None = None
        self._href: str | None = None
        self._in_quote = False
        self._in_code_span = False

    # -- inline runs

    def _autolink(self, escaped: str) -> str:
        """Wrap bare URLs in <a> anchors, parity with the briefing renderer."""

        def repl(match: re.Match[str]) -> str:
            url = match.group(0)
            trail = ""
            while url and url[-1] in ".,;:)]":
                trail = url[-1] + trail
                url = url[:-1]
            return f'<a href="{url}" color="{self.accent}">{url}</a>{trail}'

        return BARE_URL.sub(repl, escaped)

    def _append_text(self, data: str) -> None:
        if self._block or self._table is not None:
            text = escape(data)
            if self._href is None and not self._in_code_span:
                text = self._autolink(text)
            self._runs.append(text)

    def handle_data(self, data: str) -> None:
        if data.strip() or self._runs:
            self._append_text(data)

    def handle_starttag(self, tag: str, attrs) -> None:
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "p", "li"):
            self._open_block(tag)
        elif tag in ("strong", "b"):
            self._runs.append("<b>")
        elif tag in ("em", "i"):
            self._runs.append("<i>")
        elif tag == "code":
            self._in_code_span = True
            self._runs.append(f'<font face="Courier" size="{MONO_SIZE + 0.5}">')
        elif tag == "a":
            self._href = a.get("href", "")
            self._runs.append(f'<a href="{escape(self._href, {chr(34): "&quot;"})}" color="{self.accent}">')
        elif tag == "br":
            self._runs.append("<br/>")
        elif tag in ("ul", "ol"):
            # A parent <li>'s text is still pending when its nested list opens;
            # flush it now, before the stack deepens, so it keeps its own indent.
            if self._block == "li" and self._runs:
                self._flush_paragraph("li")
            self._list_stack.append({"tag": tag, "count": 0})
        elif tag == "blockquote":
            self._in_quote = True
        elif tag == "hr":
            self._emit_hr()
        elif tag == "table":
            self._table = {"rows": [], "header": False}
        elif tag == "thead":
            if self._table is not None:
                self._table["header"] = True
        elif tag == "tr":
            if self._table is not None:
                self._table["current"] = []
        elif tag in ("th", "td"):
            self._runs = []
        elif tag == "img":
            src = a.get("src", "")
            if src:
                self.story.append(self._image(Path(src)))

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h1", "h2", "h3", "h4", "p", "li"):
            self._flush_paragraph(tag)
        elif tag in ("strong", "b"):
            self._runs.append("</b>")
        elif tag in ("em", "i"):
            self._runs.append("</i>")
        elif tag == "code":
            self._in_code_span = False
            self._runs.append("</font>")
        elif tag == "a":
            self._runs.append("</a>")
            self._href = None
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
        elif tag == "blockquote":
            self._in_quote = False
        elif tag in ("th", "td"):
            if self._table is not None:
                self._table["current"].append("".join(self._runs).strip())
                self._runs = []
        elif tag == "tr":
            if self._table is not None and self._table.get("current") is not None:
                self._table["rows"].append(self._table.pop("current"))
        elif tag == "table":
            self._emit_table()

    # -- block emission

    def _open_block(self, tag: str) -> None:
        self._block = tag
        self._runs = []

    def _flush_paragraph(self, tag: str) -> None:
        from reportlab.platypus import Paragraph

        text = "".join(self._runs).strip()
        self._runs = []
        self._block = None
        if not text:
            return
        if TOKEN_RE.match(text):
            self._emit_token(text)
            return
        if tag == "li":
            depth = max(len(self._list_stack) - 1, 0)
            frame = self._list_stack[-1] if self._list_stack else {"tag": "ul", "count": 0}
            frame["count"] += 1
            bullet = f"{frame['count']}." if frame["tag"] == "ol" else "•"
            style = self.styles["bullet"].clone(f"li{depth}", leftIndent=14 + 16 * depth)
            self.story.append(Paragraph(f"{bullet} {text}", style))
            return
        style_name = {"h1": "h1", "h2": "h2", "h3": "h3", "h4": "h3", "p": "body"}[tag]
        if tag == "p" and self._in_quote:
            style_name = "quote"
        self.story.append(Paragraph(text, self.styles[style_name]))

    def _emit_token(self, token: str) -> None:
        from reportlab.platypus import Preformatted

        block = self.blocks.get(token)
        if block is None:
            return
        if block["kind"] == "diagram":
            self.story.append(self._image(block["path"]))
        else:
            self.story.append(Preformatted(wrap_code_lines(block["text"]), self.styles["mono"]))

    def _emit_hr(self) -> None:
        from reportlab.lib import colors
        from reportlab.platypus import HRFlowable

        self.story.append(self._spacer(1, 4))
        self.story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=0.6))
        self.story.append(self._spacer(1, 8))

    def _image(self, path: Path):
        from PIL import Image as PILImage
        from reportlab.platypus import Image

        with PILImage.open(path) as im:
            px_w, px_h = im.size
        natural_pt = (px_w / 3) * 0.75  # scale-3 PNG back to natural CSS size in points
        width = min(self.frame_width, natural_pt)
        height = width * px_h / px_w
        max_h = 640
        if height > max_h:
            width, height = width * max_h / height, max_h
        return Image(str(path), width=width, height=height)

    def _emit_table(self) -> None:
        from reportlab.lib import colors
        from reportlab.platypus import Paragraph, Table, TableStyle

        assert self._table is not None
        rows, has_header = self._table["rows"], self._table["header"]
        self._table = None
        if not rows:
            return
        ncols = max(len(r) for r in rows)
        rows = [r + [""] * (ncols - len(r)) for r in rows]

        # Column widths proportional to content length, floored so no column vanishes.
        weights = []
        for c in range(ncols):
            longest = max(len(re.sub(r"<[^>]+>", "", rows[r][c])) for r in range(len(rows)))
            weights.append(max(longest, 8))
        total = sum(weights)
        widths = [max(w / total, 0.12) for w in weights]
        norm = sum(widths)
        col_widths = [self.frame_width * w / norm for w in widths]

        cell, head = self.styles["cell"], self.styles["cellHead"]
        data = [
            [Paragraph(text, head if (has_header and r == 0) else cell) for text in row]
            for r, row in enumerate(rows)
        ]
        table = Table(data, colWidths=col_widths, repeatRows=1 if has_header else 0)
        style = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8c8c8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if has_header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")))
        table.setStyle(TableStyle(style))
        self.story.append(self._spacer(1, 4))
        self.story.append(table)
        self.story.append(self._spacer(1, 8))


def make_styles(accent: str):
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base = getSampleStyleSheet()
    body = ParagraphStyle("md_body", parent=base["BodyText"], fontSize=10.5, leading=15, spaceAfter=7)
    return {
        "body": body,
        "bullet": ParagraphStyle("md_bullet", parent=body, leftIndent=14, spaceAfter=5),
        "quote": ParagraphStyle(
            "md_quote", parent=body, leftIndent=18, textColor=colors.HexColor("#555555"), fontName="Helvetica-Oblique"
        ),
        "h1": ParagraphStyle(
            "md_h1", parent=base["Title"], fontSize=18, leading=22, spaceBefore=6, spaceAfter=12, keepWithNext=1
        ),
        "h2": ParagraphStyle(
            "md_h2",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor(accent),
            keepWithNext=1,
        ),
        "h3": ParagraphStyle(
            "md_h3", parent=base["Heading3"], fontSize=12, leading=16, spaceBefore=10, spaceAfter=5, keepWithNext=1
        ),
        "mono": ParagraphStyle(
            "md_mono",
            fontName="Courier",
            fontSize=MONO_SIZE,
            leading=MONO_SIZE + 2,
            backColor=colors.HexColor("#f6f6f6"),
            borderColor=colors.HexColor("#e0e0e0"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=6,
            spaceAfter=10,
        ),
        "cell": ParagraphStyle("md_cell", parent=body, fontSize=TABLE_FONT_SIZE, leading=TABLE_FONT_SIZE + 3, spaceAfter=0),
        "cellHead": ParagraphStyle(
            "md_cell_head",
            parent=body,
            fontSize=TABLE_FONT_SIZE,
            leading=TABLE_FONT_SIZE + 3,
            spaceAfter=0,
            fontName="Helvetica-Bold",
        ),
    }


# -------------------------------------------------------------- stamping


def make_numbered_canvas(footer_center: str, header_right: str, footer_left: str = ""):
    """Canvas that stamps Page N of M plus header/footer once totals are known."""

    from reportlab.pdfgen import canvas as rl_canvas

    class NumberedCanvas(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_states: list[dict] = []

        def showPage(self):
            self._saved_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_states)
            for state in self._saved_states:
                self.__dict__.update(state)
                self._stamp(total)
                super().showPage()
            super().save()

        def _stamp(self, total: int):
            width, height = self._pagesize
            self.setFont("Helvetica", 8)
            self.setFillGray(STAMP_GRAY)
            self.drawString(
                STAMP_MARGIN_X, height - HEADER_BASELINE_FROM_TOP, f"Page {self._pageNumber} of {total}"
            )
            if header_right:
                self.drawRightString(width - STAMP_MARGIN_X, height - HEADER_BASELINE_FROM_TOP, header_right)
            if footer_center:
                self.drawCentredString(width / 2, FOOTER_BASELINE, footer_center)
            # Source provenance, bottom-left: which file produced this print. A
            # printed page that outlives the session is otherwise unreorderable
            # and untraceable back to its markdown. Left-aligned so it can never
            # collide with the centered contact line on a long path.
            if footer_left:
                self.drawString(STAMP_MARGIN_X, FOOTER_BASELINE, footer_left)

    return NumberedCanvas


# ------------------------------------------------------------------ main


def source_label(md_path: Path, depth: int = 2) -> str:
    """Trailing `depth` path components of the source, for the footer stamp.

    Just the basename is often ambiguous across projects that reuse names like
    notes.md; two components ("operator-brain/2026-08-03-agent-memory.md") name
    it unambiguously without leaking a full home-directory path onto paper.
    """
    parts = md_path.resolve().parts
    return "/".join(parts[-depth:]) if len(parts) >= depth else md_path.name


def render(
    md_path: Path,
    out_path: Path,
    author: str,
    docversion: str,
    date_label: str,
    accent: str,
    footer_left: str = "",
) -> None:
    import markdown
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate

    frame_width = letter[0] - 2 * MARGIN_PT

    with tempfile.TemporaryDirectory() as tmp:
        text = strip_front_matter(md_path.read_text(encoding="utf-8"))
        text, blocks = extract_fences(text, Path(tmp))
        text = HTML_COMMENT.sub("", text)
        html = markdown.markdown(text, extensions=["tables"])

        builder = FlowableBuilder(make_styles(accent), blocks, accent, frame_width)
        builder.feed(html)

        # Build to a temp sibling, then replace. A viewer holding the target open,
        # or an antivirus scan of a cloud-synced copy, can briefly lock it on
        # Windows; writing directly would fail after all the rendering work.
        tmp_out = out_path.with_name(out_path.name + ".tmp")
        header_right = " - ".join(p for p in (docversion, date_label) if p)
        doc = SimpleDocTemplate(
            str(tmp_out),
            pagesize=letter,
            topMargin=MARGIN_PT + 14,
            bottomMargin=MARGIN_PT,
            leftMargin=MARGIN_PT,
            rightMargin=MARGIN_PT,
            title=md_path.stem,
            author=author or "markdown-to-pdf",
        )
        doc.build(builder.story, canvasmaker=make_numbered_canvas(author, header_right, footer_left))

    for delay in (0.0, 0.5, 1.0, 2.0):
        time.sleep(delay)
        try:
            os.replace(tmp_out, out_path)
            return
        except PermissionError:
            continue
    tmp_out.unlink(missing_ok=True)
    sys.exit(
        f"Cannot overwrite {out_path}: the file is locked, likely open in a PDF viewer.\n"
        "Close it and rerun."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="Markdown file to print")
    parser.add_argument("--out", type=Path, default=None, help="Output PDF path (default: <stem>.pdf beside source)")
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="Footer contact line; pass '' to suppress")
    parser.add_argument("--docversion", default="", help="Document version label for the header, e.g. v1.0.3")
    parser.add_argument("--date", default=date.today().isoformat(), help="Header date (default: today)")
    parser.add_argument("--accent", default=DEFAULT_ACCENT, help="Link and h2 color (default: %(default)s)")
    parser.add_argument(
        "--source-label",
        default=None,
        help="Bottom-left provenance stamp (default: last 2 path components of the source; pass '' to suppress)",
    )
    args = parser.parse_args(argv)

    if not args.source.is_file():
        sys.exit(f"Not a file: {args.source}")
    out = args.out or args.source.with_suffix(".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    footer_left = source_label(args.source) if args.source_label is None else args.source_label
    render(args.source, out, args.author, args.docversion, args.date, args.accent, footer_left)
    print(f"OK: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
