# crossword.adapters.export_adapter
import re
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

from crossword import Grid, Puzzle, PuzzleToSVG, Word
from crossword.ports.export import ExportError, ExportPort


class ExportAdapter(ExportPort):
    """
    Concrete implementation of ExportPort.

    Supports:
      - export_puzzle_to_acrosslite  → ZIP (txt + json)
      - export_puzzle_to_xml         → Crossword Compiler XML string
      - export_puzzle_to_nytimes     → ZIP (html + svg)

    Grid PDF/PNG export is not implemented (stubs raise ExportError).
    """

    # ------------------------------------------------------------------
    # Grid exports (stubs)
    # ------------------------------------------------------------------

    def export_grid_to_pdf(self, grid: Grid) -> bytes:
        raise ExportError("Grid PDF export is not implemented")

    def export_grid_to_png(self, grid: Grid) -> bytes:
        raise ExportError("Grid PNG export is not implemented")

    # ------------------------------------------------------------------
    # Puzzle → AcrossLite (.txt + .json → ZIP)
    # ------------------------------------------------------------------

    def export_puzzle_to_acrosslite(self, puzzle: Puzzle) -> bytes:
        """
        Return a ZIP archive containing:
          - puzzle.txt  (AcrossLite text format)
          - puzzle.json (full JSON backup)
        """
        try:
            txt = self._build_acrosslite_txt(puzzle)
            json_str = puzzle.to_json()

            buf = BytesIO()
            with ZipFile(buf, mode="w", compression=ZIP_DEFLATED) as zf:
                zf.writestr("puzzle.txt", txt)
                zf.writestr("puzzle.json", json_str)
            return buf.getvalue()
        except Exception as e:
            raise ExportError(f"AcrossLite export failed: {e}") from e

    def _build_acrosslite_txt(self, puzzle: Puzzle) -> str:
        n = puzzle.n
        indent = "     "

        with StringIO() as fp:
            fp.write("<ACROSS PUZZLE>\n")

            fp.write("<TITLE>\n")
            fp.write(indent + (puzzle.title or "") + "\n")

            fp.write("<AUTHOR>\n")
            fp.write(indent + "\n")

            fp.write("<COPYRIGHT>\n")
            fp.write(indent + "\n")

            fp.write("<SIZE>\n")
            fp.write(indent + f"{n}x{n}\n")

            fp.write("<GRID>\n")
            for r in range(1, n + 1):
                row = ""
                for c in range(1, n + 1):
                    if puzzle.is_black_cell(r, c):
                        row += "."
                    else:
                        letter = puzzle.get_cell(r, c)
                        row += letter if letter and letter.strip() else "X"
                fp.write(indent + row + "\n")

            fp.write("<ACROSS>\n")
            for seq in sorted(puzzle.across_words):
                clue = puzzle.across_words[seq].get_clue() or ""
                fp.write(indent + clue + "\n")

            fp.write("<DOWN>\n")
            for seq in sorted(puzzle.down_words):
                clue = puzzle.down_words[seq].get_clue() or ""
                fp.write(indent + clue + "\n")

            fp.write("<NOTEPAD>\n")
            fp.write("Created with Crossword Puzzle Editor, by Phil Hanna\n")
            fp.write("See https://github.com/philhanna/crossword\n")

            return fp.getvalue()

    # ------------------------------------------------------------------
    # Puzzle → Crossword Compiler XML (string)
    # ------------------------------------------------------------------

    def export_puzzle_to_xml(self, puzzle: Puzzle) -> str:
        """
        Return Crossword Compiler XML as a string.
        """
        try:
            return self._build_xml(puzzle)
        except Exception as e:
            raise ExportError(f"XML export failed: {e}") from e

    def _build_xml(self, puzzle: Puzzle) -> str:
        elem_root = ET.Element("crossword-compiler")
        elem_root.set("xmlns", "http://crossword.info/xml/crossword-compiler")

        elem_rect = ET.SubElement(elem_root, "rectangular-puzzle")
        elem_rect.set("xmlns", "http://crossword.info/xml/rectangular-puzzle")
        elem_rect.set("alphabet", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        # <metadata>
        elem_meta = ET.SubElement(elem_rect, "metadata")
        ET.SubElement(elem_meta, "title").text = puzzle.title or ""
        ET.SubElement(elem_meta, "creator").text = ""
        ET.SubElement(elem_meta, "copyright").text = ""
        ET.SubElement(elem_meta, "description").text = (
            "Created with Crossword Puzzle Editor, by Phil Hanna\n"
            "See https://github.com/philhanna/crossword"
        )

        # <crossword>
        elem_xw = ET.SubElement(elem_rect, "crossword")

        # <grid>
        n = puzzle.n
        elem_grid = ET.SubElement(elem_xw, "grid")
        elem_grid.set("width", str(n))
        elem_grid.set("height", str(n))

        elem_look = ET.SubElement(elem_grid, "grid-look")
        elem_look.set("numbering-scheme", "normal")
        elem_look.set("cell-size-in-pixels", "26")
        elem_look.set("clue-square-divider-width", "0.7")

        for c in range(1, n + 1):
            for r in range(1, n + 1):
                elem_cell = ET.SubElement(elem_grid, "cell")
                elem_cell.set("x", str(c))
                elem_cell.set("y", str(r))
                if puzzle.is_black_cell(r, c):
                    elem_cell.set("type", "block")
                else:
                    letter = puzzle.get_cell(r, c) or " "
                    elem_cell.set("solution", letter)
                    nc = puzzle.get_numbered_cell(r, c)
                    if nc:
                        elem_cell.set("number", str(nc.seq))

        # <word> elements
        wordid = 0
        for nc in filter(lambda nc: nc.a > 0, puzzle.numbered_cells):
            wordid += 1
            elem_word = ET.SubElement(elem_xw, "word")
            elem_word.set("id", str(wordid))
            elem_word.set("x", f"{nc.c}-{nc.c + nc.a - 1}")
            elem_word.set("y", str(nc.r))
        for nc in filter(lambda nc: nc.d > 0, puzzle.numbered_cells):
            wordid += 1
            elem_word = ET.SubElement(elem_xw, "word")
            elem_word.set("id", str(wordid))
            elem_word.set("x", str(nc.c))
            elem_word.set("y", f"{nc.r}-{nc.r + nc.d - 1}")

        # <clues> — Across
        wordid = 0
        elem_clues = ET.SubElement(elem_xw, "clues")
        elem_clues.set("ordering", "normal")
        ET.SubElement(ET.SubElement(elem_clues, "title"), "b").text = "Across"
        for nc in filter(lambda nc: nc.a > 0, puzzle.numbered_cells):
            wordid += 1
            elem_clue = ET.SubElement(elem_clues, "clue")
            elem_clue.set("word", str(wordid))
            elem_clue.set("number", str(nc.seq))
            elem_clue.text = puzzle.get_clue(nc.seq, Word.ACROSS) or ""

        # <clues> — Down
        elem_clues = ET.SubElement(elem_xw, "clues")
        elem_clues.set("ordering", "normal")
        ET.SubElement(ET.SubElement(elem_clues, "title"), "b").text = "Down"
        for nc in filter(lambda nc: nc.d > 0, puzzle.numbered_cells):
            wordid += 1
            elem_clue = ET.SubElement(elem_clues, "clue")
            elem_clue.set("word", str(wordid))
            elem_clue.set("number", str(nc.seq))
            elem_clue.text = puzzle.get_clue(nc.seq, Word.DOWN) or ""

        xmlstr = ET.tostring(element=elem_root, encoding="utf-8", method="xml").decode()
        xmlstr = re.sub("><", ">\n<", xmlstr)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xmlstr

    # ------------------------------------------------------------------
    # Puzzle → NYTimes submission (html + svg → ZIP)
    # ------------------------------------------------------------------

    def export_puzzle_to_nytimes(self, puzzle: Puzzle) -> bytes:
        """
        Return a ZIP archive containing:
          - puzzle.html  (clue sheet)
          - puzzle.svg   (grid image)
        """
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
