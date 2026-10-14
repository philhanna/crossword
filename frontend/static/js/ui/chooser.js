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

let _chPreviews  = [];

let _chPage      = 0;

let _chOnSelect  = null;

let _chSortOrder = 'recent';

let _chLoadItems = null;

let _chEmptyMessage = 'No items found.';

let _chStateFilter = 'all';

let _chApiPrefix = '';

export async function showPreviewChooser(title, names, apiPrefix, onSelect, options = {}) {
    _chPreviews  = [];
    _chPage      = 0;
    _chOnSelect  = onSelect;
    _chSortOrder = 'recent';
    _chLoadItems = options.loadItems || null;
    _chEmptyMessage = options.emptyMessage || 'No items found.';
    _chStateFilter = options.initialStateFilter || 'all';
    _chApiPrefix = apiPrefix;
    document.querySelector('input[name="ch-sort"][value="recent"]').checked = true;

    document.getElementById('ch-title').innerHTML = title;
    const listEl = document.getElementById('ch-list');
    const stateFilterWrap = document.getElementById('ch-state-filter-wrap');
    const stateFilter = document.getElementById('ch-state-filter');
    stateFilterWrap.style.display = options.stateFilterEnabled ? 'inline-flex' : 'none';
    stateFilter.value = _chStateFilter;
    listEl.innerHTML = '<div class="w3-container w3-padding">Loading previews...</div>';
    document.getElementById('ch-pagination').style.display = 'none';
    showElement('ch');

    if (_chLoadItems) {
        await _chReload();
        return;
    }

    _chPreviews = await _chLoadPreviewsFromNames(names, apiPrefix);
    _chRender();
}

async function _chReload() {
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '<div class="w3-container w3-padding">Loading previews...</div>';
    document.getElementById('ch-pagination').style.display = 'none';

    const names = await _chLoadItems(_chStateFilter);
    _chPreviews = await _chLoadPreviewsFromNames(names, _chApiPrefix);
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

    const ordered   = _chSortOrder === 'alpha'
        ? [..._chPreviews].sort((a, b) => a.name.localeCompare(b.name))
        : _chPreviews;
    const total     = ordered.length;
    if (total === 0) {
        listEl.innerHTML = `<div class="w3-container w3-padding">${escapeHtml(_chEmptyMessage)}</div>`;
        pageDiv.style.display = 'none';
        return;
    }
    const pageStart = _chPage * CH_PAGE_SIZE;
    const pageEnd   = Math.min(pageStart + CH_PAGE_SIZE, total);
    const pageItems = ordered.slice(pageStart, pageEnd);

    listEl.innerHTML = '';
    for (const p of pageItems) {
        const card = document.createElement('div');
        card.style.cssText = 'display:flex;flex-direction:column;align-items:center;cursor:pointer;padding:8px;border:1px solid #ddd;border-radius:4px;width:160px;flex-shrink:0';
        card.onmouseover = () => card.style.background = '#f1f1f1';
        card.onmouseout  = () => card.style.background = '';
        card.onclick     = () => { hideElement('ch'); _chOnSelect(p.name); };

        const svgDiv = document.createElement('div');
        svgDiv.style.cssText = 'width:150px;height:150px;overflow:hidden';
        if (p.svgstr) {
            svgDiv.innerHTML = p.svgstr;
            const svg = svgDiv.querySelector('svg');
            if (svg) { svg.setAttribute('width', '150'); svg.setAttribute('height', '150'); }
        }

        const textDiv = document.createElement('div');
        textDiv.style.cssText = 'margin-top:6px;text-align:center;font-size:13px;word-break:break-word;max-width:150px';
        textDiv.innerHTML = `<b>${escapeHtml(p.name)}</b><br><small class="w3-text-gray">${escapeHtml(p.heading || '')}</small>`;

        card.appendChild(svgDiv);
        card.appendChild(textDiv);
        listEl.appendChild(card);
    }

    if (total > CH_PAGE_SIZE) {
        const lastPage = Math.ceil(total / CH_PAGE_SIZE) - 1;
        labelEl.textContent    = `${pageStart + 1}–${pageEnd} of ${total}`;
        firstBtn.disabled      = _chPage === 0;
        prevBtn.disabled       = _chPage === 0;
        nextBtn.disabled       = pageEnd >= total;
        lastBtn.disabled       = _chPage === lastPage;
        pageDiv.style.display  = 'flex';
    } else {
        pageDiv.style.display = 'none';
    }
}

function chSetSort(order) { _chSortOrder = order; _chPage = 0; _chRender(); }

async function chSetPuzzleStateFilter(value) {
    _chStateFilter = value;
    _chPage = 0;
    if (!_chLoadItems) return;
    try {
        await _chReload();
    } catch (e) {
        showMessageLine(`Error listing puzzles: ${e.message}`, 'error', 0);
    }
}

function chPageFirst() { _chPage = 0; _chRender(); }

function chPagePrev()  { if (_chPage > 0) { _chPage--; _chRender(); } }

function chPageNext()  { if ((_chPage + 1) * CH_PAGE_SIZE < _chPreviews.length) { _chPage++; _chRender(); } }

function chPageLast()  { _chPage = Math.ceil(_chPreviews.length / CH_PAGE_SIZE) - 1; _chRender(); }
