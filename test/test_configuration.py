import os.path
from unittest import TestCase

from configuration import Configuration


class TestConfiguration(TestCase):

    def test_grids_root(self):
        grids_root = Configuration.get_grids_root()
        self.assertIsNotNone(grids_root)
        self.assertTrue(os.path.exists(grids_root))
        self.assertTrue(os.path.isdir(grids_root))

    def test_puzzles_root(self):
        puzzles_root = Configuration.get_puzzles_root()
        self.assertIsNotNone(puzzles_root)
        self.assertTrue(os.path.exists(puzzles_root))
        self.assertTrue(os.path.isdir(puzzles_root))

    def test_wordlists_root(self):
        wordlists_root = Configuration.get_wordlists_root()
        self.assertIsNotNone(wordlists_root)
        self.assertTrue(os.path.exists(wordlists_root))
        self.assertTrue(os.path.isdir(wordlists_root))

    def test_words(self):
        words_filename = Configuration.get_words_filename()
        self.assertIsNotNone(words_filename)
        self.assertTrue(os.path.exists(words_filename))
        self.assertTrue(os.path.isfile(words_filename))

    def test_get_author_name(self):
        self.assertIsNotNone(Configuration.get_author_name())

    def test_get_author_address(self):
        self.assertIsNotNone(Configuration.get_author_address())

    def test_get_author_city_state_zip(self):
        self.assertIsNotNone(Configuration.get_author_city_state_zip())

    def test_get_author_email(self):
        self.assertIsNotNone(Configuration.get_author_email())

