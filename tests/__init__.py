# Unit tests for crossword
import pickle
from pathlib import Path

project_root = Path(__file__).parent.parent
testdata = project_root.joinpath("testdata")


def load_test_puzzle(filename):
    fullpath = Path(testdata).joinpath(filename)
    with open(fullpath, "rb") as fp:
        puzzle = pickle.load(fp)
    return puzzle


def load_test_grid(filename):
    fullpath = Path(testdata).joinpath(filename)
    with open(fullpath, "rb") as fp:
        grid = pickle.load(fp)
    return grid


__all__ = [
    'project_root',
    'testdata',
    'load_test_puzzle',
    'load_test_grid',
    'TestGrid',
    'TestPuzzle',
    'TestWord',
    'MockUser',
]

from tests.puzzles.test_puzzle import *
from tests.grids.test_grid import *
from tests.words.test_word import *
from tests.puzzles.mock_user import *
