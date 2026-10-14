// Crossword Puzzle Editor — the puzzle chooser: a paged list of grid previews

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { escapeHtml, hideElement, showElement } from '../core/dom.js';
import { showMessageLine } from './message-line.js';

const CHOOSER_PAGES = {
    first: () => chPageFirst(),
    prev:  () => chPagePrev(),
    next:  () => chPageNext(),
    last:  () => chPageLast(),
};

registerActions({
    'chooser-sort':         (el) => chSetSort(el.value),
    'chooser-state-filter': (el) => chSetPuzzleStateFilter(el.value),
    'chooser-page':         (el) => CHOOSER_PAGES[el.dataset.page](),
});

const CH_PAGE_SIZE = 5;

// The open chooser. previews: one per puzzle, from GET <apiPrefix>/<name>/preview.
// loadItems(state), when given, lists the names to show and is called again
// whenever the state filter changes; onSelect(name) runs on a click.
const chooser = {
    previews: [],
    page: 0,
    onSelect: null,
    sortOrder: 'recent',
    loadItems: null,
    emptyMessage: 'No items found.',
    stateFilter: 'all',
    apiPrefix: '',
};

export async function showPreviewChooser(title, names, apiPrefix, onSelect, options = {}) {
    chooser.previews  = [];
    chooser.page      = 0;
    chooser.onSelect  = onSelect;
    chooser.sortOrder = 'recent';
    chooser.loadItems = options.loadItems || null;
    chooser.emptyMessage = options.emptyMessage || 'No items found.';
    chooser.stateFilter = options.initialStateFilter || 'all';
    chooser.apiPrefix = apiPrefix;
    document.querySelector('input[name="ch-sort"][value="recent"]').checked = true;

    document.getElementById('ch-title').innerHTML = title;
    const listEl = document.getElementById('ch-list');
    const stateFilterWrap = document.getElementById('ch-state-filter-wrap');
    const stateFilter = document.getElementById('ch-state-filter');
    stateFilterWrap.style.display = options.stateFilterEnabled ? 'inline-flex' : 'none';
    stateFilter.value = chooser.stateFilter;
    listEl.innerHTML = '<div class="panel-message">Loading previews...</div>';
    document.getElementById('ch-pagination').style.display = 'none';
    showElement('ch');

    if (chooser.loadItems) {
        await _chReload();
        return;
    }

    chooser.previews = await _chLoadPreviewsFromNames(names, apiPrefix);
    _chRender();
}

async function _chReload() {
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '<div class="panel-message">Loading previews...</div>';
    document.getElementById('ch-pagination').style.display = 'none';

    const names = await chooser.loadItems(chooser.stateFilter);
    chooser.previews = await _chLoadPreviewsFromNames(names, chooser.apiPrefix);
    _chRender();
}

async function _chLoadPreviewsFromNames(names, apiPrefix) {
    return await Promise.all(
        names.map(name =>
            apiFetch('GET', `${apiPrefix}/${encodeURIComponent(name)}/preview`)
                .catch(() => ({ name, heading: name, svgstr: '', error: true }))
        )
    );
}

function _chRender() {
    const listEl    = document.getElementById('ch-list');
    const pageDiv   = document.getElementById('ch-pagination');
    const firstBtn  = document.getElementById('ch-page-first');
    const prevBtn   = document.getElementById('ch-page-prev');
    const nextBtn   = document.getElementById('ch-page-next');
    const lastBtn   = document.getElementById('ch-page-last');
    const labelEl   = document.getElementById('ch-page-label');

    const ordered   = chooser.sortOrder === 'alpha'
        ? [...chooser.previews].sort((a, b) => a.name.localeCompare(b.name))
        : chooser.previews;
    const total     = ordered.length;
    if (total === 0) {
        listEl.innerHTML = `<div class="panel-message">${escapeHtml(chooser.emptyMessage)}</div>`;
        pageDiv.style.display = 'none';
        return;
    }
    const pageStart = chooser.page * CH_PAGE_SIZE;
    const pageEnd   = Math.min(pageStart + CH_PAGE_SIZE, total);
    const pageItems = ordered.slice(pageStart, pageEnd);

    listEl.innerHTML = '';
    for (const p of pageItems) {
        const card = document.createElement('div');
        card.style.cssText = 'display:flex;flex-direction:column;align-items:center;cursor:pointer;padding:8px;border:1px solid #ddd;border-radius:4px;width:160px;flex-shrink:0';
        card.onmouseover = () => card.style.background = '#f1f1f1';
        card.onmouseout  = () => card.style.background = '';
        card.onclick     = () => { hideElement('ch'); chooser.onSelect(p.name); };

        const svgDiv = document.createElement('div');
        svgDiv.style.cssText = 'width:150px;height:150px;overflow:hidden';
        if (p.svgstr) {
            svgDiv.innerHTML = p.svgstr;
            const svg = svgDiv.querySelector('svg');
            if (svg) { svg.setAttribute('width', '150'); svg.setAttribute('height', '150'); }
        }

        const textDiv = document.createElement('div');
        textDiv.style.cssText = 'margin-top:6px;text-align:center;font-size:13px;word-break:break-word;max-width:150px';
        textDiv.innerHTML = `<b>${escapeHtml(p.name)}</b><br><small class="chooser-heading">${escapeHtml(p.heading || '')}</small>`;

        card.appendChild(svgDiv);
        card.appendChild(textDiv);
        listEl.appendChild(card);
    }

    if (total > CH_PAGE_SIZE) {
        const lastPage = Math.ceil(total / CH_PAGE_SIZE) - 1;
        labelEl.textContent    = `${pageStart + 1}–${pageEnd} of ${total}`;
        firstBtn.disabled      = chooser.page === 0;
        prevBtn.disabled       = chooser.page === 0;
        nextBtn.disabled       = pageEnd >= total;
        lastBtn.disabled       = chooser.page === lastPage;
        pageDiv.style.display  = 'flex';
    } else {
        pageDiv.style.display = 'none';
    }
}

function chSetSort(order) { chooser.sortOrder = order; chooser.page = 0; _chRender(); }

async function chSetPuzzleStateFilter(value) {
    chooser.stateFilter = value;
    chooser.page = 0;
    if (!chooser.loadItems) return;
    try {
        await _chReload();
    } catch (e) {
        showMessageLine(`Error listing puzzles: ${e.message}`, 'error', 0);
    }
}

function chPageFirst() { chooser.page = 0; _chRender(); }

function chPagePrev()  { if (chooser.page > 0) { chooser.page--; _chRender(); } }

function chPageNext()  { if ((chooser.page + 1) * CH_PAGE_SIZE < chooser.previews.length) { chooser.page++; _chRender(); } }

function chPageLast()  { chooser.page = Math.ceil(chooser.previews.length / CH_PAGE_SIZE) - 1; _chRender(); }
