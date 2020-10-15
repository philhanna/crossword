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
