import os
import unittest
from datetime import datetime
from time import sleep

from crossword import get_elapsed_time, dbfile


class TestPackage(unittest.TestCase):

    def test_get_elapsed_time(self):
        stime = datetime.now()
        sleep(0.5)
        etime = datetime.now()
        expected = 0.5
        actual = get_elapsed_time(stime, etime)
        # 50 milliseconds difference is good enough
        self.assertAlmostEqual(expected, actual, delta=0.05)

    def test_dbfile(self):
        db = os.path.abspath(dbfile())
        errmsg = f"{db} file not found"
        self.assertTrue(os.path.exists(db), errmsg)
