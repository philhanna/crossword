#!/usr/bin/env python3
"""Look up the definition of a word using dictionaryapi.dev."""
import argparse
import sys

from crossword.adapters.dictionary_api_definition_adapter import DictionaryAPIDefinition
from crossword.ports.definition_port import DefinitionNotFound


def main():
    parser = argparse.ArgumentParser(description="Look up a word definition.")
    parser.add_argument("word", help="Word to look up")
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
