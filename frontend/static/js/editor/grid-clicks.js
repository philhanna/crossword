// Crossword Puzzle Editor — clicks on the grid in Puzzle mode
//
// A single click selects the Across word under the pointer, a double click the
// Down word. A single click waits CLICK_DELAY ms first, to be sure it isn't the
// start of a double click.

import { AppState } from '../core/state.js';
import { renderPuzzleEditor } from './editor.js';
import {
    _isWordEditorOpen, _setSelectedWordCursorIdx, completeSelectedWordEdit,
    findWordAtCell, getSelectedWord,
} from './selection.js';
import { _weApplyAndClose, openWordEditor } from './word-editor.js';
import { BOXSIZE } from '../svg/grid-svg.js';

const CLICK_DELAY = 280;

// A single click waiting out CLICK_DELAY: pending is true while it waits,
// timeout is its timer, and event the click it will act on.
const click = { pending: false, timeout: null, event: null };

export async function handlePuzzleClick(event) {
    const wasEditingWord = _isWordEditorOpen();
    if (wasEditingWord) {
        if (click.timeout) {
            clearTimeout(click.timeout);
            click.timeout = null;
        }
        click.pending = false;
        click.event = null;
        await _weApplyAndClose();
        if (_isWordEditorOpen()) return;
    }
    _focusPuzzleSvg();
    click.event = event;
    if (!click.pending) {
        click.pending = true;
        click.timeout = setTimeout(() => {
            click.pending = false;
            click.timeout = null;
            puzzleClickAt(click.event, 'across', !wasEditingWord);
        }, CLICK_DELAY);
    } else {
        click.pending = false;
        clearTimeout(click.timeout);
        click.timeout = null;
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
        const current = getSelectedWord();
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
    if (!getSelectedWord() || _isWordEditorOpen()) return;
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
