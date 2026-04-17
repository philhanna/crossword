from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PartOfSpeech(Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    OTHER = "other"


@dataclass(frozen=True)
class Definition:
    text: str
    example: Optional[str] = None


@dataclass(frozen=True)
class LexicalEntry:
    """Groups definitions by part of speech."""
    part_of_speech: PartOfSpeech
    definitions: list[Definition] = field(default_factory=list)


@dataclass(frozen=True)
class WordResult:
    """Top-level result for a single word lookup."""
    word: str
    entries: list[LexicalEntry] = field(default_factory=list)
