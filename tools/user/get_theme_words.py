"""
Print the theme words of a puzzle, with their lengths and clues.

Theme words are the words that are locked in the puzzle. Each one is
printed on its own line as:

    WORD (length) clue

Across words come first, then down words, each in numerical order.

Usage:
    python3 tools/user/get_theme_words.py <puzzle name> [--user-id 1]
"""

import argparse
import sys

sys.path.insert(0, ".")
from crossword import init_config
from crossword.adapters import SQLitePersistenceAdapter
from crossword.ports.persistence_port import PersistenceError


def main() -> None:
    """Load the named puzzle and print its locked words."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("name", help="Name of the puzzle")
    parser.add_argument(
        "--user-id",
        type=int,
        default=1,
        help="ID of the user who owns the puzzle (default: 1)",
    )
    args = parser.parse_args()

    config = init_config()
    persistence = SQLitePersistenceAdapter(config["dbfile"])
    try:
        puzzle = persistence.load_puzzle(args.user_id, args.name)
    except PersistenceError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    for word in get_theme_words(puzzle):
        print(format_word(word))


def get_theme_words(puzzle) -> list:
    """Return the locked words, across words first, each in numerical order."""
    words = [puzzle.across_words[seq] for seq in sorted(puzzle.across_words)]
    words += [puzzle.down_words[seq] for seq in sorted(puzzle.down_words)]
    return [word for word in words if word.is_locked()]


def format_word(word) -> str:
    """Return 'WORD (length) clue', showing empty squares as '.'."""
    text = word.get_text().replace(" ", ".")
    clue = word.get_clue() or ""
    return f"{text} ({word.length}) {clue}".rstrip()


if __name__ == "__main__":
    main()
