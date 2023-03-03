import json

from crossword.cells import NumberedCell
from crossword.grids import Grid
from crossword.words import Word, AcrossWord, DownWord

# Do not delete this line! It is necessary so that the import
# of NumberedCell is never optimized away by the IDE
dummy_numbered_cell = NumberedCell(1, 1, 1, 1, 1)


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
        self.black_cells = set(grid.get_black_cells())
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

    def to_python(self, fp):
        """Generate code that will reconstruct this puzzle"""

        self.grid.to_python(fp)

        # Import Puzzle
        fp.write("from crossword.puzzles import Puzzle" + "\n")
        fp.write("from crossword.words import Word, AcrossWord, DownWord" + "\n")
        fp.write("\n")

        # Define a function
        fp.write("def get_puzzle(grid):" + "\n")
        title_as_string = None if not self.title else f'"{self.title}"'
        fp.write(f"    puzzle = Puzzle(grid, title={title_as_string})" + "\n")

        # Do black cells
        fp.write(f"    for bc in grid.get_black_cells():" + "\n")
        fp.write(f"        puzzle.black_cells.add(bc)" + "\n")

        # Do numbered cells
        fp.write(f"    puzzle.numbered_cells = []" + "\n")
        fp.write(f"    for nc in grid.get_numbered_cells():" + "\n")
        fp.write(f"        puzzle.numbered_cells.append(nc)" + "\n")

        # Do across words
        if self.across_words is None:
            fp.write("    puzzle.across_words = None" + "\n")
        else:
            for k, v in self.across_words.items():
                text = '"' + v.get_text() + '"'
                fp.write(f'    puzzle.get_across_word({k}).set_text({text})' + "\n")
                clue = v.get_clue()
                if clue is not None:
                    fp.write(f'    puzzle.get_across_word({k}).set_clue("{clue}")' + "\n")

        # Do down words
        if self.down_words is None:
            fp.write("    puzzle.down_words = None" + "\n")
        else:
            for k, v in self.down_words.items():
                text = '"' + v.get_text() + '"'
                fp.write(f'    puzzle.get_down_word({k}).set_text({text})' + "\n")
                clue = v.get_clue()
                if clue is not None:
                    fp.write(f'    puzzle.get_down_word({k}).set_clue("{clue}")' + "\n")

        # Do undo stack
        for listitem in self.undo_stack:
            fp.write(f"    puzzle.undo_stack.append({repr(listitem)})" + "\n")

        # Do redo stack
        for listitem in self.redo_stack:
            fp.write(f"    puzzle.redo_stack.append({repr(listitem)})" + "\n")

        # Return the new grid
        fp.write("    return puzzle" + "\n\n")

        fp.write("grid = get_grid()" + "\n")
        fp.write("result = get_puzzle(grid)" + "\n")

        pass

    @staticmethod
    def from_python(stmts):
        exec(stmts)
        new_puzzle = eval("result")
        return new_puzzle

    def replace_grid(self, newgrid) -> None:
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

        across_clues = {x['text']: x['clue'] for x in obj['across_words']}
        down_clues = {x['text']: x['clue'] for x in obj['down_words']}
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

    def initialize_words(self) -> None:
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

    def __eq__(self, other) -> bool:
        thisjson = self.to_json()
        thatjson = other.to_json()
        return thisjson == thatjson

    def __id__(self) -> int:
        return id(self.to_json())

    def __hash__(self) -> int:
        return hash(self.to_json())

    #   ========================================================
    #   Getters and setters
    #   ========================================================

    def get_cell(self, r: int, c: int) -> str:
        return self.cells.get((r, c), None)

    def set_cell(self, r: int, c: int, letter: str) -> None:
        self.cells[(r, c)] = letter

    def get_word(self, seq: int, direction: str) -> Word:
        """ Returns the word at <seq><direction> """
        word = None
        if direction == Word.ACROSS:
            word = self.get_across_word(seq)
        elif direction == Word.DOWN:
            word = self.get_down_word(seq)
        return word

    def get_text(self, seq: int, direction: str) -> str:
        """ Returns the text of the word at <seq><directino>"""
        word = self.get_word(seq, direction)
        return word.get_text()

    def set_text(self, seq: int, direction: str, text: str, undo: bool = True) -> None:
        """ Sets the text of the word at <seq><direction> """
        word: Word = self.get_word(seq, direction)
        if undo:
            new_value = text
            old_value = word.get_text()
            if old_value != new_value:
                undoable = ['text', seq, direction, old_value]
                self.undo_stack.append(undoable)
        word.set_text(text)

    def get_clue(self, seq: int, direction: str) -> str:
        """ Returns the clue of the word at <seq><directino>"""
        word = self.get_word(seq, direction)
        return word.get_clue()

    def set_clue(self, seq: int, direction: str, clue: str) -> None:
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

    def get_across_word(self, seq: int) -> Word:
        """ Returns the word for <seq> across, or None"""
        return self.across_words.get(seq, None)

    def get_down_word(self, seq: int) -> Word:
        """ Returns the word for <seq> down, or None"""
        return self.down_words.get(seq, None)

    def is_black_cell(self, r: int, c: int) -> bool:
        return (r, c) in self.black_cells

    def get_numbered_cell(self, r: int, c: int) -> NumberedCell:
        """ Returns the numbered cell that starts at this (r, c), or None """
        result = None
        for nc in self.numbered_cells:
            if nc.r == r and nc.c == c:
                result = nc
                break
        return result

    def get_numbered_cell_across(self, r: int, c: int) -> NumberedCell:
        result = None
        for nc in self.numbered_cells:
            if nc.r == r:
                for i in range(nc.a):
                    if c == nc.c + i:
                        return nc
        return result

    def get_numbered_cell_down(self, r: int, c: int) -> NumberedCell:
        result = None
        for nc in self.numbered_cells:
            if nc.c == c:
                for i in range(nc.d):
                    if r == nc.r + i:
                        return nc
        return result

    def get_word_count(self) -> int:
        """ Returns the number of words in the puzzle """
        return self.grid.get_word_count()

    def get_word_lengths(self) -> dict[int, dict[str, list]]:
        """ Returns a list of word lengths and words of that length """
        return self.grid.get_word_lengths()

    #   ========================================================
    #   undo / redo logic
    #   ========================================================

    def undo(self) -> None:
        """ Undoes the last change """
        self.undoredo(self.undo_stack, self.redo_stack)

    def redo(self) -> None:
        """ Redoes the last change """
        self.undoredo(self.redo_stack, self.undo_stack)

    def undoredo(self, stackfrom: list, stackto: list):

        if len(stackfrom) == 0:
            return  # Nothing to do

        # Pop the doable from the stack and get its type
        doable = stackfrom.pop()
        do_type = doable[0]

        if do_type == 'text':
            # Extract the set text parameters from the doable
            do_seq = doable[1]
            do_direction = doable[2]
            do_text = doable[3]

            # Push the current text for this word to the undo stack
            old_text = self.get_text(do_seq, do_direction)
            stackto.append([do_type, do_seq, do_direction, old_text])

            # and set the text to the popped value
            self.set_text(do_seq, do_direction, do_text, undo=False)

    #   ========================================================
    #   to_json and from_json logic
    #   ========================================================

    def to_json(self) -> str:
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
    def from_json(jsonstr: str) -> "Puzzle":
        image: dict = json.loads(jsonstr)

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
        puzzle._title = title  # Can't use the undo/redo here yet

        # Reload the "ACROSS" words
        awlist = image['across_words']
        for aw in awlist:
            seq = aw['seq']
            text = aw['text']
            clue = aw['clue']
            word = puzzle.get_across_word(seq)
            word.set_text(text)  # TODO: Can't do this - undo/redo
            word.set_clue(clue)  # TODO: Can't do this - undo/redo

        # Reload the "DOWN" words
        dwlist = image['down_words']
        for dw in dwlist:
            seq = dw['seq']
            text = dw['text']
            clue = dw['clue']
            word = puzzle.get_down_word(seq)
            word.set_text(text)  # TODO: Can't do this - undo/redo
            word.set_clue(clue)  # TODO: Can't do this - undo/redo

        # Reload the undo/redo stacks
        puzzle.undo_stack = image.get('undo_stack', [])
        puzzle.redo_stack = image.get('redo_stack', [])

        # Done
        return puzzle

    #   ========================================================
    #   Internal methods
    #   ========================================================

    def validate(self) -> (bool, list[str]):
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

    def validate_duplicate_words(self) -> list[str]:
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

    def get_statistics(self) -> dict[str, any]:
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

    def __str__(self) -> str:
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
