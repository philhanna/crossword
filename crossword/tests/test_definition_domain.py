import pytest

from crossword.domain.definition import Definition, LexicalEntry, PartOfSpeech, WordResult
from crossword.ports.definition_port import DefinitionNotFound, DefinitionProviderPort


class TestDefinition:
    def test_text_required(self):
        d = Definition(text="A silvery-white metal.")
        assert d.text == "A silvery-white metal."
        assert d.example is None

    def test_with_example(self):
        d = Definition(text="A silvery-white metal.", example="Iron is magnetic.")
        assert d.example == "Iron is magnetic."

    def test_frozen(self):
        d = Definition(text="x")
        with pytest.raises(Exception):
            d.text = "y"


class TestLexicalEntry:
    def test_groups_by_part_of_speech(self):
        entry = LexicalEntry(
            part_of_speech=PartOfSpeech.NOUN,
            definitions=[Definition("A metal."), Definition("A clothes iron.")],
        )
        assert entry.part_of_speech == PartOfSpeech.NOUN
        assert len(entry.definitions) == 2

    def test_empty_definitions_by_default(self):
        entry = LexicalEntry(part_of_speech=PartOfSpeech.VERB)
        assert entry.definitions == []


class TestWordResult:
    def test_structure(self):
        result = WordResult(
            word="iron",
            entries=[
                LexicalEntry(
                    part_of_speech=PartOfSpeech.NOUN,
                    definitions=[Definition("A silvery-white magnetic metal.")],
                ),
                LexicalEntry(
                    part_of_speech=PartOfSpeech.VERB,
                    definitions=[Definition("To smooth with a heated iron.")],
                ),
            ],
        )
        assert result.word == "iron"
        assert len(result.entries) == 2
        assert result.entries[0].part_of_speech == PartOfSpeech.NOUN
        assert result.entries[1].part_of_speech == PartOfSpeech.VERB

    def test_empty_entries_by_default(self):
        result = WordResult(word="unknown")
        assert result.entries == []

    def test_frozen(self):
        result = WordResult(word="test")
        with pytest.raises(Exception):
            result.word = "other"


class TestDefinitionProviderPort:
    def test_port_is_abstract(self):
        with pytest.raises(TypeError):
            DefinitionProviderPort()

    def test_concrete_adapter_must_implement_lookup(self):
        class BrokenAdapter(DefinitionProviderPort):
            pass

        with pytest.raises(TypeError):
            BrokenAdapter()

    def test_concrete_adapter_lookup(self):
        class StubAdapter(DefinitionProviderPort):
            def lookup(self, word: str) -> WordResult:
                if word.lower() == "iron":
                    return WordResult(
                        word="iron",
                        entries=[
                            LexicalEntry(
                                part_of_speech=PartOfSpeech.NOUN,
                                definitions=[Definition("A metal.")],
                            )
                        ],
                    )
                raise DefinitionNotFound(word)

        adapter = StubAdapter()
        result = adapter.lookup("iron")
        assert result.word == "iron"
        assert result.entries[0].part_of_speech == PartOfSpeech.NOUN

        with pytest.raises(DefinitionNotFound):
            adapter.lookup("xyzzy")
