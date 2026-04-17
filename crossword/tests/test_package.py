import pytest

from datetime import datetime
from time import sleep

from crossword import get_elapsed_time


class TestPackage:

    def test_get_elapsed_time(self):
        stime = datetime.now()
        sleep(0.5)
        etime = datetime.now()
        expected = 0.5
        actual = get_elapsed_time(stime, etime)
        # 50 milliseconds difference is good enough
        assert actual == pytest.approx(expected, abs=0.05)
