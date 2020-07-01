import unittest

import crossword


class TestVersion(unittest.TestCase):

    def test_version(self):
        self.assertEqual("2.2.0", crossword.__version__)
