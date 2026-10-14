// Crossword Puzzle Editor — the dashboard's change-state dialog

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { hideElement, showElement } from '../core/dom.js';
import { ALL_STATES, DashboardState, renderDashboard } from './dashboard.js';

registerActions({
    'dash-state':          (el) => _dashStateChosen(el),
    'state-dialog-cancel': () => _dashCloseStateDialog(true),
});

let _dashStateRevertSelect = null;  // <select> to reset on cancel/error

function _dashStateChosen(sel) {
    const name = sel.getAttribute('data-dash-state');
    const row = DashboardState.puzzles.find(p => p.name === name);
    openStateDialog(row, sel.value, sel);
}

function openStateDialog(row, newState, selectEl) {
    if (!row) return;
    _dashStateRevertSelect = selectEl;

    document.getElementById('state-dialog-name').textContent = row.name;

    let curText = row.state;
    if ((row.state === 'submitted' || row.state === 'published') && row.publisher) {
        curText += ` (${row.publisher})`;
    }
    document.getElementById('state-dialog-current').textContent = curText;

    const stateSel = document.getElementById('state-dialog-new');
    stateSel.innerHTML = ALL_STATES.map(s =>
        `<option value="${s}"${s === newState ? ' selected' : ''}>${s}</option>`).join('');

    const pubInput = document.getElementById('state-dialog-publisher');
    pubInput.value = row.publisher || '';
    const dateInput = document.getElementById('state-dialog-date');
    dateInput.value = new Date().toISOString().slice(0, 10);

    document.getElementById('state-dialog-error').textContent = '';

    stateSel.onchange = _dashUpdateStateDialogFields;
    _dashUpdateStateDialogFields();

    document.getElementById('state-dialog-ok').onclick = () => _dashSubmitState(row);
    const cancel = () => _dashCloseStateDialog(true);
    document.getElementById('state-dialog-cancel').onclick = cancel;
    document.getElementById('state-dialog-close').onclick = cancel;

    showElement('state-dialog');
}

function _dashUpdateStateDialogFields() {
    const newState = document.getElementById('state-dialog-new').value;
    const show = newState === 'submitted' || newState === 'published';
    const pubRow = document.getElementById('state-dialog-publisher-row');
    const dateRow = document.getElementById('state-dialog-date-row');
    pubRow.style.display = show ? '' : 'none';
    dateRow.style.display = show ? '' : 'none';
    // publisher required only for 'submitted' (matches backend)
    document.getElementById('state-dialog-publisher').required = (newState === 'submitted');
}

async function _dashSubmitState(row) {
    const newState = document.getElementById('state-dialog-new').value;
    const pub = document.getElementById('state-dialog-publisher').value.trim();
    const date = document.getElementById('state-dialog-date').value;
    const errEl = document.getElementById('state-dialog-error');

    if (newState === 'submitted' && !pub) {
        errEl.textContent = 'Publisher is required when submitting.';
        return;
    }

    const body = { state: newState };
    if (newState === 'submitted') { body.publisher = pub; body.date_submitted = date; }
    if (newState === 'published') { if (pub) body.publisher = pub; body.date_published = date; }

    try {
        await apiFetch('PUT', `/api/puzzles/${encodeURIComponent(row.name)}/state`, body);
        _dashStateRevertSelect = null;   // success — no need to revert
        _dashCloseStateDialog(false);
        await renderDashboard();
    } catch (e) {
        errEl.textContent = e.message || 'Failed to change state.';
    }
}

function _dashCloseStateDialog(revert) {
    hideElement('state-dialog');
    if (revert && _dashStateRevertSelect) {
        const name = _dashStateRevertSelect.getAttribute('data-dash-state');
        const row = DashboardState.puzzles.find(p => p.name === name);
        if (row) _dashStateRevertSelect.value = row.state;
    }
    _dashStateRevertSelect = null;
}
