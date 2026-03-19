#!/usr/bin/env python3
"""
Convert a Markdown file to a PDF that resembles the VS Code Markdown Preview
(light theme). Uses python-markdown for parsing and Chrome headless for rendering.

Usage:
    python3 tools/md_to_pdf.py RESTRUCTURING_PLAN.md RESTRUCTURING_PLAN.pdf
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

import markdown

# ---------------------------------------------------------------------------
# VS Code Markdown Preview — Light Theme CSS
# Based on the vscode-markdown-preview-default stylesheet
# ---------------------------------------------------------------------------
VSCODE_CSS = """
*, *::before, *::after {
    box-sizing: border-box;
}

html {
    font-size: 14px;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe WPC", "Segoe UI",
                 system-ui, "Ubuntu", "Droid Sans", sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #3b3b3b;
    background-color: #ffffff;
    max-width: 900px;
    margin: 0 auto;
    padding: 0 28px 60px;
    word-wrap: break-word;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
    color: #111111;
}

h1 {
    font-size: 2em;
    padding-bottom: .3em;
    border-bottom: 1px solid #d0d0d0;
    page-break-after: avoid;
}

h2 {
    font-size: 1.5em;
    padding-bottom: .3em;
    border-bottom: 1px solid #d0d0d0;
    page-break-after: avoid;
}

h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: 0.875em; }
h6 { font-size: 0.85em; color: #757575; }

/* ── Links ── */
a {
    color: #4080D0;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}

/* ── Paragraphs & spacing ── */
p {
    margin: 0 0 16px;
}

/* ── Horizontal rule ── */
hr {
    border: none;
    border-top: 1px solid #d0d0d0;
    margin: 24px 0;
}

/* ── Blockquote ── */
blockquote {
    margin: 0 0 16px;
    padding: 4px 16px;
    border-left: 4px solid rgba(0, 122, 204, 0.5);
    background-color: rgba(0, 122, 204, 0.05);
    border-radius: 0 3px 3px 0;
    color: #555;
}

blockquote p {
    margin: 8px 0;
}

/* ── Lists ── */
ul, ol {
    padding-left: 2em;
    margin: 0 0 16px;
}

li {
    margin: 4px 0;
}

li > p {
    margin: 8px 0;
}

/* ── Inline code ── */
code {
    font-family: "SF Mono", Menlo, Monaco, Consolas, "Courier New", monospace;
    font-size: 0.9em;
    background-color: rgba(175, 184, 193, 0.2);
    border-radius: 3px;
    padding: 0.2em 0.4em;
    color: #c7254e;
}

/* ── Code blocks ── */
pre {
    background-color: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 16px;
    overflow: auto;
    margin: 0 0 16px;
    line-height: 1.45;
    page-break-inside: avoid;
}

pre code {
    background-color: transparent;
    border-radius: 0;
    padding: 0;
    color: #24292e;
    white-space: pre;
    font-size: 0.9em;
}

/* ── Tables ── */
table {
    border-collapse: collapse;
    margin: 0 0 16px;
    width: auto;
    overflow: auto;
    page-break-inside: avoid;
}

th {
    font-weight: 600;
    background-color: #f6f8fa;
}

th, td {
    padding: 6px 13px;
    border: 1px solid #d0d7de;
    text-align: left;
    vertical-align: top;
}

tr:nth-child(even) {
    background-color: #f6f8fa;
}

/* ── Images ── */
img {
    max-width: 100%;
    border: 1px solid #e1e4e8;
    border-radius: 3px;
}

/* ── Print / PDF page settings ── */
@page {
    size: A4;
    margin: 20mm 18mm 20mm 18mm;
}

@media print {
    body {
        max-width: 100%;
        padding: 0;
        color: #111;
        font-size: 12px;
    }
    a {
        color: #111 !important;
        text-decoration: none !important;
    }
    pre, table {
        page-break-inside: avoid;
    }
    h1, h2, h3, h4 {
        page-break-after: avoid;
    }
    /* Suppress blank page at start sometimes added by Chrome */
    html, body { height: auto; }
}
"""

# ---------------------------------------------------------------------------
# HTML shell template
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def convert(md_path: Path, pdf_path: Path) -> None:
    source = md_path.read_text(encoding="utf-8")

    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "sane_lists",
        ],
        extension_configs={
            "toc": {"permalink": False},
        },
    )
    body_html = md.convert(source)

    title = md_path.stem.replace("_", " ").replace("-", " ").title()

    html = HTML_TEMPLATE.format(
        title=title,
        css=VSCODE_CSS,
        body=body_html,
    )

    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as fh:
        fh.write(html)
        tmp_html = fh.name

    try:
        cmd = [
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--run-all-compositor-stages-before-draw",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={pdf_path.resolve()}",
            f"file://{tmp_html}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Chrome stderr:", result.stderr, file=sys.stderr)
            raise RuntimeError(f"Chrome exited with code {result.returncode}")
    finally:
        os.unlink(tmp_html)

    print(f"PDF written → {pdf_path}")


def main() -> None:
    args = sys.argv[1:]
    if len(args) != 2:
        print(f"Usage: {sys.argv[0]} <input.md> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    md_path = Path(args[0]).resolve()
    pdf_path = Path(args[1]).resolve()

    if not md_path.exists():
        print(f"Error: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    convert(md_path, pdf_path)


if __name__ == "__main__":
    main()
