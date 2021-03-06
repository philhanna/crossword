from io import StringIO

from crossword import Puzzle

userid = 1  # TODO Replace hard-coded user ID


def get_indent():
    """ Amount by which to indent each line of input """
    return " " * 5


def get_author_name(user):
    """ Formatted string with author's name and email """
    author_name = user.author_name
    fullname = f"by {author_name}"
    return fullname


class PuzzlePublishAcrossLite:
    """ Creates a text file with the puzzle and clues

    :param user a DBUser object (or mock, if unit testing)
    :param puzzle the puzzle object
    :param basename the puzzle name

    Format is documented here:
    https://www.litsoft.com/across/docs/AcrossTextFormat.pdf
    """

    def __init__(self, user, puzzle: Puzzle, basename: str):
        """ Constructor """
        self.user = user
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

    def get_title(self):
        """ Returns the puzzle title or blank """
        title = self.puzzle.title
        if not title:
            title = ""
        return title

    def get_gridlines(self):
        """ Generator that returns the rows of the puzzle """
        puzzle = self.puzzle
        n = puzzle.n
        for r in range(1, n + 1):
            rowstr = ""
            for c in range(1, n + 1):
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
            fp.write(get_indent() + self.get_title() + "\n")  # Blank line

            # AUTHOR
            fp.write("<AUTHOR>" + "\n")
            fp.write(get_indent() + get_author_name(self.user) + "\n")

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
