import re
from grid import Grid
from puzzle import Puzzle
import xml.etree.ElementTree as ET


class ToSVG:
    """ Abstract base class for grid and puzzle to svg """

    BOXSIZE = 32

    def __init__(self, n, *args, **kwargs):
        self.n = n
        self.id = f"svg{n}x{n}"
        self.boxsize = ToSVG.BOXSIZE
        self.gridsize = self.boxsize * self.n

        # Figure out where the cell number goes
        self.cell_number_x = 2
        self.cell_number_y = 10
        self.cell_number_fontsize = "8pt"

        # Figure out where the cell letter goes
        self.cell_letter_x = int(ToSVG.BOXSIZE / 3.0)
        self.cell_letter_y = int(ToSVG.BOXSIZE * 7.0 / 8.0)
        self.cell_letter_fontsize = str(int(ToSVG.BOXSIZE / 2)) + "pt"

        self.root = ET.Element("svg")
        self.root.set("id", self.id)
        self.black_cells = None
        self.numbered_cells = None
        pass

    def generate_xml(self):
        self.generate_root()
        self.generate_enclosing_square()
        self.generate_vertical_lines()
        self.generate_horizontal_lines()
        self.generate_cells()
        self.generate_word_numbers()
        xmlstr = ET.tostring(element=self.root, encoding="utf-8", method="xml").decode()
        xmlstr = re.sub('><', '>\n<', xmlstr)
        return xmlstr

    def generate_root(self):
        """ Fills in the attributes of the SVG root element """
        self.root.set("width", str(self.gridsize))
        self.root.set("height", str(self.gridsize))
        self.root.set("viewbox", f'0 0 {self.gridsize} {self.gridsize}')
        self.root.set("xmlns", 'http://www.w3.org/2000/svg')
        self.root.set("xmlns:xlink", 'http://www.w3.org/1999/xlink')

    def generate_enclosing_square(self):
        """ Adds the outermost border rectangle """
        elem_rect = ET.SubElement(self.root, "rect")
        elem_rect.set("width", f"{self.gridsize}")
        elem_rect.set("height", f"{self.gridsize}")
        elem_rect.set("fill", "white")
        elem_rect.set("stroke", "black")
        elem_rect.set("stroke-width", "2")

    def generate_vertical_lines(self):
        """ Generates the vertical lines of the grid """
        for x in range(self.n):
            elem_line = ET.SubElement(self.root, "line")
            elem_line.set("x1", f'{x * self.boxsize}')
            elem_line.set("x2", f'{x * self.boxsize}')
            elem_line.set("y1", "0")
            elem_line.set("y1", f'{self.gridsize}')
            elem_line.set("stroke", "black")

    def generate_horizontal_lines(self):
        """ Generates the horizontal lines of the grid """
        for y in range(self.n):
            elem_line = ET.SubElement(self.root, "line")
            elem_line.set("x1", "0")
            elem_line.set("x2", f'{self.gridsize}')
            elem_line.set("y1", f'{y * self.boxsize}')
            elem_line.set("y2", f'{y * self.boxsize}')
            elem_line.set("stroke", "black")

    def generate_cell(self, r, c):
        """ Fills in the letter text at (r, c) """
        pass

    def get_x_y_base(self, r, c):
        """ Returns the starting x and y bases for (r, c) """
        xbase = (c - 1) * self.boxsize
        ybase = (r - 1) * self.boxsize
        return xbase, ybase

    def generate_cells(self):
        """ Fills in the grid, including the black cells """
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                xbase, ybase = self.get_x_y_base(r, c)
                if (r, c) in self.black_cells:
                    elem_rect = ET.SubElement(self.root, "rect")
                    elem_rect.set("x", str(xbase))
                    elem_rect.set("y", str(ybase))
                    elem_rect.set("width", str(self.boxsize))
                    elem_rect.set("height", str(self.boxsize))
                    elem_rect.set("fill", "black")
                else:
                    self.generate_cell(r, c)

    def generate_word_numbers(self):
        """ Fills in the word numbers """
        for numbered_cell in self.numbered_cells:
            r = numbered_cell.r
            c = numbered_cell.c
            seq = numbered_cell.seq
            xbase, ybase = self.get_x_y_base(r, c)
            elem_text = ET.SubElement(self.root, "text")
            elem_text.set("x", str(xbase + self.cell_number_x))
            elem_text.set("y", str(ybase + self.cell_number_y))
            elem_text.set("font-size", str(self.cell_number_fontsize))
            elem_text.text = str(seq)


class GridToSVG(ToSVG):
    """ Generates SVG with an image of the puzzle """

    def __init__(self, grid: Grid, *args, **kwargs):
        super().__init__(grid.n, *args, **kwargs)
        self.grid = grid
        self.black_cells = grid.get_black_cells()
        self.numbered_cells = grid.get_numbered_cells()


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
