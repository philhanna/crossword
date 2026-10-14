// Crossword Puzzle Editor — typing into the grid
//
// Two keydown handlers take turns on the document: _peKeydown while a word is
// selected in the grid, _weKeydown while the word editor is open. Whoever
// opens or closes the word editor swaps them; exactly one may be attached at
// a time, or each key is handled twice.

import { AppState } from '../core/state.js';
import { _updatePuzzleToolbar, renderPuzzleEditor, renderPuzzleEditorLhs } from './editor.js';
import {
    _getSelectedWordCursorIdx, _isWordEditorOpen, _setSelectedWordCursorIdx,
    clearSelection, completeSelectedWordEdit, findWordAtCell, getSelectedWord,
} from './selection.js';
import {
    _weSyncTextInputFromAnswer, closeWordEditor, doWordEditOK,
    doWordSuggestFetch, openWordEditor,
} from './word-editor.js';

export function _peKeydown(e) {
    if (!getSelectedWord() || _isWordEditorOpen()) return;
    // Don't capture keystrokes going to modal inputs
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    const sw  = getSelectedWord();
    const len = sw.cells.length;
    const isAcross = sw.direction === 'across';

    if (e.key === 'Escape') {
        completeSelectedWordEdit({ keepSelection: false }).then((result) => {
            if (result.error) return;
            clearSelection();
            _updatePuzzleToolbar();
            renderPuzzleEditor();
        });
        e.preventDefault(); return;
    }

    if ((isAcross && e.key === 'ArrowRight') || (!isAcross && e.key === 'ArrowDown')) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() + 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }
    if ((isAcross && e.key === 'ArrowLeft') || (!isAcross && e.key === 'ArrowUp')) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() - 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    // Cross-direction navigation: switch to perpendicular word at the same cell
    const [curR, curC] = sw.cells[_getSelectedWordCursorIdx()];
    if (!isAcross && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        const neighbor = findWordAtCell(curR, curC, 'across');
        if (neighbor) {
            completeSelectedWordEdit({
                nextSelection: { seq: neighbor.seq, direction: neighbor.direction, clickR: curR, clickC: curC }
            }).then((result) => {
                if (!result.error) renderPuzzleEditor();
            });
        }
        e.preventDefault(); return;
    }
    if (isAcross && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        const neighbor = findWordAtCell(curR, curC, 'down');
        if (neighbor) {
            completeSelectedWordEdit({
                nextSelection: { seq: neighbor.seq, direction: neighbor.direction, clickR: curR, clickC: curC }
            }).then((result) => {
                if (!result.error) renderPuzzleEditor();
            });
        }
        e.preventDefault(); return;
    }

    const isEditKey = e.key === 'Delete' || e.key === 'Backspace' ||
        e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key));
    if (sw.draftLocked && isEditKey) {
        e.preventDefault();
        return;
    }

    if (e.key === 'Delete') {
        const idx = _getSelectedWordCursorIdx();
        const t = sw.draftText;
        sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    if (e.key === 'Backspace') {
        let idx = _getSelectedWordCursorIdx();
        const t = sw.draftText;
        if (t[idx] !== ' ') {
            sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        } else if (idx > 0) {
            idx--;
            _setSelectedWordCursorIdx(idx);
            sw.draftText = sw.draftText.slice(0, idx) + ' ' + sw.draftText.slice(idx + 1);
        }
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    if (e.key === 'Tab') {
        e.preventDefault();
        const words = [...AppState.puzzleData.puzzle.words].sort((a, b) =>
            a.direction === b.direction ? a.seq - b.seq : a.direction.localeCompare(b.direction));
        const idx = words.findIndex(w => w.seq === sw.seq && w.direction === sw.direction);
        const next = e.shiftKey
            ? words[(idx - 1 + words.length) % words.length]
            : words[(idx + 1) % words.length];
        completeSelectedWordEdit({
            nextSelection: { seq: next.seq, direction: next.direction }
        }).then((result) => {
            if (!result.error) renderPuzzleEditor();
        });
        return;
    }

    if (e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key))) {
        const ch = e.key === ' ' ? ' ' : e.key.toUpperCase();
        const idx = _getSelectedWordCursorIdx();
        const t = sw.draftText;
        sw.draftText = t.slice(0, idx) + ch + t.slice(idx + 1);
        // Advance cursor one step forward
        if (idx < len - 1) _setSelectedWordCursorIdx(idx + 1);
        renderPuzzleEditorLhs(); e.preventDefault();
    }
}

export async function _weKeydown(e) {
    if (!_isWordEditorOpen()) return;
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') {
        if (e.key === 'Escape') { closeWordEditor();     e.preventDefault(); }
        if (e.key === 'Enter' && e.target.id === 'we-text') { doWordSuggestFetch(); e.preventDefault(); }
        if (e.key === 'Enter' && e.target.id !== 'we-text') { doWordEditOK();       e.preventDefault(); }
        return;
    }
    // For buttons and other controls, keep native Enter behavior. When focus is
    // on the grid SVG itself, Enter should mirror the Apply button.
    if (e.key === 'Escape') { closeWordEditor(); e.preventDefault(); return; }
    if (e.key === 'Enter' && e.target.closest && e.target.closest('#puzzle-svg')) {
        doWordEditOK();
        e.preventDefault();
        return;
    }

    const sw = getSelectedWord();
    const len = sw.cells.length;

    const isAcross    = sw.direction === 'across';
    const forwardKey  = isAcross ? 'ArrowRight' : 'ArrowDown';
    const backwardKey = isAcross ? 'ArrowLeft'  : 'ArrowUp';

    if (e.key === forwardKey && _getSelectedWordCursorIdx() < len - 1) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() + 1);
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }
    if (e.key === backwardKey && _getSelectedWordCursorIdx() > 0) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() - 1);
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }
    if ((isAcross && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) ||
        (!isAcross && (e.key === 'ArrowLeft' || e.key === 'ArrowRight'))) {
        const [curR, curC] = sw.cells[_getSelectedWordCursorIdx()];
        const perpDir = isAcross ? 'down' : 'across';
        const neighbor = findWordAtCell(curR, curC, perpDir);
        const result = await completeSelectedWordEdit({
            nextSelection: neighbor ? {
                seq: neighbor.seq,
                direction: neighbor.direction,
                clickR: curR,
                clickC: curC,
            } : null
        });
        if (result.error) return;
        if (!neighbor) closeWordEditor();
        else await openWordEditor(neighbor.seq, neighbor.direction);
        e.preventDefault();
        return;
    }

    const isEditKey = e.key === 'Delete' || e.key === 'Backspace' ||
        e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key));
    if (sw.draftLocked && isEditKey) {
        e.preventDefault();
        return;
    }

    if (e.key === 'Delete') {
        const idx = _getSelectedWordCursorIdx();
        const t = sw.draftText || ''.padEnd(len);
        sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }

    if (e.key === 'Backspace') {
        let idx = _getSelectedWordCursorIdx();
        const t = sw.draftText || ''.padEnd(len);
        if (t[idx] !== ' ') {
            sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        } else if (idx > 0) {
            idx--;
            _setSelectedWordCursorIdx(idx);
            sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        }
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }

    if (e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key))) {
        const ch = e.key === ' ' ? ' ' : e.key.toUpperCase();
        const idx = _getSelectedWordCursorIdx();
        const t = (sw.draftText || '').padEnd(len).slice(0, len);
        sw.draftText = t.slice(0, idx) + ch + t.slice(idx + 1);
        if (idx < len - 1) _setSelectedWordCursorIdx(idx + 1);
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
    }
}
