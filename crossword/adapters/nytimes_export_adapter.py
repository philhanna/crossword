# crossword.adapters.nytimes_export_adapter
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from crossword import Puzzle, PuzzleToSVG
from crossword.ports.export_port import ExportError


class NYTimesExportAdapter:
    """
    Exports a puzzle to NYTimes submission format.

    Produces a ZIP archive containing:
      - puzzle.html  (clue sheet)
      - puzzle.svg   (grid image)
    """

    def export_puzzle_to_nytimes(self, puzzle: Puzzle) -> bytes:
        try:
            svg_str = PuzzleToSVG(puzzle).generate_xml()
            html_str = self._build_nytimes_html(puzzle, svg_str)

            buf = BytesIO()
            with ZipFile(buf, mode="w", compression=ZIP_DEFLATED) as zf:
                zf.writestr("puzzle.html", html_str)
                zf.writestr("puzzle.svg", svg_str)
            return buf.getvalue()
        except Exception as e:
            raise ExportError(f"NYTimes export failed: {e}") from e

    def _build_nytimes_html(self, puzzle: Puzzle, svg_str: str) -> str:
        svg_obj = PuzzleToSVG(puzzle)
        gridsize = svg_obj.gridsize

        elem_root = ET.Element("html")
        elem_head = ET.SubElement(elem_root, "head")
        ET.SubElement(elem_head, "style").text = (
            "td { vertical-align: top; }\n"
            "h1 { text-align: center; }\n"
            "tr.ds { height: 8mm; }\n"
        )

        elem_body = ET.SubElement(elem_root, "body")

        if puzzle.title:
            ET.SubElement(elem_body, "h1").text = puzzle.title

        # SVG grid image (inline reference)
        elem_img = ET.SubElement(elem_body, "img")
        elem_img.set("src", "puzzle.svg")
        elem_img.set("width", str(gridsize))
        elem_img.set("height", str(gridsize))

        def _clue_table(parent, heading, words_dict):
            elem_div = ET.SubElement(parent, "div")
            elem_div.set("style", "page-break-before: always;")
            elem_table = ET.SubElement(elem_div, "table")
            elem_table.set("width", "95%")
            elem_tr = ET.SubElement(elem_table, "tr")
            elem_tr.set("class", "ds")
            elem_th = ET.SubElement(elem_tr, "th")
            elem_th.set("width", "80%")
            elem_th.set("align", "left")
            elem_th.text = heading
            ET.SubElement(elem_tr, "th").set("width", "20%")
            for seq in sorted(words_dict):
                word = words_dict[seq]
                text = re.sub(" ", ".", word.get_text() or "")
                clue = word.get_clue() or ""
                elem_tr = ET.SubElement(elem_table, "tr")
                elem_tr.set("class", "ds")
                ET.SubElement(elem_tr, "td").text = f"{seq} {clue}"
                elem_td = ET.SubElement(elem_tr, "td")
                elem_td.set("style", "font-family: monospace")
                elem_td.text = text

        _clue_table(elem_body, "ACROSS", puzzle.across_words)
        _clue_table(elem_body, "DOWN", puzzle.down_words)

        htmlstr = ET.tostring(element=elem_root, encoding="utf-8").decode()
        return re.sub("><", ">\n<", htmlstr)
