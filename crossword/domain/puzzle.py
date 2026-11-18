from __future__ import annotations

import json
from typing import Any
from .word import AcrossWord, DownWord, Word
from .grid import Grid
from .numbered_cell import NumberedCell
from .word_similarity import find_duplicate, is_near_duplicate


class Puzzle:
    """
    The crossword puzzle.  See design.md for documentation.
    """

    WHITE = " "
    BLACK = "*"

    def __init__(self, grid: Grid, title: str | None = None) -> None:
        """
        Constructor. Internally, the puzzle is not represented as a matrix,
        but rather as a map of (r, c) to single-character strings.
        The puzzle is initially set to all empty.
        """
        self.grid: Grid = grid
        self.n: int = grid.n
        self.across_words: dict[int, AcrossWord] | None = None
        self.down_words: dict[int, DownWord] | None = None
        self._puzzle_undo_stack: list[list] = []
        self._puzzle_redo_stack: list[list] = []
        self.grid_undo_stack: list[str] = []
        self.grid_redo_stack: list[str] = []
        self.last_mode: str = "grid"
        self.cells: dict[tuple[int, int], str] = {}
        self.circled_cells: set[tuple[int, int]] = set()
        self._title: str | None = title

        # All cells are initially empty
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                self.cells[(r, c)] = Puzzle.WHITE

        # Except for black cells
        for bc in self.black_cells:
            self.cells[bc] = Puzzle.BLACK

        self.initialize_words()

    def replace_grid(self, newgrid: Grid) -> None:
        if newgrid.n != self.n:
            raise ValueError("Incompatible grid sizes")
        self._apply_new_grid(newgrid)

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

    def __eq__(self, other: object) -> bool:
        return self.to_json() == other.to_json()

    def __id__(self) -> int:
        return id(self.to_json())

    def __hash__(self) -> int:
        return hash(self.to_json())

    #   ========================================================
    #   Getters and setters
    #   ========================================================

    def get_cell(self, r: int, c: int) -> str | None:
        """ Returns the letter at row r, column c (both 1-based, so the
        top left square is (1, 1)), or None if (r, c) is outside the grid """
        return self.cells.get((r, c), None)

    def set_cell(self, r: int, c: int, letter: str) -> None:
        """ Sets the letter at row r, column c (both 1-based, so the top
        left square is (1, 1)). Does nothing if the square is locked """
        if (r, c) in self.locked_cells:
            return  # silently a no-op; callers don't need a special case
        self.cells[(r, c)] = letter

    def get_word(self, seq: int, direction: str) -> Word | None:
        """ Returns the word at <seq><direction> """
        word = None
        if direction == Word.ACROSS:
            word = self.get_across_word(seq)
        elif direction == Word.DOWN:
            word = self.get_down_word(seq)
        return word

    def get_text(self, seq: int, direction: str) -> str:
        """ Returns the text of the word at <seq><direction>"""
        word = self.get_word(seq, direction)
        return word.get_text()

    def set_text(self, seq: int, direction: str, text: str,
                 undo: bool = True, check_duplicates: bool = True) -> None:
        """ Sets the text of the word at <seq><direction> """
        word = self.get_word(seq, direction)
        if undo:
            new_value = text
            old_value = word.get_text()
            if old_value != new_value:
                if check_duplicates:
                    texts_before = self._all_word_texts()
                    word.set_text(text)
                    try:
                        self._check_for_duplicates(word, texts_before)
                    except ValueError:
                        word.set_text(old_value)
                        raise
                undoable = ['text', seq, direction, old_value]
                self.undo_stack.append(undoable)
        word.set_text(text)

    def _all_word_texts(self) -> dict[tuple[int, str], str]:
        """ Maps (seq, direction) to the current text of every word """
        return {(w.seq, w.direction): w.get_text() for w in self._all_words()}

    def _all_words(self) -> list[Word]:
        return list(self.across_words.values()) + list(self.down_words.values())

    def _check_for_duplicates(self, entered: Word,
                              texts_before: dict[tuple[int, str], str]) -> None:
        """ Raises ValueError if any complete word whose text differs from
        texts_before - the word just entered, or a crossing word it
        completed - duplicates or is a near-duplicate (e.g. a plain plural)
        of another complete word in the puzzle. """
        complete = [w for w in self._all_words() if w.is_complete()]
        changed = [
            w for w in complete
            if texts_before[(w.seq, w.direction)] != w.get_text()
        ]
        for word in changed:
            for other in complete:
                if other is word:
                    continue
                if find_duplicate(word.get_text(), [other.get_text()]):
                    where = "" if word is entered else f" at {word.location}"
                    raise ValueError(
                        f"{word.get_text().strip()}{where} duplicates "
                        f"{other.get_text().strip()}, already used at {other.location}"
                    )

    def get_clue(self, seq: int, direction: str) -> str | None:
        """ Returns the clue of the word at <seq><directino>"""
        word = self.get_word(seq, direction)
        return word.get_clue()

    def set_clue(self, seq: int, direction: str, clue: str | None) -> None:
        """ Sets the clue of the word at <seq><direction> """
        word = self.get_word(seq, direction)
        word.set_clue(clue)

    def set_locked(self, seq: int, direction: str, value: bool) -> None:
        """ Sets whether the word at <seq><direction> is locked, with undo tracking """
        word = self.get_word(seq, direction)
        old_value = word.is_locked()
        if old_value != value:
            self.undo_stack.append(['locked', seq, direction, old_value])
        word.set_locked(value)

    def clear_unlocked(self) -> bool:
        """ Blanks text and clue for every unlocked word; returns True if anything changed """
        changes = []
        for word in list(self.across_words.values()) + list(self.down_words.values()):
            if word.is_locked():
                continue
            old_text, old_clue = word.get_text(), word.get_clue()
            blank = " " * word.length
            if old_text != blank or old_clue:
                changes.append((word.seq, word.direction, old_text, old_clue))
                word.set_text(blank)
                word.set_clue(None)
        if changes:
            self.undo_stack.append(['clear', changes])
        return bool(changes)

    def apply_fill(self, fills: dict[tuple[int, str], str]) -> bool:
        """ Writes the given texts into the words they name, as one undoable step.

        fills maps (seq, direction) to the new text of that word. Words whose
        text would not change are skipped. Returns True if anything changed """
        changes = []
        for (seq, direction), text in fills.items():
            word = self.get_word(seq, direction)
            old_text = word.get_text()
            if old_text != text:
                changes.append((seq, direction, old_text))
        for seq, direction, _ in changes:
            self.get_word(seq, direction).set_text(fills[(seq, direction)])
        if changes:
            self.undo_stack.append(['autofill', changes])
        return bool(changes)

    def _swap_fill_texts(self, changes: list) -> list:
        """ Puts back the text of each (seq, direction, text) in changes and
        returns the same list holding the texts that were replaced, so the
        same step can be applied the other way round """
        replaced = [(seq, direction, self.get_text(seq, direction))
                    for seq, direction, _ in changes]
        for seq, direction, text in changes:
            self.get_word(seq, direction).set_text(text)
        return replaced

    def swap_words(self, seq_a: int, seq_b: int, direction: str) -> bool:
        """
        Swaps the letters and clues of two locked words of the same direction
        and length, and returns True. Returns False, changing nothing, if the
        two are the same word or already hold the same letters.

        Both words stay locked. They are unlocked only while their letters are
        written, because writes into locked squares are silently ignored.
        The clue of every crossing word whose letters change is cleared.

        Raises ValueError, leaving the puzzle exactly as it was, if either
        word does not exist, is not locked, or the lengths differ; if a
        crossing word that is locked would change; or if the swap would
        duplicate another word in the puzzle.
        """
        word_a = self.get_word(seq_a, direction)
        word_b = self.get_word(seq_b, direction)
        if word_a is None or word_b is None:
            raise ValueError("No such word to swap")
        if not (word_a.is_locked() and word_b.is_locked()):
            raise ValueError("Only locked words can be swapped")
        if word_a.length != word_b.length:
            raise ValueError(
                f"{word_a.location} and {word_b.location} have different lengths")
        text_a, text_b = word_a.get_text(), word_b.get_text()
        if word_a is word_b or text_a == text_b:
            return False

        crossing = self._crossing_words_that_change(word_a, word_b)
        for other in crossing:
            if other.is_locked():
                raise ValueError(
                    f"Swapping would change {other.location}, which is locked")

        before = [self._snapshot(w) for w in [word_a, word_b] + crossing]
        texts_before = self._all_word_texts()
        clue_a, clue_b = word_a.get_clue(), word_b.get_clue()

        word_a.set_locked(False)
        word_b.set_locked(False)
        try:
            word_a.set_text(text_b)
            word_b.set_text(text_a)
            word_a.set_clue(clue_b)
            word_b.set_clue(clue_a)
            for other in crossing:
                other.set_clue(None)
            try:
                self._check_for_duplicates(word_a, texts_before)
            except ValueError:
                self._restore(before)
                raise
        finally:
            word_a.set_locked(True)
            word_b.set_locked(True)
        self.undo_stack.append(['swap', seq_a, seq_b, direction, before])
        return True

    @staticmethod
    def _snapshot(word: Word) -> tuple[int, str, str, str | None]:
        return (word.seq, word.direction, word.get_text(), word.get_clue())

    def _restore(self, snapshot: list[tuple[int, str, str, str | None]]) -> None:
        """ Puts back the letters and clue of each (seq, direction, text, clue) """
        for seq, direction, text, clue in snapshot:
            word = self.get_word(seq, direction)
            word.set_text(text)
            word.set_clue(clue)

    @staticmethod
    def _crossing_words_that_change(word_a: Word, word_b: Word) -> list[Word]:
        """ The words crossing word_a or word_b at a square where the two
        words differ, without duplicates """
        found = {}
        for word, other in ((word_a, word_b), (word_b, word_a)):
            cells = zip(word.cell_iterator(), word.get_text(), other.get_text())
            for (r, c), mine, theirs in cells:
                if mine == theirs:
                    continue
                crossing = word.get_crossing_word(r, c)
                if crossing is not None:
                    found[(crossing.seq, crossing.direction)] = crossing
        return list(found.values())

    def _swap_history(self, undoable: list) -> list:
        """ Undoes or redoes a 'swap' entry; returns the opposite entry """
        _, seq_a, seq_b, direction, changes = undoable
        words = [self.get_word(seq_a, direction), self.get_word(seq_b, direction)]
        opposite = [self._snapshot(self.get_word(seq, d)) for seq, d, _, _ in changes]
        locks = [w.is_locked() for w in words]
        for w in words:
            w.set_locked(False)
        try:
            self._restore(changes)
        finally:
            for w, locked in zip(words, locks):
                w.set_locked(locked)
        return ['swap', seq_a, seq_b, direction, opposite]

    def is_circled(self, r: int, c: int) -> bool:
        """ Returns True if the square at (r, c) is circled """
        return (r, c) in self.circled_cells

    def toggle_circle(self, r: int, c: int, undo: bool = True) -> None:
        """ Circles or un-circles the white square at (r, c) """
        if not (1 <= r <= self.n and 1 <= c <= self.n):
            raise ValueError(f"({r}, {c}) is outside the grid")
        if self.is_black_cell(r, c):
            raise ValueError("Black squares can't be circled")
        self.circled_cells ^= {(r, c)}
        if undo:
            self.undo_stack.append(['circle', r, c])

    @property
    def undo_stack(self) -> list[list]:
        """Compatibility alias for the Puzzle-mode undo stack."""
        return self._puzzle_undo_stack

    @undo_stack.setter
    def undo_stack(self, value: list[list]) -> None:
        self._puzzle_undo_stack = value

    @property
    def redo_stack(self) -> list[list]:
        """Compatibility alias for the Puzzle-mode redo stack."""
        return self._puzzle_redo_stack

    @redo_stack.setter
    def redo_stack(self, value: list[list]) -> None:
        self._puzzle_redo_stack = value

    @property
    def black_cells(self) -> list[tuple[int, int]]:
        """ Returns black cells from the grid """
        return self.grid.get_black_cells()

    @property
    def locked_cells(self) -> set[tuple[int, int]]:
        """ Returns cells covered by any locked word """
        cells = set()
        for word in list(self.across_words.values()) + list(self.down_words.values()):
            if word.is_locked():
                cells.update(word.cell_iterator())
        return cells

    @property
    def numbered_cells(self) -> list[NumberedCell]:
        """ Returns numbered cells from the grid """
        return self.grid.get_numbered_cells()

    @property
    def title(self) -> str | None:
        """ Returns the puzzle title """
        return self._title

    @title.setter
    def title(self, title: str | None) -> None:
        """ Sets the puzzle title """
        self._title = title

    def get_across_word(self, seq: int) -> AcrossWord | None:
        """ Returns the word for <seq> across, or None"""
        return self.across_words.get(seq, None)

    def get_down_word(self, seq: int) -> DownWord | None:
        """ Returns the word for <seq> down, or None"""
        return self.down_words.get(seq, None)

    def is_black_cell(self, r: int, c: int) -> bool:
        return (r, c) in self.black_cells

    def get_numbered_cell(self, r: int, c: int) -> NumberedCell | None:
        """ Returns the numbered cell that starts at this (r, c), or None """
        result = None
        for nc in self.numbered_cells:
            if nc.r == r and nc.c == c:
                result = nc
                break
        return result

    def get_word_count(self) -> int:
        """ Returns the number of words in the puzzle """
        return self.grid.get_word_count()

    def get_word_lengths(self) -> Any:
        """ Returns a list of word lengths and words of that length """
        return self.grid.get_word_lengths()

    def symmetric_point(self, r: int, c: int) -> tuple[int, int] | None:
        return self.grid.symmetric_point(r, c)

    def enter_grid_mode(self) -> None:
        self.last_mode = "grid"
        self.grid_undo_stack = []
        self.grid_redo_stack = []

    def enter_puzzle_mode(self) -> None:
        self.last_mode = "puzzle"
        self.undo_stack = []
        self.redo_stack = []

    def toggle_black_cell(self, r: int, c: int) -> None:
        newgrid = Grid.from_json(self.grid.to_json())
        self.grid_undo_stack.append(self.grid.to_json())
        self.grid_redo_stack = []
        if newgrid.is_black_cell(r, c):
            newgrid.remove_black_cell(r, c)
        else:
            newgrid.add_black_cell(r, c)
        self._apply_new_grid(newgrid)

    def rotate_grid(self) -> None:
        newgrid = Grid.from_json(self.grid.to_json())
        self.grid_undo_stack.append(self.grid.to_json())
        self.grid_redo_stack = []
        newgrid.rotate()
        self._apply_new_grid(newgrid)

    def apply_generated_grid(self, newgrid: Grid) -> None:
        self.grid_undo_stack.append(self.grid.to_json())
        self.grid_redo_stack = []
        self._apply_new_grid(newgrid)

    def undo_grid_change(self) -> None:
        if len(self.grid_undo_stack) == 0:
            return
        oldgrid_json = self.grid_undo_stack.pop()
        self.grid_redo_stack.append(self.grid.to_json())
        self._apply_new_grid(Grid.from_json(oldgrid_json))

    def redo_grid_change(self) -> None:
        if len(self.grid_redo_stack) == 0:
            return
        oldgrid_json = self.grid_redo_stack.pop()
        self.grid_undo_stack.append(self.grid.to_json())
        self._apply_new_grid(Grid.from_json(oldgrid_json))

    #   ========================================================
    #   undo / redo logic
    #   ========================================================

    def undo(self) -> None:
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

        elif undo_type == 'locked':
            # Extract the set locked parameters from the undoable
            undo_seq = undoable[1]
            undo_direction = undoable[2]
            undo_value = undoable[3]

            # Push the current locked state for this word to the redo stack
            word = self.get_word(undo_seq, undo_direction)
            old_value = word.is_locked()
            self.redo_stack.append([undo_type, undo_seq, undo_direction, old_value])

            # and set the locked state to the popped value
            word.set_locked(undo_value)

        elif undo_type == 'clear':
            # Restore the text and clue of every word that was cleared
            changes = undoable[1]
            redo_changes = []
            for seq, direction, old_text, old_clue in changes:
                word = self.get_word(seq, direction)
                redo_changes.append((seq, direction, word.get_text(), word.get_clue()))
                word.set_text(old_text)
                word.set_clue(old_clue)
            self.redo_stack.append([undo_type, redo_changes])

        elif undo_type == 'autofill':
            self.redo_stack.append([undo_type, self._swap_fill_texts(undoable[1])])

        elif undo_type == 'swap':
            self.redo_stack.append(self._swap_history(undoable))

        elif undo_type == 'circle':
            # Toggling is its own opposite
            self.toggle_circle(undoable[1], undoable[2], undo=False)
            self.redo_stack.append(undoable)

    def redo(self) -> None:
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

        elif undo_type == 'locked':
            # Extract the set locked parameters from the undoable
            undo_seq = undoable[1]
            undo_direction = undoable[2]
            undo_value = undoable[3]

            # Push the current locked state for this word to the undo stack
            word = self.get_word(undo_seq, undo_direction)
            old_value = word.is_locked()
            self.undo_stack.append([undo_type, undo_seq, undo_direction, old_value])

            # and set the locked state to the popped value
            word.set_locked(undo_value)

        elif undo_type == 'clear':
            # Restore the text and clue of every word that was cleared
            changes = undoable[1]
            undo_changes = []
            for seq, direction, old_text, old_clue in changes:
                word = self.get_word(seq, direction)
                undo_changes.append((seq, direction, word.get_text(), word.get_clue()))
                word.set_text(old_text)
                word.set_clue(old_clue)
            self.undo_stack.append([undo_type, undo_changes])

        elif undo_type == 'autofill':
            self.undo_stack.append([undo_type, self._swap_fill_texts(undoable[1])])

        elif undo_type == 'swap':
            self.undo_stack.append(self._swap_history(undoable))

        elif undo_type == 'circle':
            # Toggling is its own opposite
            self.toggle_circle(undoable[1], undoable[2], undo=False)
            self.undo_stack.append(undoable)

    #   ========================================================
    #   to_json and from_json logic
    #   ========================================================

    def to_json(self) -> str:
        image = dict()
        image['n'] = self.n
        image['title'] = self.title
        image['last_mode'] = self.last_mode
        image['cells'] = [cellsrow for cellsrow in str(self).split('\n')]
        image['black_cells'] = [black_cell for black_cell in self.black_cells]

        # Across words
        awlist = list()
        for seq in sorted(self.across_words.keys()):
            across_word = self.across_words[seq]
            awdict = {
                'seq': seq,
                'text': across_word.get_text(),
                'clue': across_word.get_clue(),
                'locked': across_word.is_locked()
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
                'clue': down_word.get_clue(),
                'locked': down_word.is_locked()
            }
            dwlist.append(dwdict)
        image['down_words'] = dwlist
        image['circled_cells'] = [list(cell) for cell in sorted(self.circled_cells)]
        image['undo_stack'] = self.undo_stack
        image['redo_stack'] = self.redo_stack
        image['puzzle_undo_stack'] = self.undo_stack
        image['puzzle_redo_stack'] = self.redo_stack
        image['grid_undo_stack'] = self.grid_undo_stack
        image['grid_redo_stack'] = self.grid_redo_stack

        # Create string in JSON format
        jsonstr = json.dumps(image)

        return jsonstr

    @staticmethod
    def from_json(jsonstr: str) -> Puzzle:
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
        puzzle.last_mode = image.get('last_mode', 'puzzle')
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
            word.set_locked(aw.get('locked', False))

        # Reload the "DOWN" words
        dwlist = image['down_words']
        for dw in dwlist:
            seq = dw['seq']
            text = dw['text']
            clue = dw['clue']
            word = puzzle.get_down_word(seq)
            word.set_text(text)     # TODO: Can't do this - undo/redo
            word.set_clue(clue)     # TODO: Can't do this - undo/redo
            word.set_locked(dw.get('locked', False))

        puzzle.circled_cells = {tuple(cell) for cell in image.get('circled_cells', [])}
        puzzle.undo_stack = image.get('puzzle_undo_stack', image.get('undo_stack', []))
        puzzle.redo_stack = image.get('puzzle_redo_stack', image.get('redo_stack', []))
        puzzle.grid_undo_stack = image.get('grid_undo_stack', [])
        puzzle.grid_redo_stack = image.get('grid_redo_stack', [])

        return puzzle

    #   ========================================================
    #   Internal methods
    #   ========================================================

    def _word_identity(self, direction: str, word: Word) -> tuple:
        cells = list(word.cell_iterator())
        return (
            direction,
            (word.numbered_cell.r, word.numbered_cell.c),
            tuple(cells),
            word.get_text(),
        )

    def _capture_clues_by_identity(self) -> dict[tuple, str]:
        clues = {}
        for word in self.across_words.values():
            clue = word.get_clue()
            if clue:
                clues[self._word_identity(Word.ACROSS, word)] = clue
        for word in self.down_words.values():
            clue = word.get_clue()
            if clue:
                clues[self._word_identity(Word.DOWN, word)] = clue
        return clues

    def _apply_new_grid(self, newgrid: Grid) -> None:
        old_black_cells = set(self.black_cells)
        clues_by_identity = self._capture_clues_by_identity()

        self.grid = newgrid

        new_black_cells = set(self.black_cells)
        for cell in old_black_cells - new_black_cells:
            self.cells[cell] = Puzzle.WHITE
        for cell in new_black_cells:
            self.cells[cell] = Puzzle.BLACK
        self.circled_cells -= new_black_cells

        self.initialize_words()

        for word in self.across_words.values():
            clue = clues_by_identity.get(self._word_identity(Word.ACROSS, word))
            if clue:
                word.set_clue(clue)

        for word in self.down_words.values():
            clue = clues_by_identity.get(self._word_identity(Word.DOWN, word))
            if clue:
                word.set_clue(clue)

    def validate(self) -> tuple[bool, dict[str, list]]:
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

        # Distinct texts where one is a plain plural of the other
        texts = list(uwmap)
        for i, text in enumerate(texts):
            for other in texts[i + 1:]:
                if is_near_duplicate(text, other):
                    errmsg = (f"'{text}' ({', '.join(uwmap[text])}) and "
                              f"'{other}' ({', '.join(uwmap[other])}) "
                              f"are near-duplicates")
                    error_list.append(errmsg)

        return error_list

    def is_filled(self) -> bool:
        """ True if the puzzle has at least one word and every word is complete """
        words = list(self.across_words.values()) + list(self.down_words.values())
        return bool(words) and all(w.is_complete() for w in words)

    def fill_fraction(self) -> float:
        """Fraction (0.0-1.0) of white cells that contain a letter.

        White cells are all non-black cells; a cell is 'filled' when its value
        is neither WHITE (' ') nor BLACK ('*'). Returns 0.0 when there are no
        white cells.
        """
        white = [v for v in self.cells.values() if v != Puzzle.BLACK]
        if not white:
            return 0.0
        filled = sum(1 for v in white if v != Puzzle.WHITE)
        return filled / len(white)

    def all_clues_complete(self) -> bool:
        """ True if every word has a non-empty clue """
        words = list(self.across_words.values()) + list(self.down_words.values())
        return bool(words) and all((w.get_clue() or "").strip() for w in words)

    def get_statistics(self) -> dict[str, Any]:
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
