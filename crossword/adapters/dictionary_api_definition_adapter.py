import json
import urllib.error
import urllib.parse
import urllib.request

from crossword.domain.definition import Definition, LexicalEntry, PartOfSpeech, WordResult
from crossword.ports.definition_port import DefinitionNotFound, DefinitionProviderPort

_BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

_POS_MAP = {
    "noun": PartOfSpeech.NOUN,
    "verb": PartOfSpeech.VERB,
    "adjective": PartOfSpeech.ADJECTIVE,
    "adverb": PartOfSpeech.ADVERB,
}


class DictionaryAPIDefinition(DefinitionProviderPort):

    def lookup(self, word: str) -> WordResult:
        url = _BASE_URL.format(word=urllib.parse.quote(word.lower()))
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise DefinitionNotFound(word)
            raise

        # Merge meanings across all entries, grouping by part of speech
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
