import json
from crossword import AcrossWord, DownWord, Grid, Word


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
        self._title = title

        # All cells are initially empty
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                cells[(r, c)] = Puzzle.WHITE

        # Except for black cells
        for bc in self.black_cells:
            cells[bc] = Puzzle.BLACK

        # Now populate the across and down words
        self.across_words = {}
        self.down_words = {}
        for numbered_cell in self.numbered_cells:

            # Yes, this is an across word
            if numbered_cell.across_length:
                self.across_words[numbered_cell.seq] = AcrossWord(self, numbered_cell.seq)

            # Yes, this is a down word
            if numbered_cell.down_length:
                self.down_words[numbered_cell.seq] = DownWord(self, numbered_cell.seq)

        self.undo_stack = []
        self.redo_stack = []

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

    def get_title(self):
        """ Returns the puzzle title """
        return self._title

    def set_title(self, title):
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

        if undo_type == "title":
            # Extract the set title parameters from the undoable
            undo_title = undoable[1]

            # Push the current title to the redo stack
            old_title = self.get_title()
            self.redo_stack.append([undo_type, old_title])

            # and set the title to the popped value
            self._title = undo_title

        elif undo_type == 'text':
            # Extract the set text parameters from the undoable
            undo_seq = undoable[1]
            undo_direction = undoable[2]
            undo_text = undoable[3]

            # Push the current text for this word to the redo stack
            old_text = self.get_text(undo_seq, undo_direction)
            self.redo_stack.append([undo_type, undo_seq, undo_direction, old_text])

            # and set the text to the popped value
            self.set_text(undo_seq, undo_direction, undo_text, undo=False)

        elif undo_type == 'clue':
            # Extract the set clue parameters from the undoable
            undo_seq = undoable[1]
            undo_direction = undoable[2]
            undo_clue = undoable[3]

            # Push the current clue for this word to the redo stack
            old_clue = self.get_clue(undo_seq, undo_direction)
            self.redo_stack.append([undo_type, undo_seq, undo_direction, old_clue])

            # and set the text to the popped value
            self.set_clue(undo_seq, undo_direction, undo_clue, undo=False)

        pass

    def redo(self):
        """ Redoes the last change """

        if len(self.redo_stack) == 0:
            return  # Nothing to undo

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
        image['title'] = self.get_title()
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
