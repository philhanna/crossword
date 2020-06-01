from unittest import TestCase
import os
from wordlist import WordList


class TestWordList(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filename = "words"
        if not os.path.exists(filename):
            filename = "../words"
            if not os.path.exists(filename):
                raise RuntimeError("No words or ../words file found")
        self.wordlist = WordList(filename)

    def test_wildcards(self):
        expected = ['DASH', 'DISH', 'DOTH']
        actual = self.wordlist.lookup("d..h")
        self.assertEqual(expected, actual)

    def test_two_letter(self):
        expected = ['IF', 'IT', 'BE']
        actual = self.wordlist.lookup("..")
        f = list(filter(lambda x : x in actual, expected))
        self.assertEqual(len(f), len(expected))

    def test_wildfirst(self):
        expected = ['ATS', 'ITS']
        actual = self.wordlist.lookup(".ts")
        self.assertEqual(expected, actual)

    def test_wildfirst_space(self):
        expected = ['ATS', 'ITS']
        actual = self.wordlist.lookup(" ts")
        self.assertEqual(expected, actual)

    def test_wildfirst_qmark(self):
        expected = ['ATS', 'ITS']
        actual = self.wordlist.lookup("?ts")
        self.assertEqual(expected, actual)
