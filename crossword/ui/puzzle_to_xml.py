import re
import xml.etree.ElementTree as ET

from crossword import Word


class PuzzleToXML:
    """ Creates an XML string from a puzzle.

    :param user a DBUser object (or a mock, for testing)
    :param puzzle the puzzle being published

    The XML is in the format used by Crossword Compiler
    """
    CELL_SIZE_IN_PIXELS = 26
    CLUE_SQUARE_DIVIDER_WIDTH = 0.7

    def __init__(self, user, puzzle):
        self.user = user
        self.puzzle = puzzle
        self.xmlstr = self.create_xml()

    def create_xml(self):
        """ Generates the XML from the puzzle """
        elem_root = self.create_root()
        xmlstr = ET.tostring(element=elem_root, encoding="utf-8", method="xml").decode()
        xmlstr = re.sub('><', '>\n<', xmlstr)
        xmlstr = """<?xml version="1.0" encoding="UTF-8"?>\n""" + xmlstr
        return xmlstr

    def create_root(self):
        """ Creates the root element <crossword-compiler> """
        elem_root = ET.Element("crossword-compiler")
        elem_root.set("xmlns", "http://crossword.info/xml/crossword-compiler")
        self.create_elem_rectangular_puzzle(elem_root)
        return elem_root

    def create_elem_rectangular_puzzle(self, elem_root):
        """ Adds the <rectangular-puzzle> element """
        elem_rect = ET.SubElement(elem_root, "rectangular-puzzle")
        elem_rect.set("xmlns", "http://crossword.info/xml/rectangular-puzzle")
        elem_rect.set("alphabet", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.create_elem_metadata(elem_rect)
        self.create_elem_crossword(elem_rect)
        pass

    def create_elem_metadata(self, elem_rect):
        """ Adds <metadata> """
        elem_metadata = ET.SubElement(elem_rect, "metadata")
        elem_title = ET.SubElement(elem_metadata, "title")
        elem_title.text = self.puzzle.get_title()
        elem_creator = ET.SubElement(elem_metadata, "creator")
        elem_creator.text = self.get_creator()
        elem_copyright = ET.SubElement(elem_metadata, "copyright")
        elem_description = ET.SubElement(elem_metadata, "description")
        elem_description.text = (
            f"Created with Crossword Puzzle Editor, by Phil Hanna\n"
            f"See https://github.com/philhanna/crossword"
        )
        pass

    def get_creator(self):
        """ Returns the creator string based on the database record """
        username = self.user.username
        email = self.user.email
        creator = f"Created by {username} ({email})"
        return creator

    def create_elem_crossword(self, elem_rect):
        """ Creates the <crossword> element """
        elem_crossword = ET.SubElement(elem_rect, "crossword")
        self.create_elem_grid(elem_crossword)
        self.create_elem_words(elem_crossword)
        self.create_elem_clues(elem_crossword)
        pass

    def create_elem_words(self, elem_crossword):
        """ Creates all the <word> elements"""
        puzzle = self.puzzle
        wordid = 0
        # Across words
        for nc in filter(lambda nc: nc.a > 0, puzzle.numbered_cells):
            wordid += 1
            elem_word = ET.SubElement(elem_crossword, "word")
            elem_word.set("id", str(wordid))
            elem_word.set("x", f"{nc.c}-{nc.c + nc.a - 1}")
            elem_word.set("y", str(nc.r))
        # Down words
        for nc in filter(lambda nc: nc.d > 0, puzzle.numbered_cells):
            wordid += 1
            elem_word = ET.SubElement(elem_crossword, "word")
            elem_word.set("id", str(wordid))
            elem_word.set("x", str(nc.c))
            elem_word.set("y", f"{nc.r}-{nc.r + nc.d - 1}")

    def create_elem_clues(self, elem_crossword):
        """ Creates the <clues> element"""
        elem_clues = ET.SubElement(elem_crossword, "clues")
        elem_clues.set("ordering", "normal")
        puzzle = self.puzzle
        wordid = 0

        # Across clues
        elem_title = ET.SubElement(elem_clues, "title")
        elem_b = ET.SubElement(elem_title, "b")
        elem_b.text = "Across"
        for nc in filter(lambda nc: nc.a > 0, puzzle.numbered_cells):
            wordid += 1
            elem_clue = ET.SubElement(elem_clues, "clue")
            elem_clue.set("word", str(wordid))
            elem_clue.set("number", str(nc.seq))
            elem_clue.text = puzzle.get_clue(nc.seq, Word.ACROSS)
        pass

        elem_clues = ET.SubElement(elem_crossword, "clues")
        elem_clues.set("ordering", "normal")

        # Down clues
        elem_title = ET.SubElement(elem_clues, "title")
        elem_b = ET.SubElement(elem_title, "b")
        elem_b.text = "Down"
        for nc in filter(lambda nc: nc.d > 0, puzzle.numbered_cells):
            wordid += 1
            elem_clue = ET.SubElement(elem_clues, "clue")
            elem_clue.set("word", str(wordid))
            elem_clue.set("number", str(nc.seq))
            elem_clue.text = puzzle.get_clue(nc.seq, Word.DOWN)
        pass

    def create_elem_grid(self, elem_crossword):
        """ Creates the <grid> element """
        elem_grid = ET.SubElement(elem_crossword, "grid")
        elem_grid.set("width", str(self.puzzle.n))
        elem_grid.set("height", str(self.puzzle.n))

        # Add the <grid-look> element
        self.create_elem_grid_look(elem_grid)

        # Add the cells, iterating by row within column
        puzzle = self.puzzle
        n = puzzle.n
        for c in range(1, n+1):
            for r in range(1, n + 1):

                # Every cell is mentioned, somehow
                elem_cell = ET.SubElement(elem_grid, "cell")
                elem_cell.set("x", str(c))
                elem_cell.set("y", str(r))

                # Black cells get only type=block
                if puzzle.is_black_cell(r, c):
                    elem_cell.set("type", "block")
                else:
                    # Non-black cells get the current letter
                    letter = puzzle.get_cell(r, c)
                    elem_cell.set("solution", letter)

                    # In addition, if this is the start of a numbered cell,
                    # add the "number" attribute
                    nc = puzzle.get_numbered_cell(r, c)
                    if nc:
                        number = str(nc.seq)
                        elem_cell.set("number", number)
        pass

    def create_elem_grid_look(self, elem_grid):
        elem_grid_look = ET.SubElement(elem_grid, "grid-look")
        elem_grid_look.set("numbering-scheme", "normal")
        elem_grid_look.set("cell-size-in-pixels", str(self.CELL_SIZE_IN_PIXELS))
        elem_grid_look.set("clue-square-divider-width", str(self.CLUE_SQUARE_DIVIDER_WIDTH))
        pass

