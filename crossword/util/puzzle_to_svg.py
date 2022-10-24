from crossword.puzzles import Puzzle
from crossword.util import ToSVG
import xml.etree.ElementTree as ET


class PuzzleToSVG(ToSVG):
    """ Generates SVG with an image of the puzzle """

    def __init__(self, puzzle: Puzzle, *args, **kwargs):
        super().__init__(puzzle.n, *args, **kwargs)
        self.puzzle = puzzle
        self.black_cells = puzzle.black_cells
        self.numbered_cells = puzzle.numbered_cells

    def generate_cell(self, r, c):
        letter = self.puzzle.get_cell(r, c)
        if letter and not letter == " ":
            xbase, ybase = self.get_x_y_base(r, c)
            elem_text = ET.SubElement(self.root, "text")
            elem_text.set("x", str(xbase + self.cell_letter_x))
            elem_text.set("y", str(ybase + self.cell_letter_y))
            elem_text.set("font-size", str(self.cell_letter_fontsize))
            elem_text.text = letter
