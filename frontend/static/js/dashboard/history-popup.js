// Crossword Puzzle Editor — a puzzle's state history, from the dashboard's right-click menu

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { escapeHtml, hideElement, showElement } from '../core/dom.js';
import { showContextMenu } from '../ui/context-menu.js';
import { askConfirm } from '../ui/dialogs.js';
import { showRequestError } from '../ui/message-line.js';
import { fmtMonthDay } from './dashboard.js';
import { _openWorkingCopyInEditor } from '../puzzle-file/lifecycle.js';

registerActions({
    'dash-row-menu':   (el, e) => _dashOpenContextMenu(e, el.getAttribute('data-dash-name')),
    'history-restore': (el) => _dashConfirmRestore(el.dataset.name, parseInt(el.dataset.historyId, 10)),
});

function _dashOpenContextMenu(e, name) {
    if (!name) return;
    e.preventDefault();
    showContextMenu(e.clientX, e.clientY, [
        { label: 'Show history', onClick: () => _dashShowHistory(name) },
    ]);
}

async function _dashShowHistory(name) {
    document.getElementById('history-popup-title').textContent = `History — ${name}`;
    const body = document.getElementById('history-popup-body');
    body.innerHTML = '<div class="w3-container w3-padding">Loading...</div>';
    showElement('history-popup');

    try {
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(name)}/state/history`);
        body.innerHTML = _historyTableHtml(name, data.history || []);
    } catch (e) {
        body.innerHTML = `<p>Error loading history: ${escapeHtml(e.message)}</p>`;
    }
}

function _historyTableHtml(name, history) {
    if (history.length === 0) {
        return '<p class="dash-empty">No state history recorded.</p>';
    }
    const sorted = [...history].sort((a, b) => b.id - a.id);
    const rows = sorted.map((h, i) => {
        let detail = '';
        if (h.state === 'submitted' && h.publisher) {
            detail = `submitted to ${escapeHtml(h.publisher)}`;
        } else if (h.state === 'published' && h.publisher) {
            detail = `published by ${escapeHtml(h.publisher)}`;
        }
        const restoreCell = (h.has_content && i > 0)
            ? `<button class="dash-history-restore" data-action="history-restore" ` +
              `data-name="${escapeHtml(name)}" data-history-id="${h.id}">Restore</button>`
            : '';
        return `<tr>
            <td>${fmtDateTime(h.changed_at)}</td>
            <td>${escapeHtml(h.state)}</td>
            <td>${detail}</td>
            <td>${escapeHtml(h.comment || '')}</td>
            <td>${restoreCell}</td>
          </tr>`;
    }).join('');
    return `
      <table class="dash-table" style="table-layout:fixed">
        <colgroup>
          <col style="width:150px"><col style="width:90px"><col style="width:150px">
          <col style="width:250px"><col style="width:70px">
        </colgroup>
        <thead><tr><th>Changed</th><th>State</th><th>Details</th><th>Comment</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
}

function fmtDateTime(iso) {
    // Parse an ISO-ish timestamp and format as MM/dd/yy HH:mm. Guards against blanks.
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    return `${fmtMonthDay(iso)} ${hh}:${min}:${ss}`;
}

async function _dashConfirmRestore(name, historyId) {
    hideElement('history-popup');
    const confirmed = await askConfirm(
        'Restore puzzle',
        `Open this earlier saved version of <b>'${escapeHtml(name)}'</b> for editing? ` +
        `This leaves the dashboard. The current version stays untouched until you ` +
        `explicitly Save.`,
        'Restore',
    );
    if (confirmed) await _dashRestorePuzzle(name, historyId);
}

async function _dashRestorePuzzle(name, historyId) {
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(name)}/state/history/${historyId}/restore`);
        await _openWorkingCopyInEditor(name, data.working_name);
    } catch (e) { showRequestError('Error restoring puzzle', e); }
}
