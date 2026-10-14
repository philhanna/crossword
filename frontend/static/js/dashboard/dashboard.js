// Crossword Puzzle Editor — dashboard view (landing screen)
//
// Renders a four-card summary (top half) and a tabbed, full-width puzzle list
// (bottom half) into the #lhs workspace pane. Data comes from GET /api/dashboard
// in a single round-trip and is cached in DashboardState so tab switches and the
// top cards render client-side without refetching.

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { escapeHtml } from '../core/dom.js';
import { showRequestError } from '../ui/message-line.js';
import { _openPuzzleInEditor } from '../puzzle-file/lifecycle.js';

registerActions({
    'dash-tab':  (el) => _dashSelectTab(el.getAttribute('data-dash-tab')),
    'dash-sort': (el) => _dashSortBy(el.getAttribute('data-dash-sort')),
    'dash-open': (el) => _dashOpenPuzzle(el.getAttribute('data-dash-preview')),
});

export const ALL_STATES = ['draft', 'filled', 'finished', 'submitted', 'published', 'archived'];

const DASH_CARDS = [
    { idx: 1, title: 'IN PROGRESS', states: ['draft'] },
    { idx: 2, title: 'COMPLETED',   states: ['filled', 'finished'] },
    { idx: 3, title: 'SUBMITTED',   states: ['submitted', 'published'] },
    { idx: 4, title: 'ARCHIVED',    states: ['archived'] },
];

const DASH_TABS = ['all', ...ALL_STATES];

export const DashboardState = {
    puzzles: [],          // rows from GET /api/dashboard, modified DESC
    activeTab: 'all',     // active bottom-half tab
    sortKey: null,        // column key to sort by; null keeps the default (modified DESC)
    sortDir: 'asc',       // 'asc' or 'desc'
};

// Bottom-half table columns. `pubOnly` columns only show on publisher tabs.
// `fillOnly` columns only show on tabs that include in-progress completion.
// `val` extracts the sort value; `numeric` columns compare numerically.
const DASH_COLUMNS = [
    { key: 'state',     label: 'State',     pubOnly: false, val: r => r.state || '' },
    { key: 'publisher', label: 'Publisher', pubOnly: true,  val: r => _dashPublisher(r) },
    { key: 'name',      label: 'Name',      pubOnly: false, val: r => r.name || '' },
    { key: 'title',     label: 'Title',     pubOnly: false, val: r => _dashDisplayTitle(r) || '' },
    { key: 'size',      label: 'Size',      pubOnly: false, val: r => r.size, numeric: true },
    { key: 'words',     label: 'Words',     pubOnly: false, val: r => r.word_count, numeric: true },
    { key: 'fill_pct',  label: '% Complete', fillOnly: true, val: r => r.fill_pct || 0, numeric: true },
    { key: 'modified',  label: 'Modified',  pubOnly: false, val: r => r.modified || '' },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function fmtMonthDay(iso) {
    // Parse an ISO-ish timestamp and format as MM/dd/yy. Guards against blanks.
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const yy = String(d.getFullYear() % 100).padStart(2, '0');
    return `${mm}/${dd}/${yy}`;
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

function _dashPublisher(row) {
    // Archived puzzles no longer carry a publisher, so show the one they were
    // last submitted to.
    if (row.state === 'archived') return row.submitted_publisher || '';
    return row.publisher || '';
}

// ---------------------------------------------------------------------------
// Data load
// ---------------------------------------------------------------------------

export async function renderDashboard() {
    let data;
    try {
        data = await apiFetch('GET', '/api/dashboard');
    } catch (e) {
        document.getElementById('rhs').innerHTML = '';
        document.getElementById('lhs').innerHTML =
            `<div class="home-welcome"><p>Error loading dashboard: ${escapeHtml(e.message)}</p></div>`;
        return;
    }
    DashboardState.puzzles = data.puzzles || [];
    document.getElementById('rhs').innerHTML = '';
    document.getElementById('lhs').innerHTML = dashboardHtml(DashboardState.puzzles);
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
      <div class="dash-row" data-contextmenu="dash-row-menu" data-dash-name="${name}">
        <div class="dash-row-head">
          <span class="dash-row-title dash-link" data-action="dash-open" data-dash-preview="${name}">${title}</span>
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
        return `<button class="dash-tab${active}" data-action="dash-tab" data-dash-tab="${tab}">${tab}</button>`;
    }).join('');

    return `
      <div class="dash-table-card">
        <div class="dash-tabs">${tabs}</div>
        <div class="dash-table-scroll">${_dashTableBodyHtml()}</div>
      </div>`;
}

function _dashShowsPublisher(tab) {
    return tab === 'submitted' || tab === 'published' || tab === 'archived' || tab === 'all';
}

function _dashVisibleColumns(tab) {
    const showPub = _dashShowsPublisher(tab);
    const showFill = tab === 'draft' || tab === 'all';
    return DASH_COLUMNS.filter(c =>
        (!c.pubOnly || showPub) &&
        (!c.fillOnly || showFill)
    );
}

function _dashSortRows(rows) {
    // Sort a copy of `rows` by the active sort column; null key keeps load order.
    const key = DashboardState.sortKey;
    if (!key) return rows;
    const col = DASH_COLUMNS.find(c => c.key === key);
    if (!col) return rows;
    const dir = DashboardState.sortDir === 'desc' ? -1 : 1;
    return rows.slice().sort((a, b) => {
        const av = col.val(a), bv = col.val(b);
        const cmp = col.numeric
            ? (av || 0) - (bv || 0)
            : String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' });
        return cmp * dir;
    });
}

function _dashTableBodyHtml() {
    const tab = DashboardState.activeTab;
    let rows = (tab === 'all')
        ? DashboardState.puzzles
        : DashboardState.puzzles.filter(p => p.state === tab);
    rows = _dashSortRows(rows);

    const cols = _dashVisibleColumns(tab);
    const thead = `<tr>${cols.map(c => {
        let ind = '';
        if (DashboardState.sortKey === c.key) {
            ind = DashboardState.sortDir === 'desc' ? ' ▼' : ' ▲';
        }
        return `<th class="dash-sortable" data-action="dash-sort" data-dash-sort="${c.key}">${c.label}${ind}</th>`;
    }).join('')}</tr>`;

    if (rows.length === 0) {
        return `<table class="dash-table"><thead>${thead}</thead>
          <tbody><tr><td colspan="${cols.length}" class="dash-empty">No puzzles.</td></tr></tbody></table>`;
    }

    const body = rows.map(row => {
        const name = escapeHtml(row.name);
        const showPub = _dashShowsPublisher(tab);
        const showFill = tab === 'draft' || tab === 'all';
        const options = ALL_STATES.map(s =>
            `<option value="${s}"${s === row.state ? ' selected' : ''}>${s}</option>`).join('');
        const cells = [
            `<td><select class="dash-state-select" data-change="dash-state" data-dash-state="${name}">${options}</select></td>`,
        ];
        if (showPub) cells.push(`<td>${escapeHtml(_dashPublisher(row))}</td>`);
        cells.push(`<td><span class="dash-link" data-action="dash-open" data-dash-preview="${name}">${name}</span></td>`);
        cells.push(`<td><span class="dash-link" data-action="dash-open" data-dash-preview="${name}">${escapeHtml(_dashDisplayTitle(row))}</span></td>`);
        cells.push(`<td>${row.size} x ${row.size}</td>`);
        cells.push(`<td>${row.word_count}</td>`);
        if (showFill) cells.push(`<td>${row.fill_pct || 0}%</td>`);
        cells.push(`<td>${fmtMonthDay(row.modified)}</td>`);
        return `<tr data-contextmenu="dash-row-menu" data-dash-name="${name}">${cells.join('')}</tr>`;
    }).join('');

    return `<table class="dash-table"><thead>${thead}</thead><tbody>${body}</tbody></table>`;
}

// ---------------------------------------------------------------------------
// Table re-render (tab switches and sorting redraw only the table; cards stay)
// ---------------------------------------------------------------------------

function _dashSelectTab(tab) {
    DashboardState.activeTab = tab;
    document.querySelectorAll('#lhs .dash-tab').forEach(t => {
        t.classList.toggle('dash-tab-active', t.getAttribute('data-dash-tab') === tab);
    });
    _dashRedrawTable();
}

function _dashSortBy(key) {
    // Clicking the active column flips direction
    if (DashboardState.sortKey === key) {
        DashboardState.sortDir = DashboardState.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
        DashboardState.sortKey = key;
        DashboardState.sortDir = 'asc';
    }
    _dashRedrawTable();
}

function _dashRedrawTable() {
    const scroll = document.querySelector('#lhs .dash-table-scroll');
    if (scroll) scroll.innerHTML = _dashTableBodyHtml();
}

// ---------------------------------------------------------------------------
// Open-from-dashboard
// ---------------------------------------------------------------------------

async function _dashOpenPuzzle(name) {
    try {
        await _openPuzzleInEditor(name);
    } catch (e) {
        showRequestError('Error opening puzzle', e);
    }
}
