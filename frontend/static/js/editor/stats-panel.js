// Crossword Puzzle Editor — the Stats panel

import { registerActions } from '../core/actions.js';
import {
    _settlePuzzleEditingBeforeModeSwitch, renderPuzzleEditor,
    renderPuzzleEditorRhs,
} from './editor.js';
import { AppState } from '../state.js';
import { apiFetch, escapeHtml, showRequestError } from '../ui.js';

registerActions({
    'puzzle-stats': () => do_puzzle_stats(),
    'stats-subtab': (el) => setStatsSubTab(el.dataset.tab),
});

export async function do_puzzle_stats() {
    const wn = AppState.puzzleWorkingName;
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/stats`);
        AppState._statsData       = data;
        AppState.showingFillOrder = false;
        AppState.showingStats     = true;
        AppState.sidebarTab       = 'stats';
        renderPuzzleEditor();
    } catch (e) { showRequestError('Error fetching stats', e); }
}

export async function _refreshPuzzleStatsIfVisible() {
    if (AppState.sidebarTab !== 'stats' || !AppState.puzzleWorkingName) return;
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/stats`);
        AppState._statsData = data;
        renderPuzzleEditorRhs();
    } catch (e) {
        // Keep the current panel if the refresh fails.
    }
}

export function renderStatsPanel(stats) {
    const validText  = stats.valid ? 'Valid' : 'Invalid';
    const validClass = stats.valid ? 'stat-valid' : 'stat-invalid';

    const allErrors = Object.values(stats.errors).flat();
    const errorsHtml = allErrors.length === 0 ? '' :
        `<div class="stat-error-box">${allErrors.map(e => escapeHtml(e)).join('<br>')}</div>`;

    const subTab = AppState.statsSubTab === 'words' ? 'words' : 'slots';
    const tabsHtml = `
<div class="stats-subtabs">
  <button class="stats-subtab${subTab === 'slots' ? ' stats-subtab-active' : ''}" data-action="stats-subtab" data-tab="slots">Slots</button>
  <button class="stats-subtab${subTab === 'words' ? ' stats-subtab-active' : ''}" data-action="stats-subtab" data-tab="words">Words</button>
</div>`;

    const bodyHtml = subTab === 'words'
        ? _renderStatsWordsTable()
        : _renderStatsSlotsTable(stats);

    return `
<div class="stat-cards">
  <div class="stat-card ${validClass}">
    <div class="stat-card-value">${validText}</div>
    <div class="stat-card-label">Validity</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-value">${escapeHtml(stats.size)}</div>
    <div class="stat-card-label">Grid size</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-value">${stats.wordcount}</div>
    <div class="stat-card-label">Words</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-value">${stats.blockcount}</div>
    <div class="stat-card-label">Black cells</div>
  </div>
</div>
${errorsHtml}
${tabsHtml}
${bodyHtml}`;
}

function _renderStatsSlotsTable(stats) {
    const wlRows = Object.entries(stats.wordlengths)
        .sort((a, b) => Number(b[0]) - Number(a[0]))
        .map(([len, entry]) => {
            const across = (entry.alist || []).join(', ') || '—';
            const down   = (entry.dlist || []).join(', ') || '—';
            return `<tr>
  <td>${len}</td>
  <td style="word-break:break-word">${escapeHtml(across)}</td>
  <td style="word-break:break-word">${escapeHtml(down)}</td>
</tr>`;
        }).join('');

    return `
<table class="stat-table">
  <tr><th>Length</th><th>Across</th><th>Down</th></tr>
  ${wlRows}
</table>`;
}

function _renderStatsWordsTable() {
    const words = (AppState.puzzleData && AppState.puzzleData.puzzle && AppState.puzzleData.puzzle.words) || [];
    const byLen = new Map();
    for (const w of words) {
        const text = w.answer || '';
        if (!text || text.includes(' ')) continue;
        const len = text.length;
        if (len < 3) continue;
        if (!byLen.has(len)) byLen.set(len, []);
        byLen.get(len).push({ text, seq: w.seq, direction: w.direction });
    }
    const lengths = [...byLen.keys()].sort((a, b) => b - a);
    if (lengths.length === 0) {
        return `<div class="sidebar-empty">No completed words yet.</div>`;
    }
    const rows = lengths.map(len => {
        const items = byLen.get(len).slice().sort((a, b) => a.text.localeCompare(b.text));
        const links = items.map(item =>
            `<a class="stat-word-link" data-action="open-word" data-seq="${item.seq}" data-direction="${item.direction}">${escapeHtml(item.text)}</a>`
        ).join(', ');
        return `<tr>
  <td>${len}</td>
  <td style="word-break:break-word">${links}</td>
</tr>`;
    }).join('');
    return `
<table class="stat-table">
  <tr><th>Length</th><th>Words</th></tr>
  ${rows}
</table>`;
}

function setStatsSubTab(tab) {
    AppState.statsSubTab = (tab === 'words') ? 'words' : 'slots';
    renderPuzzleEditorRhs();
}
