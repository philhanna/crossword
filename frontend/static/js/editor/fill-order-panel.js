// Crossword Puzzle Editor — the Fill order panel: which slots to fill next

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { escapeHtml } from '../core/dom.js';
import { AppState } from '../core/state.js';
import { showRequestError } from '../ui/message-line.js';
import {
    _currentEditorMode, _settlePuzzleEditingBeforeModeSwitch, getSidebarTab,
    renderActionBar, renderPuzzleEditor, renderPuzzleEditorRhs, setSidebarTab,
} from './editor.js';

registerActions({
    'fill-order': () => do_puzzle_fill_order(),
});

// cache: fill-order responses keyed by the grid's letters (_cellLettersKey),
// so going back to an earlier fill doesn't ask the server again.
// loading: true while a request is out, which greys out the button.
export const fillOrder = { cache: new Map(), loading: false };

export function isFillOrderLoading() {
    return fillOrder.loading;
}

// The fill order for the grid as it is now, or undefined if not fetched yet
export function cachedFillOrder() {
    return fillOrder.cache.get(_cellLettersKey(AppState.puzzleData));
}

export function forgetFillOrders() {
    fillOrder.cache = new Map();
}

export async function do_puzzle_fill_order() {
    if (fillOrder.loading) return;
    const wn = AppState.puzzleWorkingName;
    const btn = document.getElementById('puzzle-fill-order-btn');
    fillOrder.loading = true;
    if (btn) {
        btn.classList.add('is-disabled');
        btn.disabled = true;
    }
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        if (!cachedFillOrder()) {
            const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/fill-order`);
            fillOrder.cache.set(_cellLettersKey(AppState.puzzleData), data);
        }
        setSidebarTab('fill-order');
        renderPuzzleEditor();
    } catch (e) { showRequestError('Error fetching fill order', e); }
    finally {
        fillOrder.loading = false;
        renderActionBar();
    }
}

export async function _refreshFillOrderIfVisible() {
    if (getSidebarTab() !== 'fill-order' || !AppState.puzzleWorkingName || _currentEditorMode() !== 'puzzle') return;
    const key = _cellLettersKey(AppState.puzzleData);
    if (fillOrder.cache.has(key)) {
        renderPuzzleEditorRhs();
        return;
    }
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/fill-order`);
        fillOrder.cache.set(key, data);
        renderPuzzleEditorRhs();
    } catch (e) {
        // Keep the current panel if the refresh fails.
    }
}

function _cellLettersKey(puzzleData) {
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
