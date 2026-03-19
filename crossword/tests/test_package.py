import pytest

import os
from datetime import datetime
from time import sleep

from crossword import get_elapsed_time, dbfile


class TestPackage:

    def test_get_elapsed_time(self):
        stime = datetime.now()
        sleep(0.5)
        etime = datetime.now()
        expected = 0.5
        actual = get_elapsed_time(stime, etime)
        # 50 milliseconds difference is good enough
        assert actual == pytest.approx(expected, abs=0.05)

    def test_dbfile(self):
        db = os.path.abspath(dbfile())
        errmsg = f"{db} file not found"
        assert os.path.exists(db)
