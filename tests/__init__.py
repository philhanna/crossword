# Unit tests for crossword
import pickle
from pathlib import Path

project_root = Path(__file__).parent.parent
testdata = project_root.joinpath("testdata")


def load_pickled_puzzle(filename):
    fullpath = Path(testdata).joinpath(filename)
    with open(fullpath, "rb") as fp:
        puzzle = pickle.load(fp)
    return puzzle


__all__ = [
    'project_root',
    'testdata',
    'load_pickled_puzzle',
    'TestGrid',
    'TestPuzzle',
    'TestWord',
    'MockUser',
]

from tests.puzzles.test_puzzle import *
from tests.grids.test_grid import *
from tests.words.test_word import *
from tests.puzzles.mock_user import *
