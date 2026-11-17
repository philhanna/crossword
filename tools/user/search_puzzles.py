"""
Search every puzzle in the database for words or clues matching a regular
expression.

The pattern is a Python regular expression, searched for anywhere in the
text (use ^ and $ to anchor), and is case-insensitive. By default both the answer text and the
clue of every word are searched; use --words or --clues to restrict it.
Empty squares in an unfilled word are treated as spaces, so they never
match a letter.

Each match is printed as:

    <puzzle name>  <number><A|D>  WORD  clue

Usage:
    python3 tools/user/search_puzzles.py <regex> [--words | --clues] [--user-id 1]
"""

import argparse
import re
import sys

sys.path.insert(0, ".")
from crossword import init_config
from crossword.adapters import SQLitePersistenceAdapter
from crossword.ports.persistence_port import PersistenceError

TEMP_PREFIXES = ("__wc__", "__new__")


def main() -> None:
    """Parse arguments, search all puzzles, and print the matches."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pattern", help="Regular expression to look for (case-insensitive)")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--words", action="store_true", help="Search only word text")
    scope.add_argument("--clues", action="store_true", help="Search only clues")
    parser.add_argument(
        "--user-id",
        type=int,
        default=1,
        help="ID of the user who owns the puzzles (default: 1)",
    )
    args = parser.parse_args()

    try:
        regex = re.compile(args.pattern, re.IGNORECASE)
    except re.error as e:
        parser.error(f"invalid regular expression: {e}")

    config = init_config()
    persistence = SQLitePersistenceAdapter(config["dbfile"])
    search_words = not args.clues
    search_clues = not args.words

    count = 0
    try:
        for name in sorted(persistence.list_puzzles(args.user_id), key=str.lower):
            if name.startswith(TEMP_PREFIXES):
                continue
            puzzle = persistence.load_puzzle(args.user_id, name)
            for word in all_words(puzzle):
                if matches(word, regex, search_words, search_clues):
                    print(format_match(name, word))
                    count += 1
    except PersistenceError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    if count == 0:
        print(f"No words or clues match /{args.pattern}/.", file=sys.stderr)
        sys.exit(1)


def all_words(puzzle) -> list:
    """Return the across words, then the down words, each in numerical order."""
    words = [puzzle.across_words[seq] for seq in sorted(puzzle.across_words)]
    words += [puzzle.down_words[seq] for seq in sorted(puzzle.down_words)]
    return words


def matches(word, regex: re.Pattern, search_words: bool, search_clues: bool) -> bool:
    """Return True if the regex matches the word's text or clue."""
    if search_words and regex.search(word.get_text()):
        return True
    return search_clues and bool(regex.search(word.get_clue() or ""))


def format_match(name: str, word) -> str:
    """Return 'name  <number><A|D>  WORD  clue'."""
    answer = word.get_text().replace(" ", ".")
    clue = word.get_clue() or ""
    return f"{name}  {word.seq}{word.direction}  {answer}  {clue}".rstrip()


if __name__ == "__main__":
    main()
