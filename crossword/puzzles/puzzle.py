import json
from crossword.words import Word, AcrossWord, DownWord
from crossword.grids import Grid


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
        self.undo_stack = None
        self.redo_stack = None
        self.cells = {}
        self._title = title

        # All cells are initially empty
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                self.cells[(r, c)] = Puzzle.WHITE

        # Except for black cells
        for bc in self.black_cells:
            self.cells[bc] = Puzzle.BLACK

        self.initialize_words()

    def replace_grid(self, newgrid):
        if newgrid.n != self.n:
            raise ValueError("Incompatible grid sizes")
        # Save the JSON image so that clues can be reconstructed
        oldjson = self.to_json()

        self.grid = newgrid
        for bc in self.black_cells:
            self.cells[bc] = Puzzle.WHITE
        self.black_cells = newgrid.get_black_cells()
        self.numbered_cells = newgrid.get_numbered_cells()
        for bc in self.black_cells:
            self.cells[bc] = Puzzle.BLACK
        self.initialize_words()

        # Now set the clues for words that have not changed
        obj = json.loads(oldjson)

        across_clues = {x['text']:x['clue'] for x in obj['across_words']}
        down_clues = {x['text']:x['clue'] for x in obj['down_words']}
        cluemap = {**across_clues, **down_clues}

        for word in self.across_words.values():
            text = word.get_text()
            clue = cluemap.get(text, None)
            if clue:
                word.set_clue(clue)

        for word in self.down_words.values():
            text = word.get_text()
            clue = cluemap.get(text, None)
            if clue:
                word.set_clue(clue)

        pass  # TODO replace the clues

    def initialize_words(self):
        # Now populate the across and down words
        self.across_words = {}
        self.down_words = {}
        for numbered_cell in self.numbered_cells:

            # Yes, this is an across word
            if numbered_cell.a:
                self.across_words[numbered_cell.seq] = AcrossWord(self, numbered_cell.seq)

            # Yes, this is a down word
            if numbered_cell.d:
                self.down_words[numbered_cell.seq] = DownWord(self, numbered_cell.seq)

        self.undo_stack = []
        self.redo_stack = []

    def __eq__(self, other):
        return self.to_json() == other.to_json()

    def __id__(self):
        return id(self.to_json())

    def __hash__(self):
        return hash(self.to_json())

    #   ========================================================
    #   Getters and setters
    #   ========================================================

    def get_cell(self, r, c):
        return self.cells.get((r, c), None)

    def set_cell(self, r, c, letter):
        self.cells[(r, c)] = letter

    def get_word(self, seq, direction):
        """ Returns the word at <seq><direction> """
        word = None
        if direction == Word.ACROSS:
            word = self.get_across_word(seq)
        elif direction == Word.DOWN:
            word = self.get_down_word(seq)
        return word

    def get_text(self, seq, direction):
        """ Returns the text of the word at <seq><directino>"""
        word = self.get_word(seq, direction)
        return word.get_text()

    def set_text(self, seq, direction, text, undo=True):
        """ Sets the text of the word at <seq><direction> """
        word = self.get_word(seq, direction)
        if undo:
            new_value = text
            old_value = word.get_text()
            if old_value != new_value:
                undoable = ['text', seq, direction, old_value]
                self.undo_stack.append(undoable)
        word.set_text(text)

    def get_clue(self, seq, direction):
        """ Returns the clue of the word at <seq><directino>"""
        word = self.get_word(seq, direction)
        return word.get_clue()

    def set_clue(self, seq, direction, clue):
        """ Sets the clue of the word at <seq><direction> """
        word = self.get_word(seq, direction)
        word.set_clue(clue)

    @property
    def title(self):
        """ Returns the puzzle title """
        return self._title

    @title.setter
    def title(self, title):
        """ Sets the puzzle title """
        self._title = title

    def get_across_word(self, seq):
        """ Returns the word for <seq> across, or None"""
        return self.across_words.get(seq, None)

    def get_down_word(self, seq):
        """ Returns the word for <seq> down, or None"""
        return self.down_words.get(seq, None)

    def is_black_cell(self, r, c):
        return (r, c) in self.black_cells

    def get_numbered_cell(self, r, c):
        """ Returns the numbered cell that starts at this (r, c), or None """
        result = None
        for nc in self.numbered_cells:
            if nc.r == r and nc.c == c:
                result = nc
                break
        return result

    def get_numbered_cell_across(self, r, c):
        for nc in self.numbered_cells:
            if nc.r == r:
                for i in range(nc.a):
                    if c == nc.c + i:
                        return nc
        return None

    def get_numbered_cell_down(self, r, c):
        for nc in self.numbered_cells:
            if nc.c == c:
                for i in range(nc.d):
                    if r == nc.r + i:
                        return nc
        return None


    def get_word_count(self):
        """ Returns the number of words in the puzzle """
        return self.grid.get_word_count()

    def get_word_lengths(self):
        """ Returns a list of word lengths and words of that length """
        return self.grid.get_word_lengths()

    #   ========================================================
    #   undo / redo logic
    #   ========================================================

    def undo(self):
        """ Undoes the last change """

        if len(self.undo_stack) == 0:
            return  # Nothing to undo

        # Pop the undoable from the undo stack and get its type
        undoable = self.undo_stack.pop()
        undo_type = undoable[0]

        if undo_type == 'text':
            # Extract the set text parameters from the undoable
            undo_seq = undoable[1]
            undo_direction = undoable[2]
            undo_text = undoable[3]

            # Push the current text for this word to the redo stack
            old_text = self.get_text(undo_seq, undo_direction)
            self.redo_stack.append([undo_type, undo_seq, undo_direction, old_text])

            # and set the text to the popped value
            self.set_text(undo_seq, undo_direction, undo_text, undo=False)

        pass

    def redo(self):
        """ Redoes the last change """

        if len(self.redo_stack) == 0:
            return  # Nothing to redo

        # Pop the undoable from the redo stack and get its type
        undoable = self.redo_stack.pop()
        undo_type = undoable[0]

        if undo_type == 'text':
            # Extract the set text parameters from the undoable
            undo_seq = undoable[1]
            undo_direction = undoable[2]
            undo_text = undoable[3]

            # Push the current text for this word to the undo stack
            old_text = self.get_text(undo_seq, undo_direction)
            self.undo_stack.append([undo_type, undo_seq, undo_direction, old_text])

            # and set the text to the popped value
            self.set_text(undo_seq, undo_direction, undo_text, undo=False)

        pass

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

        # Undo/redo stacks

        image['undo_stack'] = self.undo_stack
        image['redo_stack'] = self.redo_stack

        # Create string in JSON format
        jsonstr = json.dumps(image)

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
        puzzle._title = title   # Can't use the undo/redo here yet

        # Reload the "ACROSS" words
        awlist = image['across_words']
        for aw in awlist:
            seq = aw['seq']
            text = aw['text']
            clue = aw['clue']
            word = puzzle.get_across_word(seq)
            word.set_text(text)     # TODO: Can't do this - undo/redo
            word.set_clue(clue)     # TODO: Can't do this - undo/redo

        # Reload the "DOWN" words
        dwlist = image['down_words']
        for dw in dwlist:
            seq = dw['seq']
            text = dw['text']
            clue = dw['clue']
            word = puzzle.get_down_word(seq)
            word.set_text(text)     # TODO: Can't do this - undo/redo
            word.set_clue(clue)     # TODO: Can't do this - undo/redo

        # Reload the undo/redo stacks
        puzzle.undo_stack = image.get('undo_stack', [])
        puzzle.redo_stack = image.get('redo_stack', [])

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
        stats['wordlengths'] = self.get_word_lengths()
        stats['blockcount'] = len(self.black_cells)
        return stats

    def __str__(self):
        sb = f'+{"-" * (self.n * 2 - 1)}+' + "\n"
        for r in range(1, self.n + 1):
            if r > 1:
                sb += '\n'
            row = "|"
            for c in range(1, self.n + 1):
                cell = self.get_cell(r, c)
                if not cell:
                    cell = " "
                if c > 1:
                    row += "|"
                row += cell
            row += "|"
            sb += row
        sb += "\n"
        sb += f'+{"-" * (self.n * 2 - 1)}+'
        return sb
