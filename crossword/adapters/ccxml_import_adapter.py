# crossword.adapters.ccxml_import_adapter
import html
import re
import xml.etree.ElementTree as ET

_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")

from crossword import Grid, Puzzle
from crossword.domain.word import Word
from crossword.ports.import_port import ImportPort, PuzzleImportError


class CcxmlImportAdapter(ImportPort):
    """
    Imports a puzzle from Crossword Compiler XML format.

    Reads the <rectangular-puzzle> document produced by Crossword Compiler
    (and the matching export adapter). Cells are 1-indexed with ``x`` as the
    column and ``y`` as the row. Black cells use ``type="block"``; letter
    cells carry a ``solution`` attribute. Clues live inside ``<clues>``
    blocks whose ``<title>`` identifies the direction (Across/Down); each
    ``<clue>`` references either a numbered cell (``number`` attribute) or
    a word id from a sibling ``<word>`` element.
    """

    def import_puzzle(self, content: str) -> tuple[str, str, Puzzle]:
        root = self._parse_xml(content)
        rect = self._find_rectangular_puzzle(root)

        title = self._text_of(self._find_local(rect, "metadata", "title")).strip()
        author = self._text_of(self._find_local(rect, "metadata", "creator")).strip()

        crossword = self._find_local(rect, "crossword")
        if crossword is None:
            raise PuzzleImportError("Missing <crossword> element")

        grid_elem = self._find_local(crossword, "grid")
        if grid_elem is None:
            raise PuzzleImportError("Missing <grid> element")

        n = self._grid_size(grid_elem)
        cells = self._collect_cells(grid_elem, n)
        black_cells = [(r, c) for (r, c), info in cells.items() if info["block"]]
        self._validate_symmetry(black_cells, n)

        grid = Grid(n)
        for r, c in black_cells:
            grid.add_black_cell(r, c)

        puzzle = Puzzle(grid, title=title or None)
        puzzle.enter_puzzle_mode()

        for (r, c), info in cells.items():
            if info["block"]:
                continue
            letter = info["letter"]
            if letter:
                puzzle.set_cell(r, c, letter)

        word_directions = self._map_word_directions(crossword)
        across_clues, down_clues = self._collect_clues(crossword, word_directions)

        for seq in sorted(puzzle.across_words):
            if seq in across_clues:
                puzzle.set_clue(seq, Word.ACROSS, across_clues[seq])
        for seq in sorted(puzzle.down_words):
            if seq in down_clues:
                puzzle.set_clue(seq, Word.DOWN, down_clues[seq])

        return title, author, puzzle

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_xml(self, content: str) -> ET.Element:
        try:
            return ET.fromstring(content)
        except ET.ParseError as e:
            raise PuzzleImportError(f"Not a valid XML file: {e}") from e

    def _find_rectangular_puzzle(self, root: ET.Element) -> ET.Element:
        if self._local_name(root.tag) == "rectangular-puzzle":
            return root
        rect = self._find_local(root, "rectangular-puzzle")
        if rect is None:
            raise PuzzleImportError(
                "Not a Crossword Compiler XML file: missing <rectangular-puzzle>"
            )
        return rect

    def _grid_size(self, grid_elem: ET.Element) -> int:
        width = grid_elem.get("width")
        height = grid_elem.get("height")
        if width is None or height is None:
            raise PuzzleImportError("<grid> missing width/height attributes")
        try:
            w, h = int(width), int(height)
        except ValueError as e:
            raise PuzzleImportError(f"Invalid grid dimensions: {e}") from e
        if w != h:
            raise PuzzleImportError(
                f"Only square grids are supported (got {w}x{h})"
            )
        return w

    def _collect_cells(self, grid_elem: ET.Element, n: int) -> dict:
        cells: dict[tuple[int, int], dict] = {}
        for cell in self._iter_local(grid_elem, "cell"):
            x = cell.get("x")
            y = cell.get("y")
            if x is None or y is None:
                continue
            try:
                c, r = int(x), int(y)
            except ValueError:
                continue
            if not (1 <= r <= n and 1 <= c <= n):
                raise PuzzleImportError(
                    f"Cell out of bounds: x={x}, y={y} (grid is {n}x{n})"
                )
            block = (cell.get("type") == "block")
            letter = ""
            if not block:
                sol = (cell.get("solution") or "").strip().upper()
                if len(sol) == 1 and sol.isalpha():
                    letter = sol
            cells[(r, c)] = {"block": block, "letter": letter}

        for r in range(1, n + 1):
            for c in range(1, n + 1):
                if (r, c) not in cells:
                    raise PuzzleImportError(
                        f"Grid missing <cell> at row {r}, column {c}"
                    )
        return cells

    def _validate_symmetry(self, black_cells: list, n: int) -> None:
        black_set = set(black_cells)
        for r, c in black_cells:
            mirror = (n + 1 - r, n + 1 - c)
            if mirror not in black_set:
                raise PuzzleImportError(
                    f"Grid lacks 180° rotational symmetry: black cell at row {r}, col {c}"
                    f" has no matching black cell at row {mirror[0]}, col {mirror[1]}"
                )

    def _map_word_directions(self, crossword: ET.Element) -> dict:
        """Map word id → (direction, seq-start-cell) using <word> elements.

        Returns {word_id: ("A"|"D"|None)}. Direction is derived from
        whether x or y has a range (``"3-5"``). Sequence number can't be
        derived from the <word> element alone, so the mapping carries only
        the direction; the <clue> element supplies the number.
        """
        mapping: dict[str, str] = {}
        for word in self._iter_local(crossword, "word"):
            wid = word.get("id")
            if not wid:
                continue
            x_attr = word.get("x", "")
            y_attr = word.get("y", "")
            if "-" in x_attr and "-" not in y_attr:
                mapping[wid] = Word.ACROSS
            elif "-" in y_attr and "-" not in x_attr:
                mapping[wid] = Word.DOWN
        return mapping

    def _collect_clues(self, crossword: ET.Element, word_directions: dict) -> tuple:
        across: dict[int, str] = {}
        down: dict[int, str] = {}
        for clues_elem in self._iter_local(crossword, "clues"):
            direction = self._clues_direction(clues_elem, word_directions)
            if direction is None:
                continue
            bucket = across if direction == Word.ACROSS else down
            for clue in self._iter_local(clues_elem, "clue"):
                seq = self._clue_number(clue)
                if seq is None:
                    continue
                text = html.unescape(self._text_of(clue))
                bucket[seq] = _TAG_RE.sub("", text).strip()
        return across, down

    def _clues_direction(self, clues_elem: ET.Element, word_directions: dict) -> str | None:
        """Determine whether a <clues> block holds Across or Down clues.

        Crossword Compiler stores the label inside <title>, often wrapped
        in <b>. Fall back to inspecting the first child <clue>'s referenced
        word id when the title text is missing or unrecognized.
        """
        title_elem = self._find_local(clues_elem, "title")
        label = self._text_of(title_elem).strip().lower() if title_elem is not None else ""
        if "across" in label:
            return Word.ACROSS
        if "down" in label:
            return Word.DOWN
        for clue in self._iter_local(clues_elem, "clue"):
            wid = clue.get("word")
            if wid and wid in word_directions:
                return word_directions[wid]
        return None

    def _clue_number(self, clue: ET.Element) -> int | None:
        num = clue.get("number")
        if num is None:
            return None
        try:
            return int(num)
        except ValueError:
            return None

    def _text_of(self, elem: ET.Element | None) -> str:
        if elem is None:
            return ""
        return "".join(elem.itertext())

    def _local_name(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def _find_local(self, parent: ET.Element, *names: str) -> ET.Element | None:
        current = parent
        for name in names:
            if current is None:
                return None
            current = next(self._iter_local(current, name), None)
        return current

    def _iter_local(self, parent: ET.Element, name: str):
        for child in parent:
            if self._local_name(child.tag) == name:
                yield child
