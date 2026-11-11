// Crossword Puzzle Editor — Permute: swapping two locked words by drag and drop
//
// Permute is a mode the user turns on with the toolbar button. Until then this
// module attaches nothing to the grid. While it is on, pressing on a locked
// word and dragging it onto another locked word of the same direction and
// length swaps their letters and clues; the mode then ends.

import { apiFetch } from '../core/api.js';
import { AppState } from '../core/state.js';
import { clearMessageLine, showMessageLine, showRequestError } from '../ui/message-line.js';
import { BOXSIZE } from '../svg/grid-svg.js';
import { _updatePuzzleUndoRedo, renderPuzzleEditor } from './editor.js';
import { _isWordEditorOpen, clearSelection, completeSelectedWordEdit, getSelectedWord } from './selection.js';

// How far the pointer must move, in pixels, before a press becomes a drag
const DRAG_THRESHOLD = 5;

const SVG_NS = 'http://www.w3.org/2000/svg';

// on: whether Permute mode is on. drag: the drag under way, or null; it holds
// the word picked up, where the press began, whether it has become a drag yet,
// and the word under the pointer. justDragged: true for an instant after a
// drag ends, so the click the browser sends then can be ignored.
const permute = { on: false, drag: null, justDragged: false };

export function isPermuteOn() {
    return permute.on;
}

// True if the click being handled is the tail end of a drag
export function wasJustDragged() {
    return permute.justDragged;
}

// Whether the puzzle has two locked words of one direction and length
export function canPermute() {
    const words = AppState.puzzleData ? AppState.puzzleData.puzzle.words : [];
    const seen = new Set();
    for (const w of words) {
        if (!w.locked) continue;
        const key = `${w.direction}${w.cells.length}`;
        if (seen.has(key)) return true;
        seen.add(key);
    }
    return false;
}

// ---------------------------------------------------------------------------
// Turning the mode on and off
// ---------------------------------------------------------------------------

export async function togglePermute() {
    if (permute.on) {
        stopPermute();
        renderPuzzleEditor();
        return;
    }
    if (_isWordEditorOpen() || !canPermute()) return;
    const result = await completeSelectedWordEdit({ keepSelection: false });
    if (result.error) return;
    clearSelection();
    permute.on = true;
    document.addEventListener('keydown', onKeydown);
    renderPuzzleEditor();
    showMessageLine('Permute: drag a locked word onto another locked word of the same length. ' +
        'Esc to cancel.', 'notice', 0);
}

// Turn the mode off without redrawing; the caller redraws if it needs to.
export function stopPermute() {
    if (!permute.on) return;
    permute.on = false;
    endDrag();
    document.removeEventListener('keydown', onKeydown);
    clearMessageLine();
}

function onKeydown(e) {
    if (e.key !== 'Escape') return;
    e.preventDefault();
    if (permute.drag && permute.drag.started) {
        permute.drag.cancelled = true;
        removeFeedback();
        return;
    }
    stopPermute();
    renderPuzzleEditor();
}

// Called each time the grid is drawn; attaches the drag code if Permute is on
export function attachWordDrag(svg) {
    if (!permute.on) return;
    svg.style.touchAction = 'none';
    svg.addEventListener('pointerdown', onPointerDown);
    svg.addEventListener('pointermove', onHover);
}

// ---------------------------------------------------------------------------
// Finding words
// ---------------------------------------------------------------------------

function cellAt(event) {
    const svg = document.getElementById('puzzle-svg');
    if (!svg) return null;
    const rect = svg.getBoundingClientRect();
    const r = Math.floor(1 + (event.clientY - rect.top) / BOXSIZE);
    const c = Math.floor(1 + (event.clientX - rect.left) / BOXSIZE);
    const n = AppState.puzzleData.grid.size;
    if (r < 1 || r > n || c < 1 || c > n) return null;
    return { r, c };
}

function wordsAt(cell, direction) {
    return AppState.puzzleData.puzzle.words.filter(w =>
        (!direction || w.direction === direction) &&
        w.cells.some(([r, c]) => r === cell.r && c === cell.c));
}

// The locked word to pick up at a square, or null. If both the Across and the
// Down word through it are locked, the selected one wins, else the Across one.
function pickUpAt(cell) {
    const locked = wordsAt(cell).filter(w => w.locked);
    if (locked.length <= 1) return locked[0] || null;
    const selected = getSelectedWord();
    const chosen = selected && locked.find(w =>
        w.seq === selected.seq && w.direction === selected.direction);
    return chosen || locked.find(w => w.direction === 'across');
}

// Why the dragged word can't go onto this word, or '' if it can
function problemWith(dragged, target) {
    if (!target.locked) return 'Only locked words can be swapped';
    if (target.cells.length !== dragged.cells.length) return 'Different length';
    return '';
}

// ---------------------------------------------------------------------------
// Pointer handling
// ---------------------------------------------------------------------------

function onHover(event) {
    if (permute.drag) return;
    const svg = event.currentTarget;
    const cell = cellAt(event);
    svg.style.cursor = cell && pickUpAt(cell) ? 'grab' : 'pointer';
}

function onPointerDown(event) {
    if (event.button !== 0 || event.shiftKey || _isWordEditorOpen()) return;
    const cell = cellAt(event);
    const word = cell && pickUpAt(cell);
    if (!word) return;
    const svg = event.currentTarget;
    svg.setPointerCapture(event.pointerId);
    svg.addEventListener('pointermove', onPointerMove);
    svg.addEventListener('pointerup', onPointerUp);
    svg.addEventListener('pointercancel', onPointerCancel);
    permute.drag = {
        word, svg, startX: event.clientX, startY: event.clientY,
        started: false, cancelled: false, target: null,
    };
}

function onPointerMove(event) {
    const drag = permute.drag;
    if (!drag || drag.cancelled) return;
    if (!drag.started) {
        const far = Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY);
        if (far < DRAG_THRESHOLD) return;
        drag.started = true;
        drag.svg.style.cursor = 'grabbing';
    }
    const cell = cellAt(event);
    const found = cell ? wordsAt(cell, drag.word.direction)[0] : null;
    drag.target = found && found !== drag.word ? found : null;
    showFeedback(event);
}

async function onPointerUp() {
    const drag = permute.drag;
    if (!drag) return;
    const { word, target, started, cancelled } = drag;
    endDrag();
    if (!started) return;
    permute.justDragged = true;
    setTimeout(() => { permute.justDragged = false; }, 0);
    if (cancelled || !target) return;
    const problem = problemWith(word, target);
    if (problem) {
        showMessageLine(problem, 'error');
        return;
    }
    await doSwap(word, target);
}

function onPointerCancel() {
    endDrag();
}

function endDrag() {
    const drag = permute.drag;
    if (!drag) return;
    drag.svg.removeEventListener('pointermove', onPointerMove);
    drag.svg.removeEventListener('pointerup', onPointerUp);
    drag.svg.removeEventListener('pointercancel', onPointerCancel);
    drag.svg.style.cursor = 'pointer';
    removeFeedback();
    permute.drag = null;
}

// ---------------------------------------------------------------------------
// Feedback while dragging: shading, an outline on the target, and a note
// ---------------------------------------------------------------------------

function showFeedback(event) {
    const { word, target, svg } = permute.drag;
    removeFeedback();
    const layer = document.createElementNS(SVG_NS, 'g');
    layer.id = 'permute-layer';
    layer.setAttribute('pointer-events', 'none');
    addCells(layer, word.cells, 'rgba(70,130,220,0.35)', '#2f6fdb');
    if (target) {
        const problem = problemWith(word, target);
        addCells(layer, target.cells,
            problem ? 'rgba(220,60,60,0.25)' : 'rgba(60,170,90,0.30)',
            problem ? '#d33' : '#2a9d4b');
        if (problem) showNote(problem, event);
    }
    svg.appendChild(layer);
}

function addCells(layer, cells, fill, stroke) {
    for (const [r, c] of cells) {
        const rect = document.createElementNS(SVG_NS, 'rect');
        rect.setAttribute('x', (c - 1) * BOXSIZE);
        rect.setAttribute('y', (r - 1) * BOXSIZE);
        rect.setAttribute('width', BOXSIZE);
        rect.setAttribute('height', BOXSIZE);
        rect.setAttribute('fill', fill);
        rect.setAttribute('stroke', stroke);
        rect.setAttribute('stroke-width', 2);
        layer.appendChild(rect);
    }
}

function showNote(text, event) {
    const note = document.createElement('div');
    note.id = 'permute-note';
    note.textContent = text;
    note.style.cssText = 'position:fixed;z-index:1000;pointer-events:none;padding:2px 8px;' +
        'background:#333;color:#fff;font-size:0.8rem;border-radius:3px;' +
        `left:${event.clientX + 12}px;top:${event.clientY + 12}px`;
    document.body.appendChild(note);
}

function removeFeedback() {
    const layer = document.getElementById('permute-layer');
    if (layer) layer.remove();
    const note = document.getElementById('permute-note');
    if (note) note.remove();
}

// ---------------------------------------------------------------------------
// The swap itself
// ---------------------------------------------------------------------------

async function doSwap(word, target) {
    const before = AppState.puzzleData.puzzle.words;
    let reply;
    try {
        reply = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/words/swap`,
            { direction: word.direction, seq_a: word.seq, seq_b: target.seq });
    } catch (e) {
        showRequestError('Cannot swap', e);
        return;
    }
    const cleared = reply.puzzle.words.filter(after => {
        const was = before.find(w => w.seq === after.seq && w.direction === after.direction);
        return was && was.clue && !after.clue && !isOneOf(after, word, target);
    }).length;
    AppState.puzzleData = reply;
    stopPermute();
    clearSelection();
    renderPuzzleEditor();
    _updatePuzzleUndoRedo();
    const names = `${word.seq}-${cap(word.direction)} and ${target.seq}-${cap(target.direction)}`;
    const note = cleared ? ` (${cleared} crossing clue${cleared === 1 ? '' : 's'} cleared)` : '';
    showMessageLine(`Swapped ${names}${note}`);
}

function isOneOf(w, a, b) {
    return w.direction === a.direction && (w.seq === a.seq || w.seq === b.seq);
}

function cap(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}
