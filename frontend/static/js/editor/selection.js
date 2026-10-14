// Crossword Puzzle Editor — the selected word
//
// AppState.selectedWord is the word the user is working on, with its saved
// text, clue and lock state alongside the draft being typed. These functions
// create it, keep it in step with the puzzle, and save the draft to the
// server when the user moves on.

import { apiFetch } from '../core/api.js';
import { AppState } from '../core/state.js';
import { showMessageLine, showRequestError } from '../ui/message-line.js';
import {
    _closeSidePanels, _updatePuzzleToolbar, _updatePuzzleUndoRedo,
    renderPuzzleEditorLhs, renderPuzzleEditorRhs,
} from './editor.js';
import { _syncSelectedWordFromInputs } from './word-editor.js';

export function _getPuzzleWord(seq, direction) {
    const pd = AppState.puzzleData;
    if (!pd || !pd.puzzle || !pd.puzzle.words) return null;
    return pd.puzzle.words.find(w => w.seq === seq && w.direction === direction) || null;
}

export function findWordAtCell(r, c, direction) {
    for (const word of AppState.puzzleData.puzzle.words) {
        if (word.direction !== direction) continue;
        for (const [wr, wc] of word.cells) {
            if (wr === r && wc === c) return word;
        }
    }
    return null;
}

export function _isWordEditorOpen() {
    return !!(AppState.selectedWord && AppState.selectedWord.editorMode === 'word');
}

// ---------------------------------------------------------------------------
// Creating and refreshing the selection
// ---------------------------------------------------------------------------

export function selectWord(seq, direction, clickR, clickC, editorMode = 'puzzle') {
    const word = _getPuzzleWord(seq, direction);
    if (!word) return;
    AppState.selectedWord = _hydrateSelectedWord(word, { clickR, clickC, editorMode });
    _closeSidePanels();
    AppState.sidebarTab = editorMode === 'word' ? 'word' : 'clues';
    _updatePuzzleToolbar();
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

function _hydrateSelectedWord(word, options = {}) {
    if (!word) return null;
    const len = word.cells.length;
    const text = _normalizeWordText(word.answer || '', len);
    return {
        seq: word.seq,
        direction: word.direction,
        cells: word.cells,
        originalText: text,
        draftText: options.draftText !== undefined ? _normalizeWordText(options.draftText, len) : text,
        originalClue: word.clue || '',
        draftClue: options.draftClue !== undefined ? options.draftClue : (word.clue || ''),
        originalLocked: !!word.locked,
        draftLocked: options.draftLocked !== undefined ? options.draftLocked : !!word.locked,
        cursorIdx: _getDefaultCursorIdx(word, text, options.clickR, options.clickC),
        editorMode: options.editorMode || 'puzzle',
    };
}

export function _normalizeWordText(text, len) {
    return (text || '').toUpperCase().replace(/\./g, ' ').padEnd(len).slice(0, len);
}

function _getDefaultCursorIdx(word, text, clickR, clickC) {
    if (clickR !== undefined && clickC !== undefined) {
        const clickedIdx = word.cells.findIndex(([r, c]) => r === clickR && c === clickC);
        if (clickedIdx >= 0) return clickedIdx;
    }
    const firstBlank = text.indexOf(' ');
    return firstBlank >= 0 ? firstBlank : 0;
}

export function _refreshSelectedWordFromPuzzleData(options = {}) {
    const current = AppState.selectedWord;
    if (!current) return null;
    const word = _getPuzzleWord(current.seq, current.direction);
    if (!word) {
        AppState.selectedWord = null;
        return null;
    }
    const next = _hydrateSelectedWord(word, {
        clickR: options.clickR,
        clickC: options.clickC,
        editorMode: options.editorMode !== undefined ? options.editorMode : current.editorMode,
    });
    next.cursorIdx = options.cursorIdx !== undefined
        ? Math.max(0, Math.min(options.cursorIdx, next.cells.length - 1))
        : Math.max(0, Math.min(current.cursorIdx || 0, next.cells.length - 1));
    AppState.selectedWord = next;
    return next;
}

// ---------------------------------------------------------------------------
// Cursor
// ---------------------------------------------------------------------------

export function _getSelectedWordCursorIdx() {
    return AppState.selectedWord ? AppState.selectedWord.cursorIdx || 0 : 0;
}

export function _setSelectedWordCursorIdx(value) {
    if (!AppState.selectedWord) return;
    const len = AppState.selectedWord.cells.length;
    AppState.selectedWord.cursorIdx = Math.max(0, Math.min(value, len - 1));
}

// ---------------------------------------------------------------------------
// Saving the draft
// ---------------------------------------------------------------------------

export async function completeSelectedWordEdit(options = {}) {
    const sw = AppState.selectedWord;
    if (!sw) {
        if (options.nextSelection) {
            const next = options.nextSelection;
            selectWord(next.seq, next.direction, next.clickR, next.clickC, next.editorMode || 'puzzle');
        }
        return { saved: false, changedSelection: !!options.nextSelection, error: false };
    }

    if (_isWordEditorOpen()) _syncSelectedWordFromInputs();

    if (!_selectedWordIsPlausibleAnswer()) {
        showMessageLine('Cannot apply: the Answer field holds a search pattern, not an answer', 'error', 0);
        sw.draftText = sw.originalText;
    }

    if (!_selectedWordIsComplete()) {
        sw.draftClue = '';
    }

    const cursorIdx = sw.cursorIdx || 0;
    const editorMode = options.editorMode !== undefined ? options.editorMode : sw.editorMode;
    const dirty = _selectedWordHasChanges();

    if (dirty) {
        const wn = AppState.puzzleWorkingName;
        try {
            AppState.puzzleData = await apiFetch('PUT',
                `/api/puzzles/${encodeURIComponent(wn)}/words/${sw.seq}/${sw.direction}`,
                { text: sw.draftText, clue: sw.draftClue, locked: sw.draftLocked });
        } catch (e) {
            showRequestError('Error saving word', e);
            return { saved: false, changedSelection: false, error: true };
        }
    }

    if (options.keepSelection === false) {
        AppState.selectedWord = null;
    } else if (options.nextSelection) {
        const next = options.nextSelection;
        selectWord(next.seq, next.direction, next.clickR, next.clickC, next.editorMode || 'puzzle');
    } else if (AppState.selectedWord) {
        _refreshSelectedWordFromPuzzleData({ cursorIdx, editorMode });
    }

    _updatePuzzleUndoRedo();
    return { saved: dirty, changedSelection: !!options.nextSelection, error: false };
}

export async function _peCommitWord() {
    return completeSelectedWordEdit();
}

function _selectedWordHasChanges() {
    const sw = AppState.selectedWord;
    if (!sw) return false;
    return sw.draftText !== sw.originalText || sw.draftClue !== sw.originalClue ||
        sw.draftLocked !== sw.originalLocked;
}

function _selectedWordIsComplete() {
    const sw = AppState.selectedWord;
    if (!sw) return false;
    return !((sw.draftText || '').includes(' '));
}

function _selectedWordIsPlausibleAnswer() {
    const sw = AppState.selectedWord;
    if (!sw) return false;
    return /^[A-Z ]*$/.test(sw.draftText || '');
}
