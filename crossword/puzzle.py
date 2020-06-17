import json

from crossword import AcrossWord, DownWord, Grid


class Puzzle:
    """
    The crossword puzzle.  See design.md for documentation.
    """

    WHITE = " "
    BLACK = "*"

    def __init__(self, grid, title=None):
        """
        Constructor. Internally, the puzzle is not represented as a matrix,
        but rather as a map of (r, c) to single-character strings.
        The puzzle is initially set to all empty.
        """
        self.grid = grid
        self.n = grid.n
        self.black_cells = grid.get_black_cells()
        self.numbered_cells = grid.get_numbered_cells()
        self.across_words = None
        self.down_words = None

        cells = {}
        self.cells = cells
        self.title = title

        # All cells are initially empty
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                cells[(r, c)] = Puzzle.WHITE

        # Except for black cells
        for bc in self.black_cells:
            cells[bc] = Puzzle.BLACK

        # Now populate the across and down words
        self.initialize_words()

    def initialize_words(self):
        # We know where the words go
        self.across_words = {}
        self.down_words = {}
        for numbered_cell in self.numbered_cells:

            # Yes, this is an across word
            if numbered_cell.across_length:
                self.across_words[numbered_cell.seq] = AcrossWord(self, numbered_cell.seq)

            # Yes, this is a down word
            if numbered_cell.down_length:
                self.down_words[numbered_cell.seq] = DownWord(self, numbered_cell.seq)

    def replace_grid(self, grid):
        """ Use a new grid for this puzzle """

        # Make sure new grid is the same size
        if self.n != grid.n:
            errmsg = f"Incompatible sizes: puzzle={self.n}, new grid={grid.n}"
            raise ValueError(errmsg)

        self.black_cells = grid.get_black_cells()
        self.numbered_cells = grid.get_numbered_cells()

        # Set all the old black cells to white
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                if self.cells[(r, c)] == Puzzle.BLACK:
                    self.cells[(r, c)] = Puzzle.WHITE

        # Now set the new black cells
        for bc in self.black_cells:
            self.cells[bc] = Puzzle.BLACK

        # Repopulate the across and down words
        self.initialize_words()

    #   ========================================================
    #   Getters and setters
    #   ========================================================

    def get_cell(self, r, c):
        return self.cells.get((r, c), None)

    def set_cell(self, r, c, letter):
        self.cells[(r, c)] = letter

    def get_across_word(self, seq):
        """ Returns the word for <seq> across, or None"""
        return self.across_words.get(seq, None)

    def get_down_word(self, seq):
        """ Returns the word for <seq> down, or None"""
        return self.down_words.get(seq, None)

    def is_black_cell(self, r, c):
        return (r, c) in self.black_cells

    def get_numbered_cell(self, r, c):
        result = None
        for nc in self.numbered_cells:
            if nc.r == r and nc.c == c:
                result = nc
                break
        return result

    def accept(self, visitor):
        visitor.visit_puzzle(self)

    def get_word_count(self):
        """ Returns the number of words in the puzzle """
        return self.grid.get_word_count()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    #   ========================================================
    #   to_json and from_json logic
    #   ========================================================

    def to_json(self):
        image = dict()
        image['n'] = self.n
        image['title'] = self.title
        image['cells'] = [cellsrow for cellsrow in str(self).split('\n')]
        image['black_cells'] = [black_cell for black_cell in self.black_cells]

        # Numbered cells
        nclist = list()
        for numbered_cell in self.numbered_cells:
            ncdict = vars(numbered_cell)
            nclist.append(ncdict)
        image['numbered_cells'] = nclist

        # Across words
        awlist = list()
        for seq in sorted(self.across_words.keys()):
            across_word = self.across_words[seq]
            awdict = {
                'seq': seq,
                'text': across_word.get_text(),
                'clue': across_word.get_clue()
            }
            awlist.append(awdict)
        image['across_words'] = awlist

        # Down words
        dwlist = list()
        for seq in sorted(self.down_words.keys()):
            down_word = self.down_words[seq]
            dwdict = {
                'seq': seq,
                'text': down_word.get_text(),
                'clue': down_word.get_clue()
            }
            dwlist.append(dwdict)
        image['down_words'] = dwlist

        # Create string in JSON format
        jsonstr = json.dumps(image, indent=2)

        return jsonstr

    @staticmethod
    def from_json(jsonstr):
        image = json.loads(jsonstr)

        # Create a puzzle of the specified size
        n = image['n']
        grid = Grid(n)

        # Initialize the black cells
        black_cells = image['black_cells']
        for black_cell in black_cells:
            grid.add_black_cell(*black_cell)

        # Create the puzzle
        puzzle = Puzzle(grid)
        title = image.get('title', None)
        puzzle.title = title

        # Reload the "ACROSS" words
        awlist = image['across_words']
        for aw in awlist:
            seq = aw['seq']
            text = aw['text']
            clue = aw['clue']
            word = puzzle.get_across_word(seq)
            word.set_text(text)
            word.set_clue(clue)

        # Reload the "DOWN" words
        dwlist = image['down_words']
        for dw in dwlist:
            seq = dw['seq']
            text = dw['text']
            clue = dw['clue']
            word = puzzle.get_down_word(seq)
            word.set_text(text)
            word.set_clue(clue)

        # Done
        return puzzle

    #   ========================================================
    #   Internal methods
    #   ========================================================

    def validate(self):
        """ Validates puzzle for errors """

        grid = self.grid
        errors = dict()
        errors['interlock'] = grid.validate_interlock()
        errors['unchecked'] = grid.validate_unchecked_squares()
        errors['wordlength'] = grid.validate_minimum_word_length()
        errors['dupwords'] = self.validate_duplicate_words()

        ok = True
        for error_key, error_list in errors.items():
            if len(error_list) > 0:
                ok = False

        return ok, errors

    def validate_duplicate_words(self):
        """ Checks whether there are any duplicate words """

        # Create a map of unique word text to a list of places it's used
        uwmap = {}

        for seq, word in self.across_words.items():
            if not word.is_complete():
                continue
            text = word.get_text()
            if text not in uwmap:
                uwmap[text] = []
            place = f"{word.seq} across"
            uwmap[text].append(place)

        for seq, word in self.down_words.items():
            if not word.is_complete():
                continue
            text = word.get_text()
            if text not in uwmap:
                uwmap[text] = []
            place = f"{word.seq} down"
            uwmap[text].append(place)

        # For any unique word text that's used in more than one place,
        # issue an error message
        error_list = []
        for text, places in uwmap.items():
            if len(places) > 1:
                errmsg = f"'{text}' is used in {', '.join(places)}"
                error_list.append(errmsg)
            pass

        return error_list

    def get_statistics(self):
        """ Returns a dictionary of grid statistics """
        stats = dict()
        ok, errors = self.validate()
        stats['valid'] = ok
        stats['errors'] = errors
        stats['size'] = f"{self.n} x {self.n}"
        stats['wordcount'] = self.get_word_count()
        stats['wordlengths'] = self.grid.get_word_lengths()
        return stats

    def __str__(self):
        sb = f'+{"-" * (self.n * 2 - 1)}+' + "\n"
        for r in range(1, self.n + 1):
            if r > 1:
                sb += '\n'
            row = "|"
            for c in range(1, self.n + 1):
                cell = self.get_cell(r, c)
                if c > 1:
                    row += "|"
                row += cell
            row += "|"
            sb += row
        sb += "\n"
        sb += f'+{"-" * (self.n * 2 - 1)}+'
        return sb
