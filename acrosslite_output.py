import os
import re
from io import StringIO

from configuration import Configuration
from puzzle import Puzzle


# Simple functions

def get_indent():
    """ Amount by which to indent each line of input """
    return " " * 5


def get_author_name():
    """ Formatted string with author's name and email """
    name = Configuration.get_author_name()
    email = Configuration.get_author_email()
    fullname = f"Created by {name} ({email})"
    return fullname


class AcrossLiteOutput:
    """ Creates a text file with the puzzle and clues

    Format is documented here:
    https://www.litsoft.com/across/docs/AcrossTextFormat.pdf
    """

    def __init__(self, puzzle: Puzzle, basename: str):
        """ Constructor """
        self.puzzle = puzzle
        self.basename = basename
        self.txtstr = self.generate_txt()

    def get_txt(self):
        """ Returns the completed text """
        return self.txtstr

    def get_size(self):
        """ Returns the size of the puzzle as nxn """
        n = self.puzzle.n
        size = f"{n}x{n}"
        return size

    def get_gridlines(self):
        """ Generator that returns the rows of the puzzle """
        puzzle = self.puzzle
        n = puzzle.n
        for r in range(1, n+1):
            rowstr = ""
            for c in range(1, n+1):
                if puzzle.is_black_cell(r, c):
                    rowstr += "."
                else:
                    cell = puzzle.get_cell(r, c)
                    rowstr += cell
            yield rowstr

    def get_across_clues(self):
        """ Generator that returns the across clues """
        puzzle = self.puzzle
        for seq in sorted(puzzle.across_words):
            word = puzzle.across_words[seq]
            clue = word.get_clue()
            if not clue:
                clue = ""
            yield clue

    def get_down_clues(self):
        """ Generator that returns the across clues """
        puzzle = self.puzzle
        for seq in sorted(puzzle.down_words):
            word = puzzle.down_words[seq]
            clue = word.get_clue()
            if not clue:
                clue = ""
            yield clue

    def generate_txt(self):
        """ Generates the AcrossLite text format"""
        with StringIO() as fp:
            # ACROSS PUZZLE
            fp.write("<ACROSS PUZZLE>" + "\n")

            # TITLE
            fp.write("<TITLE>" + "\n")
            fp.write("\n")  # Blank line

            # AUTHOR
            fp.write("<AUTHOR>" + "\n")
            fp.write(get_indent() + get_author_name() + "\n")

            # COPYRIGHT
            fp.write("<COPYRIGHT>" + "\n")
            fp.write("\n")  # Blank line

            # SIZE nxn
            fp.write("<SIZE>" + "\n")
            fp.write(get_indent() + self.get_size() + "\n")

            # GRID the rows of the puzzle
            fp.write("<GRID>" + "\n")
            for gridline in self.get_gridlines():
                fp.write(get_indent() + gridline + "\n")

            # ACROSS - the across clues
            fp.write("<ACROSS>" + "\n")
            for clue in self.get_across_clues():
                fp.write(get_indent() + clue + "\n")

            # DOWN - the down clues
            fp.write("<DOWN>" + "\n")
            for clue in self.get_down_clues():
                fp.write(get_indent() + clue + "\n")

            # NOTEPAD - describe the tool
            fp.write("<NOTEPAD>" + "\n")
            fp.write("Created with Crossword Puzzle Editor, by Phil Hanna" + "\n")
            fp.write("See https://github.com/philhanna/crossword" + "\n")

            # Get the full string (before you close the file)
            txtstr = fp.getvalue()

        # Return the body of the file
        return txtstr
