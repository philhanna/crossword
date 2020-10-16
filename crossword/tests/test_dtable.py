import os.path
import tempfile
from unittest import TestCase

from crossword.dtable import DTable


class q\
            (TestCase):

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

    def test_load(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        dtable.create()
        dtable.save()
        dtable.load()

    def test_lookup(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        if not os.path.exists(outfile):
            dtable.create()
        else:
            dtable.load()

        word_set = dtable.lookup("PR.")
        self.assertEqual(3, len(word_set))
        word_list = [dtable.words[windex] for windex in word_set]
        print(word_list)

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
