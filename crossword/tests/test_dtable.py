import os.path
import tempfile
from unittest import TestCase

from crossword.dtable import DTable


class TestDTable(TestCase):

    def test_create(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        dtable.create()

    def test_load(self):
        outfile = os.path.join(tempfile.gettempdir(), "dtable.bin")
        dtable = DTable(outfile=outfile)
        dtable.create()
        table = dtable.load()
