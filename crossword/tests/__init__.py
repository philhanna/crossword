# Unit tests for crossword
__all__ = [
    'TestAcrossWord',
    'TestClues',
    'TestConfiguration',
    'TestDownWord',
    'TestGetNumberedCells',
    'TestGrid',
    'TestGridRotate',
    'TestNumberClues',
    'TestNumberedCell',
    'TestPuzzleGetNumberedCell',
    'TestPuzzleIsBlackCell',
    'TestPuzzlePublishNYTimes',
    'TestPuzzle',
    'TestPuzzleToSVG',
    'TestPuzzleUndo',
    'TestWordList',
    'TestWord',
]
from .test_puzzle import *
from .test_grid import *
from .test_configuration import *
from .test_word import *
from .test_get_numbered_cells import *

from .test_across_word import *
from .test_clues import *
from .test_down_word import *
from .test_grid_rotate import *
from .test_number_clues import *
from .test_numbered_cell import *
from .test_puzzle_get_numbered_cell import *
from .test_puzzle_is_black_cell import *
from .test_puzzle_publish_nytimes import *
from .test_puzzle_to_svg import *
from .test_puzzle_undo import *
from .test_wordlist import *
