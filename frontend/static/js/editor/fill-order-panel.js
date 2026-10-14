// Crossword Puzzle Editor — the Fill order panel: which slots to fill next

import { registerActions } from '../core/actions.js';
import {
    _currentEditorMode, _settlePuzzleEditingBeforeModeSwitch, renderActionBar,
    renderPuzzleEditor, renderPuzzleEditorRhs,
} from './editor.js';
import { AppState } from '../state.js';
import { apiFetch, escapeHtml, showRequestError } from '../ui.js';

registerActions({
    'fill-order': () => do_puzzle_fill_order(),
});

export async function do_puzzle_fill_order() {
    if (AppState.fillOrderLoading) return;
    const wn = AppState.puzzleWorkingName;
    const btn = document.getElementById('puzzle-fill-order-btn');
    AppState.fillOrderLoading = true;
    if (btn) {
        btn.classList.add('w3-disabled');
        btn.disabled = true;
    }
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const key = _cellLettersKey(AppState.puzzleData);
        let data = AppState._fillOrderCache && AppState._fillOrderCache.get(key);
        if (!data) {
            data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/fill-order`);
            if (AppState._fillOrderCache) AppState._fillOrderCache.set(key, data);
        }
        AppState.showingStats       = false;
        AppState.showingFillOrder   = true;
        AppState.sidebarTab         = 'fill-order';
        renderPuzzleEditor();
    } catch (e) { showRequestError('Error fetching fill order', e); }
    finally {
        AppState.fillOrderLoading = false;
        renderActionBar();
    }
}

export async function _refreshFillOrderIfVisible() {
    if (AppState.sidebarTab !== 'fill-order' || !AppState.puzzleWorkingName || _currentEditorMode() !== 'puzzle') return;
    const key = _cellLettersKey(AppState.puzzleData);
    if (AppState._fillOrderCache && AppState._fillOrderCache.has(key)) {
        renderPuzzleEditorRhs();
        return;
    }
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/fill-order`);
        if (AppState._fillOrderCache) AppState._fillOrderCache.set(key, data);
        renderPuzzleEditorRhs();
    } catch (e) {
        // Keep the current panel if the refresh fails.
    }
}

export function _cellLettersKey(puzzleData) {
    if (!puzzleData?.puzzle?.cells) return '';
    return Object.entries(puzzleData.puzzle.cells)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([idx, cell]) => `${idx}:${cell.letter ?? ''}`)
        .join('|');
}

export function renderFillOrderPanel(data) {
    const rows = (data.fill_priority || []).map(item => {
        const countLabel = `${item.candidate_count} candidate${item.candidate_count === 1 ? '' : 's'}`;
        return `<tr data-action="open-word" data-seq="${item.seq}" data-direction="${item.direction}">
  <td style="white-space:nowrap"><a>${escapeHtml(item.label)}</a></td>
  <td style="font-family:var(--font-mono)">${escapeHtml(item.pattern || '')}</td>
  <td style="white-space:nowrap">${escapeHtml(countLabel)}</td>
  <td>${escapeHtml(item.reason || '')}</td>
</tr>`;
    }).join('');
    const body = rows
        ? `<table class="fill-table">
    <thead><tr><th>Slot</th><th>Pattern</th><th>Candidates</th><th>Reason</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`
        : `<div class="sidebar-empty">No fill-order data yet.</div>`;

    return `
<p class="fill-intro">Best slots to fill next, ranked by candidate count. Click a row to open the word editor for that slot.</p>
${body}`;
}
