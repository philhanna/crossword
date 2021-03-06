from enum import Enum


class UIState(Enum):
    """ Application state, which controls which menu items are enabled """
    MAIN_MENU = 1
    PUZZLE_CHOOSER = 2
    GRID_CHOOSER = 3
    PROMPT_FOR_GRID_SIZE = 4
    EDITING_GRID = 5
    EDITING_PUZZLE = 6
    EDITING_WORD = 7

    def get_enabled(self):
        enabled = {
            "grid_new": self in [UIState.MAIN_MENU],
            "grid_open": self in [UIState.MAIN_MENU],
            "grid_save": self in [UIState.EDITING_GRID],
            "grid_save_as": self in [UIState.EDITING_GRID],
            "grid_close": self in [UIState.EDITING_GRID],
            "grid_stats": self in [UIState.EDITING_GRID],
            "grid_rotate": self in [UIState.EDITING_GRID],
            "grid_undo": self in [UIState.EDITING_GRID],
            "grid_redo": self in [UIState.EDITING_GRID],
            "grid_delete": self in [UIState.EDITING_GRID],
            "puzzle_new": self in [UIState.MAIN_MENU],
            "puzzle_open": self in [UIState.MAIN_MENU],
            "puzzle_save": self in [UIState.EDITING_PUZZLE],
            "puzzle_save_as": self in [UIState.EDITING_PUZZLE],
            "puzzle_stats": self in [UIState.EDITING_PUZZLE],
            "puzzle_title": self in [UIState.EDITING_PUZZLE],
            "puzzle_undo": self in [UIState.EDITING_PUZZLE],
            "puzzle_redo": self in [UIState.EDITING_PUZZLE],
            "puzzle_close": self in [UIState.EDITING_PUZZLE],
            "puzzle_delete": self in [UIState.EDITING_PUZZLE],
        }
        return enabled
