"""
Word use cases - Word suggestions, validation, and lookup.

Public interface:
  get_suggestions(pattern) -> list[str]
  get_all_words() -> list[str]
  validate_word(word) -> bool
  get_word_constraints(word) -> dict
"""

import re
from crossword import LetterList
from crossword.ports.word_list_port import WordListPort


class WordUseCases:
    """
    Orchestrates word operations via the word list port.

    Constructor injection: takes a WordListPort instance.
    """

    def __init__(self, word_list: WordListPort):
        self.word_list = word_list

    def get_suggestions(self, pattern: str) -> list[str]:
        """
        Get word suggestions matching a pattern.

        Pattern is a regex with ? for unknown letters and . for exact position.
        Example: "?HALE" or ".H.LE" (5-letter words with H in position 2, E in position 5).

        Args:
            pattern: Pattern string with wildcards or regex

        Returns:
            List of matching words (lowercase), or empty list if no matches

        Raises:
            ValueError: If pattern is not a valid regex
        """
        # Convert simple pattern (with ?) to regex if needed
        regex_pattern = self._pattern_to_regex(pattern)
        try:
            return self.word_list.get_matches(regex_pattern)
        except ValueError as e:
            raise ValueError(f"Invalid pattern: {e}")

    def get_all_words(self) -> list[str]:
        """
        Get all words in the dictionary.

        Returns:
            List of all words (lowercase)
        """
        return self.word_list.get_all_words()

    def validate_word(self, word: str) -> bool:
        """
        Check if a word is in the dictionary.

        Args:
            word: Word to validate (case-insensitive)

        Returns:
            True if word is in dictionary, False otherwise
        """
        if not isinstance(word, str) or not word:
            return False

        word_lower = word.lower()
        all_words = self.word_list.get_all_words()
        return word_lower in all_words

    def get_word_constraints(self, word) -> dict:
        """
        Compute letter constraints for a word based on its crossing words.

        For each position in the word, examines the crossing word and determines
        which letters are valid at that position by looking up all dictionary
        words matching the crossing word's current pattern.

        Args:
            word: A Word domain object (AcrossWord or DownWord)

        Returns:
            Dict with keys:
              - word: current text of the word (spaces shown as '.')
              - length: word length
              - crossers: list of per-position constraint dicts, each with:
                  pos, letter, crossing_text, crossing_location,
                  crossing_index, regexp, choices, letter_freq
              - pattern: concatenated regexps (usable as a suggestions pattern)
        """
        word_coords = list(word.cell_iterator())
        word_text = word.get_text()
        crossing_words = word.get_crossing_words()

        crossers = []
        for i, crossing_word in enumerate(crossing_words):
            crossing_text = crossing_word.get_text()
            # Build regex pattern from crossing word: spaces/blanks become '.'
            crossing_pattern = "^" + re.sub(r"[ ?]", ".", crossing_text) + "$"

            # Find where in the crossing word it intersects this word
            crossing_index = 1
            for j, (r, c) in enumerate(crossing_word.cell_iterator()):
                if (r, c) == word_coords[i]:
                    crossing_index = j + 1  # 1-indexed
                    break

            # Look up all words matching the crossing pattern
            matches = self.word_list.get_matches(crossing_pattern)
            letter_freq = {}
            for m in matches:
                letter = m[crossing_index - 1].upper()
                letter_freq[letter] = letter_freq.get(letter, 0) + 1
            letter_set = set(letter_freq.keys())
            nchoices = len(matches)

            regexp = LetterList.regexp(letter_set)
            if not regexp:
                # Crossing word not in dictionary — fall back to current letter
                regexp = word_text[i] if word_text[i] != " " else "."
                nchoices = 1

            crossers.append({
                "pos": i + 1,
                "letter": word_text[i],
                "crossing_text": crossing_text.replace(" ", "."),
                "crossing_location": crossing_word.location,
                "crossing_index": crossing_index,
                "regexp": regexp,
                "choices": nchoices,
                "letter_freq": letter_freq,
            })

        pattern = "".join(c["regexp"] for c in crossers)

        return {
            "word": word_text.replace(" ", "."),
            "length": word.length,
            "crossers": crossers,
            "pattern": pattern,
        }

    def get_ranked_suggestions(self, word) -> list[dict]:
        """
        Return word candidates for the given word, ranked by crossing viability score.

        For each candidate matching the word's constraint pattern, computes a score
        equal to the sum of crossing-word match counts for each letter in the candidate.
        Higher scores mean the candidate's letters are more common across the crossing
        words, leaving more options open for those words.

        Args:
            word: A Word domain object (AcrossWord or DownWord)

        Returns:
            List of dicts sorted by score descending:
              [{"word": "crane", "score": 142}, ...]
        """
        constraints = self.get_word_constraints(word)
        pattern = constraints["pattern"]
        crossers = constraints["crossers"]

        candidates = self.word_list.get_matches(self._pattern_to_regex(pattern))

        def score(candidate):
            total = 0
            for i, crosser in enumerate(crossers):
                if i < len(candidate):
                    letter = candidate[i].upper()
                    total += crosser["letter_freq"].get(letter, 0)
            return total

        return sorted(
            [{"word": c, "score": score(c)} for c in candidates],
            key=lambda x: x["score"],
            reverse=True,
        )

    # Helper methods

    def _pattern_to_regex(self, pattern: str) -> str:
        """
        Convert a simple pattern with ? wildcards to a regex pattern.

        Example: "?HALE" -> "^.HALE$" (case-insensitive)
        If pattern already looks like regex, return as-is.

        Args:
            pattern: Pattern with ? for unknown or a regex

        Returns:
            Regex pattern string
        """
        # If already contains regex syntax, add anchors if missing
        if any(c in pattern for c in "[]()*+^$|"):
            p = pattern
            if not p.startswith("^"):
                p = "^" + p
            if not p.endswith("$"):
                p = p + "$"
            return p

        # Convert ? to . (any character) and ^ . $ anchors
        escaped = pattern.replace("?", ".")
        return f"^{escaped}$"
