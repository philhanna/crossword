# crossword.adapters.nytimes_export_adapter
import os
import re
import subprocess
import tempfile

from crossword import Puzzle, PuzzleToSVG
from crossword.ports.export_port import ExportError


class NYTimesExportAdapter:
    """
    Exports a puzzle to NYTimes submission format (PDF).

    Produces a PDF containing:
      - Page 1: filled-in answer grid with numbers and author contact info
      - Page 2+: clue sheet with ACROSS then DOWN (double-spaced, answers at far right)

    Author info (name, address, email) is optional; omit fields that are not set.
    """

    def __init__(self, author_name=None, author_address=None, author_email=None):
        self.author_name = author_name
        self.author_address = author_address
        self.author_email = author_email

    def export_puzzle_to_nytimes(self, puzzle: Puzzle) -> bytes:
        try:
            html = self._build_html(puzzle)
            return self._html_to_pdf(html)
        except ExportError:
            raise
        except Exception as e:
            raise ExportError(f"NYTimes export failed: {e}") from e

    # ------------------------------------------------------------------
    # HTML builder
    # ------------------------------------------------------------------

    def _build_html(self, puzzle: Puzzle) -> str:
        svg_str = PuzzleToSVG(puzzle).generate_xml()
        title = puzzle.title or ""

        author_lines = []
        if self.author_name:
            author_lines.append(f"<strong>Name:</strong> {self.author_name}")
        if self.author_address:
            author_lines.append(f"<strong>Address:</strong> {self.author_address}")
        if self.author_email:
            author_lines.append(f"<strong>Email:</strong> {self.author_email}")
        author_html = "<br>\n".join(author_lines)

        clue_rows = self._clue_rows(puzzle)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{ size: Letter; margin: 1in; }}
  body {{ font-family: "Times New Roman", Times, serif; font-size: 12pt; }}
  h1 {{ text-align: center; font-size: 18pt; margin: 0 0 0.75em 0; }}
  .grid-page {{ text-align: center; page-break-after: always; }}
  .author-info {{ margin-top: 1.5em; text-align: left; font-size: 11pt; line-height: 1.6; }}
  table {{ width: 100%; border-collapse: collapse; }}
  tr.ds {{ height: 8mm; }}
  td, th {{ vertical-align: top; padding: 1px 4px; }}
  .section-head {{ font-size: 14pt; font-weight: bold; padding-top: 1em; padding-bottom: 0.25em; }}
  .answer {{ font-family: "Courier New", Courier, monospace; text-align: right; }}
</style>
</head>
<body>

<div class="grid-page">
  {"<h1>" + title + "</h1>" if title else ""}
  {svg_str}
  {"<div class='author-info'>" + author_html + "</div>" if author_lines else ""}
</div>

<div class="clue-section">
  <table>
    <tr><td colspan="2" class="section-head">ACROSS</td></tr>
{clue_rows["across"]}
    <tr><td colspan="2" class="section-head">DOWN</td></tr>
{clue_rows["down"]}
  </table>
</div>

</body>
</html>"""

    def _clue_rows(self, puzzle: Puzzle) -> dict:
        def rows(words_dict):
            lines = []
            for seq in sorted(words_dict):
                word = words_dict[seq]
                clue = word.get_clue() or ""
                answer = re.sub(" ", ".", word.get_text() or "")
                lines.append(
                    f'    <tr class="ds">'
                    f'<td>{seq} {clue}</td>'
                    f'<td class="answer">{answer}</td>'
                    f'</tr>'
                )
            return "\n".join(lines)

        return {
            "across": rows(puzzle.across_words),
            "down": rows(puzzle.down_words),
        }

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
