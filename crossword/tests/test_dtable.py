import os.path
import tempfile
from unittest import TestCase

from crossword.dtable import DTable


class TestDTable(TestCase):

    def no_test_create(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        dtable.create()
        for i, k in enumerate(dtable.table.keys()):
            if i > 100:
                break
            v = dtable.table[k]
            words = [dtable.words[windex] for windex in v]
            print(f"DEBUG: {i}, {k}, {len(k)}, {len(words)}, {','.join(words)}")

    def test_lookup(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        if not os.path.exists(outfile):
            dtable.create()
            dtable.save()
        else:
            dtable.load()

        word_list = dtable.lookup("D.SH")
        self.assertEqual(3, len(word_list))
        self.assertIn("DISH", word_list)
        self.assertIn("DASH", word_list)
        self.assertIn("DOSH", word_list)
        self.assertNotIn("Puppies", word_list)

    def test_cached_lookup(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        if not os.path.exists(outfile):
            dtable.create()
            dtable.save()
        else:
            dtable.load()

        word_list = dtable.lookup("PR.")
        self.assertEqual(3, len(word_list))
        self.assertIn("PRE", word_list)
        self.assertIn("PRY", word_list)
        self.assertIn("PRO", word_list)

        # Now see if the pattern was cached
        self.assertIn("PR.", dtable.table.keys())

    def test_keymaker(self):
        pattern = "D.SH"
        actual = DTable.keymaker(pattern)
        expected = [
            'D...', '..S.', '...H'
        ]
        self.assertListEqual(expected, actual)

    def test_keymaker_with_all_blanks(self):
        pattern = "......"
        actual = DTable.keymaker(pattern)
        self.assertIsNone(actual)
