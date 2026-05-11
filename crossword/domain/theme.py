from dataclasses import dataclass, field


@dataclass
class Theme:
    """A crossword puzzle theme grouping a title, slot sizes, and word pools.

    A theme is *complete* when ``selected_words`` contains exactly one word per
    slot and each word's length matches the corresponding slot length.
    """

    id: int
    title: str
    word_lengths: list[int]
    selected_words: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return sorted(len(w) for w in self.selected_words) == sorted(self.word_lengths)


@dataclass
class GridPattern:
    """A crossword grid layout read from the external grids database."""

    name: str
    size: int
    grid_text: str
