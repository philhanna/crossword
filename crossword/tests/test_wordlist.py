from unittest import TestCase

from crossword import Configuration, WordList


class TestWordList(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filename = Configuration.get_words_filename()
        self.wordlist = WordList(filename)

    def test_wildcards(self):
        expected = ['DASH', 'DINH', 'DISH', 'DOTH']
        actual = self.wordlist.lookup("d..h")
        self.assertEqual(expected, actual)

    def test_wildfirst(self):
        expected = ['ATS', 'ITS', 'QTS', 'STS']
        actual = self.wordlist.lookup(".ts")
        self.assertEqual(expected, actual)

    def test_wildfirst_space(self):
        expected = ['ATS', 'ITS', 'QTS', 'STS']
        actual = self.wordlist.lookup(" ts")
        self.assertEqual(expected, actual)

    def test_wildfirst_qmark(self):
        expected = ['ATS', 'ITS', 'QTS', 'STS']
        actual = self.wordlist.lookup("?ts")
        self.assertEqual(expected, actual)
