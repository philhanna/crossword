"""
Adapter that fetches word definitions from the Wikimedia REST API's
"definition" endpoint, which serves parsed Wiktionary content.

API reference: https://en.wiktionary.org/api/rest_v1/#/Page%20content/get_page_definition__title_

The API returns a JSON object keyed by language code (e.g. "en" for
English). Each value is a list of entry objects, one per part of speech,
each holding a list of definitions. Definition and example text is HTML
fragments (Wiktionary markup rendered to HTML), so this adapter strips
tags and unescapes entities before constructing the domain ``WordResult``.

Only the "en" (English) language section is used, since the rest of the
application operates on English-language puzzles.

Raises ``DefinitionNotFound`` when the API returns HTTP 404, or when the
word has no "en" section. Any other non-2xx response is re-raised via
``requests.Response.raise_for_status()``.
"""
import html
import re

import requests

from crossword.domain.definition import Definition, LexicalEntry, PartOfSpeech, WordResult
from crossword.ports.definition_port import DefinitionNotFound, DefinitionProviderPort

_BASE_URL = "https://en.wiktionary.org/api/rest_v1/page/definition/{word}"

# Wikimedia's API etiquette policy rejects requests with no (or a generic)
# User-Agent header, so a descriptive one is required.
_HEADERS = {"User-Agent": "crossword/1.0 (https://github.com/philhanna/crossword)"}

# Maps the API's part-of-speech strings to domain enum values.
# Unmapped strings (e.g. "Symbol", "Conjunction") fall back to OTHER.
_POS_MAP = {
    "noun": PartOfSpeech.NOUN,
    "verb": PartOfSpeech.VERB,
    "adjective": PartOfSpeech.ADJECTIVE,
    "adverb": PartOfSpeech.ADVERB,
}

_TAG_RE = re.compile(r"<[^>]+>")


class WiktionaryAPIDefinition(DefinitionProviderPort):
    """``DefinitionProviderPort`` implementation backed by Wiktionary's REST API."""

    def lookup(self, word: str) -> WordResult:
        """Return definitions for *word* grouped by part of speech.

        Args:
            word: The word to look up. Case is ignored; the lookup is always
                performed in lower case.

        Returns:
            A ``WordResult`` containing one ``LexicalEntry`` per part of speech
            found in the "en" section, each holding all ``Definition`` objects
            (text + optional example sentence), with HTML markup stripped.

        Raises:
            DefinitionNotFound: The API returned HTTP 404 for this word, or
                the word has no English-language section.
            requests.HTTPError: The API returned any other non-2xx status.
        """
        url = _BASE_URL.format(word=word.lower())
        resp = requests.get(url, headers=_HEADERS)
        if resp.status_code == 404:
            raise DefinitionNotFound(word)
        resp.raise_for_status()
        data = resp.json()

        en_entries = data.get("en", [])
        if not en_entries:
            raise DefinitionNotFound(word)

        entries = []
        for entry in en_entries:
            pos = _POS_MAP.get(entry.get("partOfSpeech", "").lower(), PartOfSpeech.OTHER)
            defs = []
            for d in entry.get("definitions", []):
                text = _strip_html(d.get("definition", ""))
                if not text:
                    continue
                examples = d.get("examples") or []
                example = _strip_html(examples[0]) if examples else None
                defs.append(Definition(text=text, example=example or None))
            if defs:
                entries.append(LexicalEntry(part_of_speech=pos, definitions=defs))

        if not entries:
            raise DefinitionNotFound(word)

        return WordResult(word=word.lower(), entries=entries)


def _strip_html(fragment: str) -> str:
    """Strip HTML tags from *fragment* and unescape entities, collapsing whitespace."""
    text = _TAG_RE.sub("", fragment)
    text = html.unescape(text)
    return " ".join(text.split())
