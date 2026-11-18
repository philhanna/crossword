"""
Autofill use cases - fill every incomplete word of a puzzle from the word list.

Public interface:
  AutofillUseCases(word_list).autofill(puzzle, time_limit, seed) -> AutofillResult

The search works on a scratch copy of the letters, so the real puzzle is
changed only once, at the end, and only if every word could be filled.
"""

import random
import time
from dataclasses import dataclass, field

from crossword.domain.word import Word
from crossword.domain.word_similarity import find_duplicate
from crossword.ports.word_list_port import WordListPort

DEFAULT_TIME_LIMIT = 10.0

# The search restarts with a fresh random order when it has tried this many
# words without finishing, and each restart is allowed more tries than the last.
FIRST_ATTEMPT_BUDGET = 500
BUDGET_GROWTH = 2


class AutofillError(ValueError):
    """Raised when no fill could be found; the message says why."""


@dataclass
class AutofillResult:
    """What the search found.

    Attributes:
        fills: Maps (seq, direction) to the full text of every word that
            changed. Empty when the search failed.
        seed: The random seed used, so a run can be repeated.
        message: A readable explanation when the search failed.
    """

    fills: dict[tuple[int, str], str] = field(default_factory=dict)
    seed: int = 0
    message: str = ""

    @property
    def success(self) -> bool:
        return not self.message


class _Stop(Exception):
    """Internal: the time limit or the try budget ran out."""


class _TimeUp(_Stop):
    """Internal: the overall time limit has passed; no more restarts."""


class AutofillUseCases:
    """
    Fills the blanks of a puzzle with words from the word list.

    Constructor injection: takes a WordListPort instance.
    """

    def __init__(self, word_list: WordListPort):
        self.word_list = word_list
        self._index_by_length: dict[int, _LengthIndex] = {}

    def autofill(self, puzzle, time_limit: float = DEFAULT_TIME_LIMIT,
                 seed: int | None = None) -> AutofillResult:
        """
        Fill every incomplete word of the puzzle, or change nothing.

        Words that are already complete, locked words, and letters already
        in partly filled words are never changed. No word repeats another,
        or is its plain plural.

        Args:
            puzzle: The Puzzle to fill. It is changed (as one undo step)
                only if the whole puzzle could be filled.
            time_limit: Seconds to search before giving up
            seed: Random seed, for repeating a run; chosen at random if None

        Returns:
            An AutofillResult; check its success flag.
        """
        if seed is None:
            seed = random.randrange(1_000_000)
        result = AutofillResult(seed=seed)

        search = self._start_search(puzzle, time_limit, seed, result)
        if search is None:
            return result
        if not search.run():
            result.message = search.failure_message()
            return result

        result.fills = search.fills()
        puzzle.apply_fill(result.fills)
        return result

    def _start_search(self, puzzle, time_limit, seed, result):
        """Build the search, or return None (with result.message set) if the
        puzzle can be seen to be unfillable before searching."""
        words = list(puzzle.across_words.values()) + list(puzzle.down_words.values())
        for word in words:
            if word.is_locked() and not word.is_complete():
                result.message = (
                    f"{_label(word)} is locked but not filled in, so it "
                    f"can't be changed. Unlock it or fill it first.")
                return None

        lengths = {w.length for w in words if not w.is_complete()}
        indexes = {n: self._index_for(n) for n in lengths}
        search = _Search(puzzle, words, indexes, time_limit, random.Random(seed))

        stuck = search.slot_without_candidates()
        if stuck is not None:
            result.message = (
                f"No words fit {stuck.label} as it stands "
                f"(pattern {stuck.pattern()}).")
            return None
        return search

    def _index_for(self, length: int) -> "_LengthIndex":
        if length not in self._index_by_length:
            words = [w.upper() for w in self.word_list.get_matches(".*", length=length)]
            words = [w for w in words if len(w) == length and w.isascii() and w.isalpha()]
            self._index_by_length[length] = _LengthIndex(words, length)
        return self._index_by_length[length]


class _LengthIndex:
    """All the words of one length, with a fast way to find the ones that
    have a given letter in a given position.

    Each (position, letter) pair maps to a number whose binary digits mark
    which words have that letter there. Combining two such numbers with
    "and" gives the words that satisfy both, in a single step.
    """

    def __init__(self, words: list[str], length: int):
        self.words = words
        self.everything = (1 << len(words)) - 1
        size = (len(words) + 7) // 8
        builders: dict[tuple[int, str], bytearray] = {}
        for i, word in enumerate(words):
            for pos, letter in enumerate(word):
                bits = builders.setdefault((pos, letter), bytearray(size))
                bits[i >> 3] |= 1 << (i & 7)
        self.with_letter = {key: int.from_bytes(bits, "little")
                            for key, bits in builders.items()}

    def matching(self, letters: list[str]) -> int:
        """Bits of the words fitting letters, where " " means any letter."""
        bits = self.everything
        for pos, letter in enumerate(letters):
            if letter != " ":
                bits &= self.with_letter.get((pos, letter), 0)
                if not bits:
                    break
        return bits

    def pick(self, bits: int) -> list[str]:
        """The words whose bits are set."""
        digits = bin(bits)[:1:-1]
        return [self.words[i] for i, d in enumerate(digits) if d == "1"]


class _Slot:
    """One word position of the puzzle, as seen by the search."""

    def __init__(self, word: Word, search: "_Search"):
        self.seq = word.seq
        self.direction = word.direction
        self.cells = list(word.cell_iterator())
        self.length = word.length
        self.label = _label(word)
        self.search = search
        self.original = word.get_text()

    def letters(self) -> list[str]:
        letters = self.search.letters
        return [letters[cell] for cell in self.cells]

    def text(self) -> str:
        return "".join(self.letters())

    def is_full(self) -> bool:
        return " " not in self.letters()

    def pattern(self) -> str:
        return "".join("." if c == " " else c for c in self.letters())


class _Search:
    """Backtracking search on a scratch copy of the puzzle's letters.

    Repeatedly picks the unfilled word with the fewest candidates, tries
    each candidate, and rejects it at once if any crossing word is left
    with no candidates. Starts over with a new random order whenever a
    try budget runs out, which rescues runs that got stuck early.
    """

    def __init__(self, puzzle, words, indexes, time_limit, rng):
        self.rng = rng
        self.deadline = time.monotonic() + time_limit
        self.time_limit = time_limit
        self.indexes = indexes
        self.letters = {}
        for word in words:
            for cell, letter in zip(word.cell_iterator(), word.get_text()):
                self.letters[cell] = letter
        self.slots = [_Slot(w, self) for w in words]
        self.slots_at: dict[tuple[int, int], list[int]] = {}
        for i, slot in enumerate(self.slots):
            for cell in slot.cells:
                self.slots_at.setdefault(cell, []).append(i)
        self.used = [s.text() for s in self.slots if s.is_full()]
        self.open = [i for i, s in enumerate(self.slots) if not s.is_full()]
        self.failures = [0] * len(self.slots)
        self.initial_count = {i: self._count(i) for i in self.open}
        self.proved_impossible = False
        self.tries = 0
        self.budget = 0
        self.trail = []

    def slot_without_candidates(self):
        """A slot that already has no candidates, or None."""
        for i in self.open:
            if self.initial_count[i] == 0:
                return self.slots[i]
        return None

    def run(self) -> bool:
        """Search until filled (True) or out of time / proven impossible (False)."""
        budget = FIRST_ATTEMPT_BUDGET
        try:
            while True:
                self.tries, self.budget = 0, budget
                try:
                    if self._solve():
                        return True
                    self.proved_impossible = True
                    return False
                except _Stop:
                    self._unwind()
                    self._check_time()
                    budget *= BUDGET_GROWTH
        except _TimeUp:
            return False

    def fills(self) -> dict[tuple[int, str], str]:
        """The words that differ from the puzzle as it was."""
        return {(s.seq, s.direction): s.text()
                for s in self.slots if s.text() != s.original}

    def failure_message(self) -> str:
        if self.proved_impossible:
            reason = "No fill is possible with this word list and the words already placed."
        else:
            reason = f"No fill found in {self.time_limit:g} seconds."
        worst = max(self.open, key=lambda i: self.failures[i], default=None)
        if worst is None or not self.failures[worst]:
            return reason
        slot = self.slots[worst]
        original = "".join("." if c == " " else c for c in slot.original)
        return (f"{reason} The hardest spot was {slot.label} "
                f"(pattern {original}, {self.initial_count[worst]} "
                f"candidate{'' if self.initial_count[worst] == 1 else 's'}).")

    # --- the search itself -------------------------------------------------

    def _solve(self) -> bool:
        if not self.open:
            return True
        chosen = min(self.open, key=lambda i: (self._count(i), self.slots[i].length))
        slot = self.slots[chosen]
        index = self.indexes[slot.length]
        candidates = index.pick(index.matching(slot.letters()))
        self.rng.shuffle(candidates)

        for word in candidates:
            self._tick()
            if self._place(chosen, word):
                if self._solve():
                    return True
                self._undo_placement()
        self.failures[chosen] += 1
        return False

    def _place(self, chosen: int, word: str) -> bool:
        """Put word in slot `chosen`, then check everything it touches.
        Returns False (having changed nothing) if that leaves a dead end."""
        slot = self.slots[chosen]
        if find_duplicate(word, self.used):
            return False

        changed_cells = [c for c, ch in zip(slot.cells, slot.letters()) if ch == " "]
        for cell, letter in zip(slot.cells, word):
            self.letters[cell] = letter
        used_before = len(self.used)
        open_before = list(self.open)
        self.used.append(word)
        self.open.remove(chosen)
        self.trail.append((changed_cells, used_before, open_before))

        touched = {j for cell in changed_cells for j in self.slots_at[cell]}
        touched.discard(chosen)
        for j in sorted(touched):
            if j not in self.open:
                continue
            if self._count(j) == 0:
                self.failures[j] += 1
                self._undo_placement()
                return False
            if self.slots[j].is_full():
                text = self.slots[j].text()
                if find_duplicate(text, self.used):
                    self.failures[j] += 1
                    self._undo_placement()
                    return False
                self.used.append(text)
                self.open.remove(j)
        return True

    def _undo_placement(self) -> None:
        changed_cells, used_before, open_before = self.trail.pop()
        for cell in changed_cells:
            self.letters[cell] = " "
        del self.used[used_before:]
        self.open = open_before

    def _unwind(self) -> None:
        """Take back every word placed so far."""
        while self.trail:
            self._undo_placement()

    def _count(self, i: int) -> int:
        slot = self.slots[i]
        return self.indexes[slot.length].matching(slot.letters()).bit_count()

    def _tick(self) -> None:
        self.tries += 1
        if self.tries > self.budget:
            raise _Stop
        if self.tries % 64 == 0:
            self._check_time()

    def _check_time(self) -> None:
        if time.monotonic() > self.deadline:
            raise _TimeUp


def _label(word: Word) -> str:
    return f"{word.seq}-{'Across' if word.direction == Word.ACROSS else 'Down'}"
