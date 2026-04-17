"""
Adapter that fetches word definitions from the free dictionaryapi.dev REST API.

API reference: https://dictionaryapi.dev/

The API returns a JSON array of entry objects for a given word.  Each entry
may contain multiple "meanings", each of which groups a list of definitions
under a part-of-speech label.  Because a single word can have several entries
(e.g. the noun form and the verb form returned separately), this adapter merges
all meanings across every entry and groups them by part of speech before
constructing the domain ``WordResult``.

Raises ``DefinitionNotFound`` when the API returns HTTP 404.  Any other
non-2xx response is re-raised via ``requests.Response.raise_for_status()``.
"""
import requests

from crossword.domain.definition import Definition, LexicalEntry, PartOfSpeech, WordResult
from crossword.ports.definition_port import DefinitionNotFound, DefinitionProviderPort

_BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

# Maps the API's part-of-speech strings to domain enum values.
# Unmapped strings (e.g. "conjunction", "interjection") fall back to OTHER.
_POS_MAP = {
    "noun": PartOfSpeech.NOUN,
    "verb": PartOfSpeech.VERB,
    "adjective": PartOfSpeech.ADJECTIVE,
    "adverb": PartOfSpeech.ADVERB,
}


class DictionaryAPIDefinition(DefinitionProviderPort):
    """``DefinitionProviderPort`` implementation backed by dictionaryapi.dev."""

    def lookup(self, word: str) -> WordResult:
        """Return definitions for *word* grouped by part of speech.

        Args:
            word: The word to look up.  Case is ignored; the lookup is always
                performed in lower case.

        Returns:
            A ``WordResult`` containing one ``LexicalEntry`` per part of speech
            found, each holding all ``Definition`` objects (text + optional
            example sentence) merged across every API entry for the word.

        Raises:
            DefinitionNotFound: The API returned HTTP 404 for this word.
            requests.HTTPError: The API returned any other non-2xx status.
        """
        url = _BASE_URL.format(word=word.lower())
        resp = requests.get(url)
        if resp.status_code == 404:
            raise DefinitionNotFound(word)
        resp.raise_for_status()
        data = resp.json()

        # Merge meanings across all entries, grouping by part of speech.
        merged: dict[PartOfSpeech, list[Definition]] = {}
        for entry in data:
            for meaning in entry.get("meanings", []):
                pos = _POS_MAP.get(meaning.get("partOfSpeech", ""), PartOfSpeech.OTHER)
                defs = merged.setdefault(pos, [])
                for d in meaning.get("definitions", []):
                    defs.append(Definition(
                        text=d.get("definition", ""),
                        example=d.get("example") or None,
                    ))

        entries = [LexicalEntry(part_of_speech=pos, definitions=defs)
                   for pos, defs in merged.items()]
        return WordResult(word=word.lower(), entries=entries)
