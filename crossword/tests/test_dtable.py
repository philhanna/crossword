import os.path
import tempfile
from unittest import TestCase, skip

from crossword.dtable import DTable


class TestDTable(TestCase):

    def setUp(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        self.dtable = DTable(outfile=outfile)

    @skip("Print first 100 entries in tale")
    def test_create(self):
        dtable = self.dtable
        for i, k in enumerate(dtable.table.keys()):
            if i > 100:
                break
            v = dtable.table[k]
            words = [dtable.words[windex] for windex in v]
            print(f"DEBUG: {i}, {k}, {len(k)}, {len(words)}, {','.join(words)}")

    def test_lookup(self):
        dtable = self.dtable

        word_list = dtable.lookup("D.SH")
        self.assertEqual(3, len(word_list))
        self.assertIn("DISH", word_list)
        self.assertIn("DASH", word_list)
        self.assertIn("DOSH", word_list)
        self.assertNotIn("Puppies", word_list)

    def test_cached_lookup(self):
        dtable = self.dtable

        word_list = dtable.lookup("PR.")
        self.assertEqual(3, len(word_list))
        self.assertIn("PRE", word_list)
        self.assertIn("PRY", word_list)
        self.assertIn("PRO", word_list)

        # Now see if the pattern was cached
        self.assertIn("PR.", dtable.table.keys())

    def test_find_candidates(self):
        dtable = self.dtable

        pattern = "...C."
        word_list = dtable.lookup(pattern)
        self.assertGreater(len(word_list), 200)
        #print(word_list)
