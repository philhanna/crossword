#!/usr/bin/env python3
"""
Look up the definition of a word using the free dictionaryapi.dev API.

Usage:
    python tools/user/lookup.py <word>

Examples:
    python tools/user/lookup.py serendipity
    python tools/user/lookup.py run

Output format:
    Definitions are grouped by part of speech (noun, verb, adjective, etc.).
    Each definition is numbered and followed by an example sentence if one
    is available from the API.

Exit codes:
    0  Word was found and definitions were printed.
    1  Word was not found in the dictionary.
"""
import argparse
import sys

from crossword.adapters.dictionary_api_definition_adapter import DictionaryAPIDefinition
from crossword.ports.definition_port import DefinitionNotFound


def main():
    """Parse arguments, look up the word, and print its definitions."""
    parser = argparse.ArgumentParser(
        description="Look up the definition of a word.",
        epilog="Definitions are provided by the free dictionaryapi.dev service.",
    )
    parser.add_argument("word", help="The word to look up.")
    args = parser.parse_args()

    adapter = DictionaryAPIDefinition()
    try:
        result = adapter.lookup(args.word)
    except DefinitionNotFound:
        print(f"No definition found for '{args.word}'.", file=sys.stderr)
        sys.exit(1)

    print(result.word)
    for entry in result.entries:
        print(f"\n[{entry.part_of_speech.value}]")
        for i, defn in enumerate(entry.definitions, 1):
            print(f"  {i}. {defn.text}")
            if defn.example:
                print(f"     Example: {defn.example}")


if __name__ == "__main__":
    main()
