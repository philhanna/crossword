// Crossword Puzzle Editor — temporary bridge for inline event handlers
//
// The onclick="..." (and oninput, onchange, onblur) attributes in index.html
// and in HTML built by the modules can only call functions on `window`. This
// file puts the ones they use there. It is a to-do list: each function comes
// off as its handlers move to data-action, and the file goes when it's empty.

import {
    chPageFirst, chPageLast, chPageNext, chPagePrev, chSetPuzzleStateFilter,
    chSetSort, clearMessageLine, hideElement, showView,
} from './ui.js';
import {
    _weOnClueBlur, closeWordEditor, doWordConstraints, doWordDefinitions,
    doWordEditOK, doWordSuggestFetch, do_puzzle_edit_word, weHandleClueInput,
    weHandleLockToggle, weHandleTextInput, wePageNext, wePagePrev,
} from './word-editor.js';
import { _dashCloseStateDialog } from './dashboard.js';
import {
    _openWordFromFillOrder, _openWordFromStats, do_export, do_puzzle_clear,
    do_puzzle_close, do_puzzle_delete, do_puzzle_delete_current,
    do_puzzle_fill_order, do_puzzle_generate_grid, do_puzzle_import,
    do_puzzle_import_ccxml, do_puzzle_import_ipuz, do_puzzle_import_puz,
    do_puzzle_import_xd, do_puzzle_new, do_puzzle_open, do_puzzle_redo,
    do_puzzle_rename, do_puzzle_rotate_grid, do_puzzle_save, do_puzzle_save_as,
    do_puzzle_stats, do_puzzle_title, do_puzzle_undo, do_switch_to_grid_mode,
    do_switch_to_puzzle_mode, setStatsSubTab, startInlineClueEdit,
    switchClueDirection, switchSidebarTab,
} from './puzzle-editor.js';
import { do_settings, do_settings_cancel, do_settings_save } from './settings.js';

Object.assign(window, {
    // ui.js
    chPageFirst, chPageLast, chPageNext, chPagePrev, chSetPuzzleStateFilter,
    chSetSort, clearMessageLine, hideElement, showView,

    // word-editor.js
    _weOnClueBlur, closeWordEditor, doWordConstraints, doWordDefinitions,
    doWordEditOK, doWordSuggestFetch, do_puzzle_edit_word, weHandleClueInput,
    weHandleLockToggle, weHandleTextInput, wePageNext, wePagePrev,

    // dashboard.js
    _dashCloseStateDialog,

    // puzzle-editor.js
    _openWordFromFillOrder, _openWordFromStats, do_export, do_puzzle_clear,
    do_puzzle_close, do_puzzle_delete, do_puzzle_delete_current,
    do_puzzle_fill_order, do_puzzle_generate_grid, do_puzzle_import,
    do_puzzle_import_ccxml, do_puzzle_import_ipuz, do_puzzle_import_puz,
    do_puzzle_import_xd, do_puzzle_new, do_puzzle_open, do_puzzle_redo,
    do_puzzle_rename, do_puzzle_rotate_grid, do_puzzle_save, do_puzzle_save_as,
    do_puzzle_stats, do_puzzle_title, do_puzzle_undo, do_switch_to_grid_mode,
    do_switch_to_puzzle_mode, setStatsSubTab, startInlineClueEdit,
    switchClueDirection, switchSidebarTab,

    // settings.js
    do_settings, do_settings_cancel, do_settings_save,
});
