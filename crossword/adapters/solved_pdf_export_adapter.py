# crossword.adapters.solved_pdf_export_adapter
import os
import re
import subprocess
import tempfile
import html
import json
from pathlib import Path

from crossword import Puzzle, PuzzleToSVG
from crossword.adapters.nytimes_export_adapter import _find_chrome
from crossword.ports.export_port import ExportError

_PAGE_MARGIN = 0.4
_PAGE_WIDTH = 8.5 - (_PAGE_MARGIN * 2)
_PAGE_HEIGHT = 11 - (_PAGE_MARGIN * 2)
_TITLE_HEIGHT = 0.5
_COLUMN_GAP = 0.2
_COLUMN_WIDTH = (_PAGE_WIDTH - (_COLUMN_GAP * 2)) / 3
_GRID_SIZE = (_COLUMN_WIDTH * 2) + _COLUMN_GAP

_GRID_WIDTH = f"{_GRID_SIZE:.3f}in"
_GRID_HEIGHT = _GRID_WIDTH


class SolvedPdfExportAdapter:
    """
    Exports a puzzle to a solved PDF (filled-in grid + clues).

    Same layout as SolverPdfExportAdapter but uses PuzzleToSVG so that
    the answer letters appear in every white cell.
    """

    def export_puzzle_to_solved_pdf(self, puzzle: Puzzle) -> bytes:
        try:
            html = self._build_html(puzzle)
            return self._html_to_pdf(html)
        except ExportError:
            raise
        except Exception as e:
            raise ExportError(f"Solved PDF export failed: {e}") from e

    # ------------------------------------------------------------------
    # HTML builder
    # ------------------------------------------------------------------

    def _build_html(self, puzzle: Puzzle) -> str:
        svg_str = self._prepare_svg(PuzzleToSVG(puzzle).generate_xml())
        title = puzzle.title or ""
        clue_blocks_json = self._clue_blocks_json(puzzle)
        grid_bottom_pad = _GRID_SIZE / (puzzle.grid.n * 3)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  :root {{
    --page-width: {_PAGE_WIDTH:.3f}in;
    --page-height: {_PAGE_HEIGHT:.3f}in;
    --title-height: {_TITLE_HEIGHT:.3f}in;
    --column-gap: {_COLUMN_GAP:.3f}in;
    --column-width: {_COLUMN_WIDTH:.3f}in;
    --grid-size: {_GRID_SIZE:.3f}in;
    --grid-bottom-pad: {grid_bottom_pad:.3f}in;
    --body-height: calc(var(--page-height) - var(--title-height));
    --bottom-row-height: calc(var(--body-height) - var(--grid-size));
  }}
  @page {{ size: Letter; margin: {_PAGE_MARGIN:.3f}in; }}
  * {{
    box-sizing: border-box;
  }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9pt;
    margin: 0;
  }}
  .page {{
    width: var(--page-width);
    height: var(--page-height);
    page-break-after: always;
    overflow: hidden;
  }}
  .page:last-child {{
    page-break-after: auto;
  }}
  .page-title {{
    font-size: 13pt;
    height: var(--title-height);
    line-height: var(--title-height);
    margin: 0;
    text-align: center;
    font-weight: bold;
  }}
  .first-page-body {{
    display: grid;
    grid-template-columns: var(--column-width) var(--column-width) var(--column-width);
    grid-template-rows: var(--grid-size) var(--bottom-row-height);
    column-gap: var(--column-gap);
    row-gap: 0;
    height: var(--body-height);
  }}
  .first-page-left {{
    grid-column: 1;
    grid-row: 1 / span 2;
  }}
  .first-page-grid {{
    grid-column: 2 / span 2;
    grid-row: 1;
  }}
  .first-page-bottom {{
    grid-column: 2 / span 2;
    grid-row: 2;
    columns: 2;
    column-gap: var(--column-gap);
  }}
  .continuation-body {{
    columns: 3;
    column-gap: var(--column-gap);
    height: var(--body-height);
  }}
  .region {{
    overflow: hidden;
  }}
  .flow-region {{
    height: 100%;
  }}
  .flow-region .clue-block {{
    break-inside: avoid;
  }}
  .grid-wrapper {{
    width: var(--grid-size);
    height: var(--grid-size);
    padding-bottom: var(--grid-bottom-pad);
    margin-left: auto;
  }}
  svg.grid-svg {{
    display: block;
    width: 100%;
    height: 100%;
  }}
  .section-title {{
    font-size: 10pt;
    font-weight: bold;
    margin: 0 0 4px 0;
    break-after: avoid;
  }}
  .clue {{
    line-height: 1.25;
    margin-bottom: 3px;
  }}
  .seq {{
    font-weight: bold;
  }}
  #clue-source {{
    position: absolute;
    left: -9999px;
    top: 0;
    width: var(--column-width);
    visibility: hidden;
  }}
</style>
</head>
<body>
<div id="pages">
  <section class="page">
    {"<h1 class='page-title'>" + html.escape(title) + "</h1>" if title else "<div class='page-title'></div>"}
    <div class="first-page-body">
      <div id="first-page-left" class="region flow-region first-page-left"></div>
      <div class="first-page-grid">
        <div class="grid-wrapper">{svg_str}</div>
      </div>
      <div id="first-page-bottom" class="region flow-region first-page-bottom"></div>
    </div>
  </section>
</div>
<div id="clue-source"></div>
<script>
  const clueBlocks = {clue_blocks_json};

  function makeBlock(data) {{
    const wrapper = document.createElement("div");
    wrapper.className = "clue-block";
    if (data.kind === "section") {{
      const header = document.createElement("div");
      header.className = "section-title";
      header.textContent = data.text;
      wrapper.appendChild(header);
    }} else {{
      const clue = document.createElement("div");
      clue.className = "clue";

      const seq = document.createElement("span");
      seq.className = "seq";
      seq.textContent = data.seq;
      clue.appendChild(seq);
      clue.appendChild(document.createTextNode(" " + data.text));

      wrapper.appendChild(clue);
    }}
    return wrapper;
  }}

  function regionOverflows(region) {{
    if (getComputedStyle(region).columnCount !== "auto") {{
      return region.scrollWidth > region.clientWidth + 1;
    }}
    return region.scrollHeight > region.clientHeight + 1;
  }}

  function appendUntilFull(region, blocks, startIndex) {{
    let index = startIndex;
    while (index < blocks.length) {{
      const block = makeBlock(blocks[index]);
      region.appendChild(block);
      if (regionOverflows(region)) {{
        region.removeChild(block);
        break;
      }}
      index += 1;
    }}
    return index;
  }}

  function addContinuationPage() {{
    const pages = document.getElementById("pages");
    const page = document.createElement("section");
    page.className = "page";
    page.innerHTML = '<div class="page-title"></div><div class="continuation-body region flow-region"></div>';
    pages.appendChild(page);
    return page.querySelector(".continuation-body");
  }}

  function layoutClues() {{
    let nextIndex = 0;
    nextIndex = appendUntilFull(document.getElementById("first-page-left"), clueBlocks, nextIndex);
    nextIndex = appendUntilFull(document.getElementById("first-page-bottom"), clueBlocks, nextIndex);

    while (nextIndex < clueBlocks.length) {{
      const region = addContinuationPage();
      const pageEnd = appendUntilFull(region, clueBlocks, nextIndex);
      if (pageEnd === nextIndex) {{
        throw new Error("A clue block is too tall to fit in the available page region.");
      }}
      nextIndex = pageEnd;
    }}
  }}

  window.addEventListener("load", layoutClues);
</script>
</body>
</html>"""

    def _prepare_svg(self, svg_str: str) -> str:
        """Set SVG root width/height to CSS units, expand viewBox to include border stroke."""
        m = re.search(r'width="(\d+(?:\.\d+)?)"', svg_str)
        orig_w = int(float(m.group(1))) if m else 352
        m = re.search(r'height="(\d+(?:\.\d+)?)"', svg_str)
        orig_h = int(float(m.group(1))) if m else 352
        svg_str = re.sub(r'width="\d+(?:\.\d+)?"', f'width="{_GRID_WIDTH}"', svg_str, count=1)
        svg_str = re.sub(r'height="\d+(?:\.\d+)?"', f'height="{_GRID_HEIGHT}"', svg_str, count=1)
        svg_str = re.sub(
            r'viewBox="[^"]*"',
            f'viewBox="0 0 {orig_w + 1} {orig_h}"',
            svg_str, count=1, flags=re.IGNORECASE,
        )
        svg_str = svg_str.replace('<svg ', '<svg class="grid-svg" ', 1)
        return svg_str

    def _clue_blocks_json(self, puzzle: Puzzle) -> str:
        blocks = [{"kind": "section", "text": "ACROSS"}]
        blocks.extend(self._clue_blocks_for_words(puzzle.across_words))
        blocks.append({"kind": "section", "text": "DOWN"})
        blocks.extend(self._clue_blocks_for_words(puzzle.down_words))
        return json.dumps(blocks)

    def _clue_blocks_for_words(self, words_dict: dict) -> list[dict[str, str]]:
        blocks = []
        for seq in sorted(words_dict):
            clue = words_dict[seq].get_clue() or ""
            blocks.append(
                {
                    "kind": "clue",
                    "seq": str(seq),
                    "text": clue,
                }
            )
        return blocks

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

            html_url = Path(html_path).as_uri()

            result = subprocess.run(
                [
                    _find_chrome(),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--print-to-pdf-no-header",
                    f"--print-to-pdf={pdf_path}",
                    html_url,
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
