// Crossword Puzzle Editor — clicks on the grid in Puzzle mode
//
// A single click selects the Across word under the pointer, a double click the
// Down word. A single click waits CLICK_DELAY ms first, to be sure it isn't the
// start of a double click.

import { renderPuzzleEditor } from './editor.js';
import {
    _isWordEditorOpen, _setSelectedWordCursorIdx, completeSelectedWordEdit,
    findWordAtCell,
} from './selection.js';
import { _weApplyAndClose, openWordEditor } from './word-editor.js';
import { AppState, BOXSIZE } from '../state.js';

let _clickState   = 0;
let _clickTimeout = null;
let _clickEvent   = null;
let _ignorePuzzleClicksUntil = 0;
const CLICK_DELAY = 280;

export async function handlePuzzleClick(event) {
    if (Date.now() < _ignorePuzzleClicksUntil) return;
    const wasEditingWord = _isWordEditorOpen();
    if (wasEditingWord) {
        if (_clickTimeout) {
            clearTimeout(_clickTimeout);
            _clickTimeout = null;
        }
        _clickState = 0;
        _clickEvent = null;
        await _weApplyAndClose();
        if (_isWordEditorOpen()) return;
    }
    _focusPuzzleSvg();
    _clickEvent = event;
    if (_clickState === 0) {
        _clickState = 1;
        _clickTimeout = setTimeout(() => {
            _clickState = 0;
            _clickTimeout = null;
            puzzleClickAt(_clickEvent, 'across', !wasEditingWord);
        }, CLICK_DELAY);
    } else {
        _clickState = 0;
        clearTimeout(_clickTimeout);
        _clickTimeout = null;
        puzzleClickAt(event, 'down', !wasEditingWord);
    }
}

async function puzzleClickAt(event, direction, openEditor = true) {
    const svg = document.getElementById('puzzle-svg');
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const r = Math.floor(1 + y / BOXSIZE);
    const c = Math.floor(1 + x / BOXSIZE);
    const n = AppState.puzzleData.grid.size;
    if (r < 1 || r > n || c < 1 || c > n) {
        await completeSelectedWordEdit();
        renderPuzzleEditor();
        return;
    }
    if (AppState.puzzleData.grid.cells[(r - 1) * n + (c - 1)]) {
        await completeSelectedWordEdit();
        renderPuzzleEditor();
        return;
    } // black cell
    const word = findWordAtCell(r, c, direction);
    if (word) {
        const current = AppState.selectedWord;
        const inCurrentWord = current && current.seq === word.seq && current.direction === word.direction &&
            current.cells.some(([wr, wc]) => wr === r && wc === c);
        if (!inCurrentWord) {
            const result = await completeSelectedWordEdit({
                nextSelection: { seq: word.seq, direction: word.direction, clickR: r, clickC: c }
            });
            if (result.error) return;
        } else {
            const clickedIdx = current.cells.findIndex(([wr, wc]) => wr === r && wc === c);
            if (clickedIdx >= 0) _setSelectedWordCursorIdx(clickedIdx);
            if (openEditor) {
                await openWordEditor(word.seq, word.direction);
                return;
            }
        }
        if (openEditor && !_isWordEditorOpen()) await openWordEditor(word.seq, word.direction);
        else renderPuzzleEditor();
    }
}

export function _focusPuzzleSvg() {
    const svg = document.getElementById('puzzle-svg');
    if (!svg) return;
    try {
        svg.focus({ preventScroll: true });
    } catch (e) {
        svg.focus();
    }
}

export function _peOutsideMousedown(e) {
    if (!AppState.selectedWord || _isWordEditorOpen()) return;
    const svg = document.getElementById('puzzle-svg');
    if (svg && svg.contains(e.target)) return; // SVG clicks handled by puzzleClickAt
    if (e.target.closest && (
        e.target.closest('#action-bar') ||
        e.target.closest('#rhs') ||
        e.target.closest('.app-bar') ||
        e.target.closest('#mb') ||
        e.target.closest('#ib') ||
        e.target.closest('#ch') ||
        e.target.closest('#constraints-popup') ||
        e.target.closest('#defs-popup') ||
        e.target.closest('.puzzle-title-display') ||
        e.target.closest('button') ||
        e.target.closest('a') ||
        e.target.closest('input') ||
        e.target.closest('textarea') ||
        e.target.closest('select') ||
        e.target.closest('label')
    )) {
        return;
    }
    completeSelectedWordEdit().then((result) => {
        if (!result.error) renderPuzzleEditor();
    });
}
