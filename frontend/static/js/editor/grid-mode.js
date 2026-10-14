// Crossword Puzzle Editor — Grid mode: toggling black cells, rotating and generating the grid

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { AppState } from '../core/state.js';
import { messageLineTimeout, showMessageLine, showRequestError } from '../ui/message-line.js';
import { _currentEditorMode, renderPuzzleEditor } from './editor.js';
import { _refreshFillOrderIfVisible } from './fill-order-panel.js';
import { clearSelection } from './selection.js';
import { _refreshPuzzleStatsIfVisible } from './stats-panel.js';
import { BOXSIZE } from '../svg/grid-svg.js';

registerActions({
    'grid-rotate':   () => do_puzzle_rotate_grid(),
    'grid-generate': () => do_puzzle_generate_grid(),
});

export function renderGridModePanel() {
    const pd   = AppState.puzzleData;
    const size = pd ? pd.grid.size : '—';
    const wc   = pd ? pd.puzzle.words.length : '—';
    const canGen = pd && pd.grid.size >= 9 && pd.grid.size % 2 === 1;
    return `
<div class="grid-panel-info">
  <p class="grid-instructions">Click any cell to toggle it between white and black. The grid maintains rotational symmetry automatically.</p>
  <div class="grid-info-card">
    <div class="grid-info-row"><span class="grid-info-label">Grid size</span><span class="grid-info-value">${size} × ${size}</span></div>
    <div class="grid-info-row"><span class="grid-info-label">Words</span><span class="grid-info-value">${wc}</span></div>
    <div class="grid-info-row"><span class="grid-info-label">Symmetry</span><span class="grid-info-value">180° rotational</span></div>
    <div class="grid-info-row"><span class="grid-info-label">Auto-generate</span><span class="grid-info-value">${canGen ? 'Available (odd size ≥ 9)' : 'Not available for this size'}</span></div>
  </div>
  <p class="grid-instructions" style="margin-top:0">Use <b>Rotate</b> to rotate the grid 90°. Use <b>Generate</b> to create a random valid grid pattern. Switch to <b>Puzzle Mode</b> when done.</p>
</div>`;
}

export async function handleGridModeClick(event) {
    const svg = document.getElementById('puzzle-svg');
    const pd  = AppState.puzzleData;
    if (!svg || !pd || _currentEditorMode() !== 'grid') return;
    const rect = svg.getBoundingClientRect();
    const x    = event.clientX - rect.left;
    const y    = event.clientY - rect.top;
    const n    = pd.grid.size;
    const r    = Math.floor(y / BOXSIZE);
    const c    = Math.floor(x / BOXSIZE);
    if (r < 0 || r >= n || c < 0 || c >= n) return;
    try {
        const data = await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/cells/${r}/${c}`);
        await _applyGridModeUpdate(data);
    } catch (e) {
        showRequestError('Error updating grid', e);
    }
}

// True after a Grid-mode edit, until the user is back in Puzzle mode and has
// been told to review the recomputed entries
let gridStructureChanged = false;

// Whether the grid changed since the last call, and forget it
export function takeGridStructureChanged() {
    const changed = gridStructureChanged;
    gridStructureChanged = false;
    return changed;
}

export function forgetGridChanges() {
    gridStructureChanged = false;
}

async function _applyGridModeUpdate(data) {
    AppState.puzzleData = data;
    clearSelection();
    gridStructureChanged = true;
    renderPuzzleEditor();
    await _refreshPuzzleStatsIfVisible();
    await _refreshFillOrderIfVisible();
}

async function do_puzzle_rotate_grid() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() !== 'grid') return;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/rotate`);
        await _applyGridModeUpdate(data);
    } catch (e) { showRequestError('Error rotating grid', e); }
}

export async function do_puzzle_generate_grid() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() !== 'grid') return;
    const btn = document.getElementById('puzzle-generate-btn');
    if (btn) btn.classList.add('w3-disabled');
    try {
        const specParam = AppState.puzzleThemeSpec
            ? '?spec=' + AppState.puzzleThemeSpec.join(',')
            : '';
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/generate${specParam}`);
        if (data.notice) { showMessageLine(data.notice, 'notice'); return; }
        await _applyGridModeUpdate(data);
    } catch (e) { showRequestError('Error generating grid', e, messageLineTimeout()); }
    finally {
        if (btn) btn.classList.remove('w3-disabled');
    }
}
