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
            print(f"DEBUG: {i}, {k}, {len(words)}, {','.join(words)}")

    def test_load(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        dtable.create()
        dtable.save()
        dtable.load()

    def test_lookup(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        dtable.load()
        set1 = dtable.lookup("P..")
        set2 = dtable.lookup(".R.")
        set3 = set1.intersection(set2)
        self.assertEqual(3, len(set3))

    def test_keymaker(self):
        pattern = "D.SH"
        actual = DTable.keymaker(pattern)
        expected = [
            'D...', '..S.', '...H'
        ]
        self.assertListEqual(expected, actual)
