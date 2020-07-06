# Web application for crossword package
__all__ = [
    'grid_changed',
    'grid_screen',
    'grid_new',
    'grid_open',
    'grid_preview',
    'grid_save',
    'grid_save_as',
    'grid_save_common',
    'grid_delete',
    'grid_changed',
    'grid_click',
    'grid_rotate',
    'grid_statistics',
    'grids',
    'main_screen',
    'puzzle_publish_acrosslite',
    'puzzle_publish_nytimes',
    'puzzle_screen',
    'puzzle_new',
    'puzzle_open',
    'puzzle_preview',
    'puzzle_save',
    'puzzle_save_as',
    'puzzle_save_common',
    'puzzle_delete',
    'puzzle_undo',
    'puzzle_redo',
    'puzzle_click_across',
    'puzzle_click_down',
    'puzzle_click',
    'puzzle_changed',
    'puzzle_statistics',
    'puzzle_title',
    'puzzles',
    'wordlists',
    'word_edit',
    'word_reset',
    'get_filelist',
]


def get_filelist(rootdir):
    """ Returns the list of JSON files in the specified directory.

    :param rootdir the root directory
    :returns the list of base file names, sorted with most recently updated first
    """
    filelist = []
    for filename in os.listdir(rootdir):
        if filename.endswith(".json"):
            fullpath = os.path.join(rootdir, filename)
            filetime = os.path.getmtime(fullpath)
            basename = os.path.splitext(filename)[0]
            filelist.append(f"{filetime}|{basename}")
    filelist.sort(reverse=True)
    filelist = [filename.split('|', 2)[1] for filename in filelist]
    return filelist

from .uigrid import *
from .uimain import *
from .uipublish import *
from .uipuzzle import *
from .uiwordlists import *
from .uiword import *
