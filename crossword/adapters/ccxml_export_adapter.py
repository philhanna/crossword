# crossword.adapters.ccxml_export_adapter
import re
import xml.etree.ElementTree as ET

from crossword import Puzzle, Word
from crossword.ports.export_port import ExportError


class CcxmlExportAdapter:
    """
    Exports a puzzle to Crossword Compiler XML format.
    """

    def export_puzzle_to_xml(self, puzzle: Puzzle) -> str:
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
