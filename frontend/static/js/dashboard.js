// Crossword Puzzle Editor — dashboard view (landing screen)
//
// Renders a four-card summary (top half) and a tabbed, full-width puzzle list
// (bottom half) into the #lhs workspace pane. Data comes from GET /api/dashboard
// in a single round-trip and is cached in DashboardState so tab switches and the
// top cards render client-side without refetching.

const ALL_STATES = ['draft', 'filled', 'finished', 'submitted', 'published', 'archived'];

const DASH_CARDS = [
    { idx: 1, title: 'IN PROGRESS', states: ['draft'] },
    { idx: 2, title: 'COMPLETED',   states: ['filled', 'finished'] },
    { idx: 3, title: 'SUBMITTED',   states: ['submitted', 'published'] },
    { idx: 4, title: 'ARCHIVED',    states: ['archived'] },
];

const DASH_TABS = [...ALL_STATES, 'all'];

const DashboardState = {
    puzzles: [],          // rows from GET /api/dashboard, modified DESC
    activeTab: 'all',     // active bottom-half tab
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtMonthDay(iso) {
    // Parse an ISO-ish timestamp and format as MM/dd. Guards against blanks.
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${mm}/${dd}`;
}

function _dashRowLengths(row) {
    // "7-letter: 12, 6-letter: 18" from top_lengths
    return (row.top_lengths || [])
        .map(t => `${t.length}-letter: ${t.count}`)
        .join(', ');
}

function _dashDisplayTitle(row) {
    return row.title || row.name;
}

// ---------------------------------------------------------------------------
// Data load
// ---------------------------------------------------------------------------

async function renderDashboard() {
    let data;
    try {
        data = await apiFetch('GET', '/api/dashboard');
    } catch (e) {
        document.getElementById('rhs').innerHTML = '';
        document.getElementById('lhs').innerHTML =
            `<div class="home-welcome"><p>Error loading dashboard: ${escapeHtml(e.message)}</p></div>`;
        return;
    }
    if (data.error) {
        document.getElementById('rhs').innerHTML = '';
        document.getElementById('lhs').innerHTML =
            `<div class="home-welcome"><p>Error loading dashboard: ${escapeHtml(data.error)}</p></div>`;
        return;
    }
    DashboardState.puzzles = data.puzzles || [];
    document.getElementById('rhs').innerHTML = '';
    document.getElementById('lhs').innerHTML = dashboardHtml(DashboardState.puzzles);
    bindDashboardEvents();
}

// ---------------------------------------------------------------------------
// Top half — four cards
// ---------------------------------------------------------------------------

function dashboardHtml(puzzles) {
    const cards = DASH_CARDS.map(card => _dashCardHtml(card, puzzles)).join('');
    return `
      <div class="dash">
        <div class="dash-cards">${cards}</div>
        ${_dashTableHtml(puzzles)}
      </div>`;
}

function _dashCardHtml(card, puzzles) {
    const inCard = puzzles.filter(p => card.states.includes(p.state));
    const rows = inCard.slice(0, 4).map(p => _dashCardRowHtml(card, p)).join('');
    return `
      <div class="dash-card dash-card-${card.idx}">
        <div class="dash-card-title">${card.title} (${inCard.length})</div>
        <div class="dash-card-rows">${rows}</div>
      </div>`;
}

function _dashCardRowHtml(card, row) {
    const name = escapeHtml(row.name);
    const title = escapeHtml(_dashDisplayTitle(row));
    const meta = [
        fmtMonthDay(row.modified),
        `${row.size} x ${row.size}`,
        _dashRowLengths(row),
    ].filter(Boolean).join(', ');

    let extra = '';
    if (card.idx === 1) {
        const pct = row.fill_pct || 0;
        extra = `
          <div class="progress-wrap">
            <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
            <div class="progress-text">${pct}% filled</div>
          </div>`;
    } else if (card.idx === 2 && row.state === 'finished') {
        extra = `<span class="dash-row-extra">fully clued</span>`;
    } else if (card.idx === 3) {
        const pub = escapeHtml(row.publisher || '');
        if (row.state === 'submitted') {
            extra = `<span class="dash-row-extra">submitted to ${pub}</span>`;
        } else if (row.state === 'published') {
            extra = `<span class="dash-row-extra">published by ${pub}</span>`;
        }
    }

    return `
      <div class="dash-row">
        <div class="dash-row-head">
          <span class="dash-row-title dash-link" data-dash-preview="${name}">${title}</span>
          ${extra}
        </div>
        <div class="dash-row-meta">${escapeHtml(meta)}</div>
      </div>`;
}

// ---------------------------------------------------------------------------
// Bottom half — tabbed list
// ---------------------------------------------------------------------------

function _dashTableHtml(puzzles) {
    const tabs = DASH_TABS.map(tab => {
        const active = tab === DashboardState.activeTab ? ' dash-tab-active' : '';
        return `<button class="dash-tab${active}" data-dash-tab="${tab}">${tab}</button>`;
    }).join('');

    return `
      <div class="dash-table-card">
        <div class="dash-tabs">${tabs}</div>
        <div class="dash-table-scroll">${_dashTableBodyHtml()}</div>
      </div>`;
}

function _dashShowsPublisher(tab) {
    return tab === 'submitted' || tab === 'published' || tab === 'all';
}

function _dashTableBodyHtml() {
    const tab = DashboardState.activeTab;
    const showPub = _dashShowsPublisher(tab);
    const rows = (tab === 'all')
        ? DashboardState.puzzles
        : DashboardState.puzzles.filter(p => p.state === tab);

    const headers = ['State'];
    if (showPub) headers.push('Publisher');
    headers.push('Name', 'Title', 'Size', 'Words', 'Modified');
    const thead = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;

    if (rows.length === 0) {
        return `<table class="dash-table"><thead>${thead}</thead>
          <tbody><tr><td colspan="${headers.length}" class="dash-empty">No puzzles.</td></tr></tbody></table>`;
    }

    const body = rows.map(row => {
        const name = escapeHtml(row.name);
        const options = ALL_STATES.map(s =>
            `<option value="${s}"${s === row.state ? ' selected' : ''}>${s}</option>`).join('');
        const cells = [
            `<td><select class="dash-state-select" data-dash-state="${name}">${options}</select></td>`,
        ];
        if (showPub) cells.push(`<td>${escapeHtml(row.publisher || '')}</td>`);
        cells.push(`<td><span class="dash-link" data-dash-preview="${name}">${name}</span></td>`);
        cells.push(`<td><span class="dash-link" data-dash-preview="${name}">${escapeHtml(_dashDisplayTitle(row))}</span></td>`);
        cells.push(`<td>${row.size} x ${row.size}</td>`);
        cells.push(`<td>${row.word_count}</td>`);
        cells.push(`<td>${fmtMonthDay(row.modified)}</td>`);
        return `<tr>${cells.join('')}</tr>`;
    }).join('');

    return `<table class="dash-table"><thead>${thead}</thead><tbody>${body}</tbody></table>`;
}

// ---------------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------------

function bindDashboardEvents() {
    const root = document.getElementById('lhs');
    if (!root) return;

    // Tab switches — re-render only the table body (cards stay).
    root.querySelectorAll('[data-dash-tab]').forEach(btn => {
        btn.onclick = () => {
            DashboardState.activeTab = btn.getAttribute('data-dash-tab');
            const card = root.querySelector('.dash-table-card');
            if (card) {
                card.querySelector('.dash-tabs').querySelectorAll('.dash-tab').forEach(t => {
                    t.classList.toggle('dash-tab-active',
                        t.getAttribute('data-dash-tab') === DashboardState.activeTab);
                });
                card.querySelector('.dash-table-scroll').innerHTML = _dashTableBodyHtml();
                _bindDashTableBody(root);
            }
        };
    });

    // Name / title click → preview popup.
    root.querySelectorAll('[data-dash-preview]').forEach(el => {
        el.onclick = () => showPuzzlePreview(el.getAttribute('data-dash-preview'));
    });

    _bindDashTableBody(root);
}

function _bindDashTableBody(root) {
    // State dropdowns and preview links inside the (re-rendered) table body.
    root.querySelectorAll('.dash-state-select').forEach(sel => {
        sel.onchange = () => {
            const name = sel.getAttribute('data-dash-state');
            const row = DashboardState.puzzles.find(p => p.name === name);
            openStateDialog(row, sel.value, sel);
        };
    });
    root.querySelectorAll('.dash-table [data-dash-preview]').forEach(el => {
        el.onclick = () => showPuzzlePreview(el.getAttribute('data-dash-preview'));
    });
}

// ---------------------------------------------------------------------------
// State-change dialog
// ---------------------------------------------------------------------------

let _dashStateRevertSelect = null;  // <select> to reset on cancel/error

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
        const resp = await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(row.name)}/state`, body);
        if (resp && resp.error) {
            errEl.textContent = resp.error;
            return;
        }
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

// ---------------------------------------------------------------------------
// Puzzle-preview popup (open-from-dashboard)
// ---------------------------------------------------------------------------

async function showPuzzlePreview(name) {
    const body = document.getElementById('preview-popup-body');
    document.getElementById('preview-popup-title').textContent = name;
    body.innerHTML = '<div class="w3-container w3-padding">Loading preview...</div>';
    showElement('preview-popup');

    let data;
    try {
        data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(name)}/preview`);
    } catch (e) {
        body.innerHTML = `<div class="w3-container w3-padding">Error: ${escapeHtml(e.message)}</div>`;
        return;
    }
    if (data.error) {
        body.innerHTML = `<div class="w3-container w3-padding">Error: ${escapeHtml(data.error)}</div>`;
        return;
    }

    const svgDiv = document.createElement('div');
    svgDiv.style.cssText = 'display:flex;flex-direction:column;align-items:center';
    if (data.svgstr) {
        svgDiv.innerHTML = data.svgstr;
        const svg = svgDiv.querySelector('svg');
        if (svg && data.width) {
            svg.setAttribute('width', data.width);
            svg.setAttribute('height', data.width);
        }
    }
    const heading = document.createElement('div');
    heading.style.cssText = 'margin-top:8px;text-align:center;font-size:13px';
    heading.innerHTML = `<small class="w3-text-gray">${escapeHtml(data.heading || '')}</small>`;
    body.innerHTML = '';
    body.appendChild(svgDiv);
    body.appendChild(heading);

    document.getElementById('preview-popup-cancel').onclick = () => hideElement('preview-popup');
    document.getElementById('preview-popup-close').onclick = () => hideElement('preview-popup');
    document.getElementById('preview-popup-open').onclick = async () => {
        hideElement('preview-popup');
        try {
            await _openPuzzleInEditor(name);
        } catch (e) {
            showMessageLine('Error opening puzzle', 'error', 0);
        }
    };
}
