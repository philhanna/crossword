# crossword.adapters.solver_pdf_export_adapter
import os
import re
import subprocess
import tempfile

from crossword import Puzzle, GridToSVG
from crossword.ports.export_port import ExportError

_GRID_WIDTH = "4in"
_GRID_HEIGHT = "4in"


class SolverPdfExportAdapter:
    """
    Exports a puzzle to a compact solver PDF.

    Layout (Letter, 0.4in margins): title at top, grid floated right at 4in,
    ACROSS/DOWN clues fill the narrow column beside it then continue at full
    width below the grid before resorting to additional pages.
    """

    def export_puzzle_to_solver_pdf(self, puzzle: Puzzle) -> bytes:
        try:
            html = self._build_html(puzzle)
            return self._html_to_pdf(html)
        except ExportError:
            raise
        except Exception as e:
            raise ExportError(f"Solver PDF export failed: {e}") from e

    # ------------------------------------------------------------------
    # HTML builder
    # ------------------------------------------------------------------

    def _build_html(self, puzzle: Puzzle) -> str:
        svg_str = self._prepare_svg(GridToSVG(puzzle.grid).generate_xml())
        title = puzzle.title or ""
        across_html = self._clue_list(puzzle.across_words)
        down_html = self._clue_list(puzzle.down_words)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{ size: Letter; margin: 0.4in; }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9pt;
    margin: 0;
  }}
  h1 {{
    text-align: center;
    font-size: 13pt;
    margin: 0 0 0.5em 0;
    font-weight: bold;
  }}
  .layout::after {{
    content: "";
    display: table;
    clear: both;
  }}
  svg.grid-svg {{
    float: right;
    display: block;
    width: {_GRID_WIDTH};
    height: {_GRID_HEIGHT};
    margin-left: 0.75em;
    margin-right: 4px;
    overflow: visible;
  }}
  .section-title {{
    font-size: 10pt;
    font-weight: bold;
    margin: 0.5em 0 4px 0;
  }}
  .clue {{
    line-height: 1.25;
    margin-bottom: 2px;
  }}
  .seq {{
    font-weight: bold;
  }}
</style>
</head>
<body>
{"<h1>" + title + "</h1>" if title else ""}
<div class="layout">
  {svg_str}
  <div class="section-title">ACROSS</div>
  {across_html}
  <div class="section-title">DOWN</div>
  {down_html}
</div>
</body>
</html>"""

    def _prepare_svg(self, svg_str: str) -> str:
        """Set SVG root width/height to CSS units and add float class."""
        svg_str = re.sub(r'width="\d+(?:\.\d+)?"', f'width="{_GRID_WIDTH}"', svg_str, count=1)
        svg_str = re.sub(r'height="\d+(?:\.\d+)?"', f'height="{_GRID_HEIGHT}"', svg_str, count=1)
        svg_str = svg_str.replace('<svg ', '<svg class="grid-svg" ', 1)
        return svg_str

    def _clue_list(self, words_dict: dict) -> str:
        lines = []
        for seq in sorted(words_dict):
            clue = words_dict[seq].get_clue() or ""
            lines.append(
                f'<div class="clue"><span class="seq">{seq}</span> {clue}</div>'
            )
        return "\n      ".join(lines)

    # ------------------------------------------------------------------
    # PDF generation via Chrome headless
    # ------------------------------------------------------------------

    def _html_to_pdf(self, html: str) -> bytes:
        html_fd, html_path = tempfile.mkstemp(suffix=".html")
        pdf_fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
        try:
            os.close(pdf_fd)
            with os.fdopen(html_fd, "w", encoding="utf-8") as f:
                f.write(html)

            result = subprocess.run(
                [
                    "google-chrome",
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--print-to-pdf-no-header",
                    f"--print-to-pdf={pdf_path}",
                    f"file://{html_path}",
                ],
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode(errors="replace")
                raise ExportError(f"Chrome PDF generation failed: {stderr}")

            with open(pdf_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(html_path):
                os.unlink(html_path)
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
