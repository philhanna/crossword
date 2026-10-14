// Crossword Puzzle Editor — puzzle editor rendering, grid ops, undo/redo

import { registerActions } from './core/actions.js';
import { AppState, BOXSIZE, MESSAGE_LINE_TIMEOUT_MS } from './state.js';
import { buildPuzzleSvg } from './svg.js';
import {
    _hash, apiFetch, escapeHtml, inputBox, messageBox, showMessageLine,
    showRequestError, updateMenu,
} from './ui.js';
import {
    _focusPuzzleSvg, _getPuzzleWord, _getSelectedWordCursorIdx,
    _isWordEditorOpen, _peCommitWord, _peKeydown, _peOutsideMousedown,
    _refreshSelectedWordFromPuzzleData, closeWordEditor,
    completeSelectedWordEdit, handlePuzzleClick, openWordEditor,
    renderWordEditorPanel,
} from './word-editor.js';

registerActions({
    'puzzle-title':  () => do_puzzle_title(),
    'puzzle-clear':  () => do_puzzle_clear(),
    'puzzle-undo':   () => do_puzzle_undo(),
    'puzzle-redo':   () => do_puzzle_redo(),
    'puzzle-stats':  () => do_puzzle_stats(),
    'puzzle-mode':   () => do_switch_to_puzzle_mode(),
    'grid-mode':     () => do_switch_to_grid_mode(),
    'grid-rotate':   () => do_puzzle_rotate_grid(),
    'grid-generate': () => do_puzzle_generate_grid(),
    'fill-order':    () => do_puzzle_fill_order(),

    // Side panels
    'open-word':      (el) => _openWordFromPanel(Number(el.dataset.seq), el.dataset.direction),
    'sidebar-tab':    (el) => switchSidebarTab(el.dataset.tab),
    'clue-direction': (el) => switchClueDirection(el.dataset.direction),
    'clue-edit':      (el) => startInlineClueEdit(Number(el.dataset.seq), el.dataset.direction),
    'stats-subtab':   (el) => setStatsSubTab(el.dataset.tab),
});

// ---------------------------------------------------------------------------
// Puzzle editor — rendering
// ---------------------------------------------------------------------------

export function _currentEditorMode() {
    return (AppState.puzzleData && AppState.puzzleData.mode) || 'puzzle';
}

export function renderPuzzleEditor() {
    document.removeEventListener('keydown', _peKeydown);
    document.removeEventListener('mousedown', _peOutsideMousedown);
    if (_currentEditorMode() === 'puzzle') {
        document.addEventListener('keydown', _peKeydown);
        document.addEventListener('mousedown', _peOutsideMousedown);
    }
    updateMenu();
    updateAppBarPuzzleInfo();
    renderActionBar();
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

export function renderPuzzleEditorLhs() {
    const pd   = AppState.puzzleData;
    const mode = _currentEditorMode();

    const sw  = AppState.selectedWord;
    const editState = mode === 'puzzle' && _isWordEditorOpen() && sw
        ? { cells: sw.cells, cursorIdx: _getSelectedWordCursorIdx(), text: sw.draftText || '' }
        : mode === 'puzzle' && sw
        ? { cells: sw.cells, cursorIdx: _getSelectedWordCursorIdx(), text: sw.draftText }
        : null;
    const clickHelp = mode === 'grid'
        ? `<div class="kb-hints">
             <span class="kb-hint"><kbd>Click</kbd> toggle cell</span>
             <span class="kb-hint"><kbd>Rotate</kbd> or <kbd>Generate</kbd> in toolbar</span>
           </div>`
        : _isWordEditorOpen()
        ? `<div class="kb-hints">
             <span class="kb-hint"><kbd>Enter</kbd> suggest words</span>
             <span class="kb-hint"><kbd>Esc</kbd> cancel</span>
           </div>`
        : `<div class="kb-hints">
             <span class="kb-hint"><kbd>← → ↑ ↓</kbd> move</span>
             <span class="kb-hint"><kbd>Tab</kbd> next word</span>
             <span class="kb-hint"><kbd>A–Z</kbd> fill</span>
             <span class="kb-hint"><kbd>⌫</kbd> clear</span>
             <span class="kb-hint"><kbd>Esc</kbd> deselect</span>
           </div>`;

    updateAppBarPuzzleInfo();
    const puzzleTitle = pd && pd.puzzle.title ? pd.puzzle.title : '';
    const titleHtml = puzzleTitle
        ? `<div class="puzzle-title-display" data-action="puzzle-title" style="cursor:pointer">${escapeHtml(puzzleTitle)}</div>`
        : '';
    document.getElementById('lhs').innerHTML = `
<div class="grid-canvas-frame">
  ${titleHtml}
  <div id="puzzle-svg-container">
    ${pd ? buildPuzzleSvg(pd, editState) : ''}
  </div>
</div>
${clickHelp}`;

    const svg = document.getElementById('puzzle-svg');
    if (svg && mode === 'puzzle') svg.addEventListener('click', handlePuzzleClick);
    if (svg && mode === 'grid') svg.addEventListener('click', handleGridModeClick);
    if (mode === 'puzzle' && sw && !_isWordEditorOpen()) _focusPuzzleSvg();
    _updatePuzzleUndoRedo();
}

export function updateAppBarPuzzleInfo() {
    const el = document.getElementById('app-bar-puzzle-info');
    if (!el) return;
    if (AppState.view !== 'editor' || !AppState.puzzleData) {
        el.innerHTML = '';
        return;
    }
    const name = AppState.puzzleName || '(No name)';
    const mode = _currentEditorMode();
    const badgeClass = mode === 'grid' ? 'mode-badge mode-badge-grid' : 'mode-badge mode-badge-puzzle';
    const badgeText  = mode === 'grid' ? 'Grid Mode' : 'Puzzle Mode';
    const isDirty = AppState.puzzleSavedHash !== null &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    const saveHtml = isDirty
        ? `<span class="save-status save-status-dirty">● Unsaved</span>`
        : `<span class="save-status save-status-saved">✓ Saved</span>`;
    const stateHtml = AppState.puzzleState
        ? `<span class="state-label">State: ${escapeHtml(AppState.puzzleState)}</span>`
        : '';
    el.innerHTML =
        `<span class="puzzle-info-name">${escapeHtml(name)}</span>` +
        `<span class="${badgeClass}">${badgeText}</span>` +
        stateHtml +
        saveHtml;
}

export function renderActionBar() {
    const ab = document.getElementById('action-bar');
    if (!ab) return;
    if (AppState.view !== 'editor') {
        ab.style.display = 'none';
        document.body.classList.remove('editor-open');
        return;
    }
    ab.style.display = 'flex';
    document.body.classList.add('editor-open');

    const pd   = AppState.puzzleData;
    const mode = _currentEditorMode();
    const size = pd ? pd.grid.size : 0;
    const genDisabled = (size >= 9 && size % 2 === 1) ? '' : ' w3-disabled';
    const fillOrderDisabled = AppState.fillOrderLoading ? ' w3-disabled' : '';
    const fillOrderDisabledAttr = AppState.fillOrderLoading ? ' disabled' : '';
    const closeDisabled = _isWordEditorOpen() ? ' w3-disabled' : '';
    const closeDisabledAttr = _isWordEditorOpen() ? ' disabled' : '';
    const hasLockedWords = !!(pd && pd.puzzle.words.some(w => w.locked));
    const gridModeDisabled = hasLockedWords ? ' w3-disabled' : '';
    const gridModeDisabledAttr = hasLockedWords ? ' disabled' : '';
    const gridModeTitle = hasLockedWords ? ' title="Unlock all words before switching to Grid Mode"' : '';

    const modeSpecific = mode === 'grid' ? `
<div class="ab-group">
  <button class="ab-btn ab-mode-btn" data-action="puzzle-mode">Puzzle Mode</button>
  <button class="ab-btn ab-mode-btn ab-mode-active">Grid Mode</button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button class="ab-btn" data-action="grid-rotate">
    <i class="material-icons">rotate_right</i><span>Rotate</span>
  </button>
  <button id="puzzle-generate-btn" class="ab-btn${genDisabled}" data-action="grid-generate">
    <i class="material-icons">casino</i><span>Generate</span>
  </button>
  <button class="ab-btn" data-action="puzzle-stats">
    <i class="material-icons">info</i><span>Stats</span>
  </button>
</div>` : `
<div class="ab-group">
  <button class="ab-btn ab-mode-btn ab-mode-active">Puzzle Mode</button>
  <button class="ab-btn ab-mode-btn${gridModeDisabled}" data-action="grid-mode"${gridModeDisabledAttr}${gridModeTitle}>Grid Mode</button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button id="puzzle-editword-btn" class="ab-btn" data-action="edit-word">
    <i class="material-icons">edit</i><span>Edit word</span>
  </button>
  <button id="puzzle-fill-order-btn" class="ab-btn${fillOrderDisabled}" data-action="fill-order"${fillOrderDisabledAttr}>
    <i class="material-icons">format_list_numbered</i><span>Fill order</span>
  </button>
  <button class="ab-btn" data-action="puzzle-stats">
    <i class="material-icons">info</i><span>Stats</span>
  </button>
</div>
<div class="ab-group ab-group-right">
  <button id="puzzle-clear-btn" class="ab-btn" data-action="puzzle-clear">
    <i class="material-icons">clear_all</i><span>Clear</span>
  </button>
  <button id="puzzle-delete-btn" class="ab-btn" data-action="puzzle-delete-current">
    <i class="material-icons">delete</i><span>Delete</span>
  </button>
</div>`;

    ab.innerHTML = `
<div class="ab-group">
  <button class="ab-btn" data-action="puzzle-save">
    <i class="material-icons">save</i><span>Save</span>
  </button>
  <button id="puzzle-close-btn" class="ab-btn${closeDisabled}" data-action="puzzle-close"${closeDisabledAttr}>
    <i class="material-icons">close</i><span>Close</span>
  </button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button id="puzzle-undo-btn" class="ab-btn" data-action="puzzle-undo">
    <i class="material-icons">undo</i><span>Undo</span>
  </button>
  <button id="puzzle-redo-btn" class="ab-btn" data-action="puzzle-redo">
    <i class="material-icons">redo</i><span>Redo</span>
  </button>
</div>
<div class="ab-divider"></div>
${modeSpecific}`;
}

export function renderPuzzleEditorRhs() {
    const mode      = _currentEditorMode();
    const activeTab = _getActiveTab(mode);
    const tabList   = mode === 'grid' ? ['grid', 'stats'] : ['word', 'clues'];
    let contentHtml;

    if (mode === 'grid') {
        contentHtml = activeTab === 'stats' && AppState._statsData
            ? renderStatsPanel(AppState._statsData)
            : renderGridModePanel();
    } else {
        switch (activeTab) {
            case 'word':
                contentHtml = _isWordEditorOpen()
                    ? renderWordEditorPanel()
                    : `<div class="sidebar-empty">Select a word in the grid, then click <b>Edit word</b> to edit it here.</div>`;
                break;
            case 'stats':
                contentHtml = AppState._statsData
                    ? renderStatsPanel(AppState._statsData)
                    : `<div class="sidebar-empty">Loading stats…</div>`;
                break;
            case 'fill-order': {
                const _foData = AppState._fillOrderCache &&
                    AppState._fillOrderCache.get(_cellLettersKey(AppState.puzzleData));
                contentHtml = _foData
                    ? renderFillOrderPanel(_foData)
                    : `<div class="sidebar-empty">Loading fill order…</div>`;
                break;
            }
            default:
                contentHtml = renderClues();
        }
    }

    // Remember where the clue list was scrolled so a re-render doesn't lose it
    const oldList   = document.getElementById('clue-list-active');
    const oldScroll = oldList ? oldList.scrollTop : null;

    document.getElementById('rhs').innerHTML =
        renderSidebarTabs(activeTab, tabList) +
        `<div class="sidebar-content">${contentHtml}</div>`;

    if (oldScroll !== null && _clueDirection === _lastClueDirection) {
        _restoreCluesScroll(oldScroll);
    } else {
        _scrollCluesToFirstMissing();
    }
    _lastClueDirection = _clueDirection;
}

function _restoreCluesScroll(scrollTop) {
    const list = document.getElementById('clue-list-active');
    if (!list) return;
    list.scrollTop = scrollTop;

    // Keep the selected row (e.g. the word just clued) in view
    const selected = list.querySelector('.clue-row-selected');
    if (selected) selected.scrollIntoView({ block: 'nearest' });
}

function _getActiveTab(mode) {
    if (mode === 'grid') return AppState.sidebarTab === 'stats' ? 'stats' : 'grid';
    if (_isWordEditorOpen()) return 'word';
    return AppState.sidebarTab || 'clues';
}

function renderSidebarTabs(activeTab, tabs) {
    const labels = { clues: 'Clues', word: 'Word', stats: 'Stats', 'fill-order': 'Fill Order', grid: 'Grid' };
    return `<div class="sidebar-tabs">${
        tabs.map(t =>
            `<button class="sidebar-tab${t === activeTab ? ' sidebar-tab-active' : ''}"
                     data-action="sidebar-tab" data-tab="${t}">${labels[t]}</button>`
        ).join('')
    }</div>`;
}

async function switchSidebarTab(tab) {
    if (tab === 'clues' && _isWordEditorOpen()) {
        closeWordEditor();
        return;
    }
    if (tab === 'stats' && !AppState._statsData) {
        await do_puzzle_stats(); return;
    }
    if (tab === 'fill-order' && !(AppState._fillOrderCache &&
            AppState._fillOrderCache.has(_cellLettersKey(AppState.puzzleData)))) {
        await do_puzzle_fill_order(); return;
    }
    if (tab === 'word' && !_isWordEditorOpen() && AppState.selectedWord) {
        await openWordEditor(AppState.selectedWord.seq, AppState.selectedWord.direction); return;
    }
    AppState.sidebarTab     = tab;
    AppState.showingStats   = (tab === 'stats');
    AppState.showingFillOrder = (tab === 'fill-order');
    renderPuzzleEditorRhs();
}

let _clueDirection     = 'across'; // active clue direction in Clues tab
let _lastClueDirection = null;     // direction shown by the previous render

function switchClueDirection(dir) {
    _clueDirection = dir;
    renderPuzzleEditorRhs();
}

function _scrollCluesToFirstMissing() {
    const list = document.getElementById('clue-list-active');
    if (!list) return;
    const first = list.querySelector('[data-noclue]');
    if (!first) return;
    // Scroll so the first unclued row sits in the top third of the list
    const rowTop = first.getBoundingClientRect().top - list.getBoundingClientRect().top + list.scrollTop;
    list.scrollTop = Math.max(0, rowTop - list.clientHeight / 3);
}

function renderGridModePanel() {
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

function renderClues() {
    if (!AppState.puzzleData) return '';
    const words    = AppState.puzzleData.puzzle.words;
    const across   = words.filter(w => w.direction === 'across').sort((a, b) => a.seq - b.seq);
    const down     = words.filter(w => w.direction === 'down').sort((a, b) => a.seq - b.seq);
    const selected = AppState.selectedWord;
    const dir      = _clueDirection;
    const list     = dir === 'across' ? across : down;

    const acrossClued = across.filter(w => w.clue).length;
    const downClued   = down.filter(w => w.clue).length;
    const countLabel  = dir === 'across'
        ? `${acrossClued}/${across.length} clued`
        : `${downClued}/${down.length} clued`;
    const countClass  = (dir === 'across' ? acrossClued === across.length : downClued === down.length)
        ? 'clue-count-ok' : 'clue-count-bad';

    const items = list.map(w => {
        const isSelected = selected && selected.seq === w.seq && selected.direction === dir;
        const hasMissing = !w.clue;
        const editWord = `data-action="edit-word" data-seq="${w.seq}" data-direction="${dir}"`;
        return `<tr class="clue-row${isSelected ? ' clue-row-selected' : ''}"${hasMissing ? ' data-noclue="1"' : ''}>` +
            `<td class="clue-num" ${editWord}>${w.seq}</td>` +
            `<td class="clue-answer" ${editWord}>${escapeHtml((w.answer || '').replace(/ /g, '.'))}</td>` +
            `<td class="clue-text${hasMissing ? ' clue-text-missing' : ''}" data-seq="${w.seq}"` +
            ` data-action="clue-edit" data-direction="${dir}">` +
            (hasMissing ? '<span class="clue-missing-dot"></span>' : '') +
            escapeHtml(w.clue || 'No clue') +
            `</td>` +
            `</tr>`;
    }).join('');

    return `
<div class="clue-toolbar">
  <div class="clue-dir-toggle">
    <button class="clue-dir-btn${dir === 'across' ? ' clue-dir-btn-active' : ''}" data-action="clue-direction" data-direction="across">Across</button>
    <button class="clue-dir-btn${dir === 'down'   ? ' clue-dir-btn-active' : ''}" data-action="clue-direction" data-direction="down">Down</button>
  </div>
  <span class="clue-count ${countClass}">${countLabel}</span>
</div>
<div id="clue-list-active" class="clue-list-new">
  <table class="clue-table"><tbody>${items}</tbody></table>
</div>`;
}

let _inlineClueSave = Promise.resolve();  // pending save from the last inline clue edit

async function startInlineClueEdit(seq, direction) {
    if (_currentEditorMode() !== 'puzzle') return;
    await _inlineClueSave;  // a blur-triggered save re-renders the list; let it finish first
    const word = _getPuzzleWord(seq, direction);
    if (!word) return;
    if (!word.answer || word.answer.includes(' ')) {
        showMessageLine('Fill in the word before giving it a clue', 'error');
        return;
    }
    const result = await completeSelectedWordEdit({ nextSelection: { seq, direction } });
    if (result.error) return;

    const cell = document.querySelector(`#clue-list-active .clue-text[data-seq="${seq}"]`);
    if (!cell) return;
    cell.classList.remove('clue-text-missing');

    // Clicks inside the text box must not start another edit
    cell.removeAttribute('data-action');
    cell.innerHTML = '';
    const input = document.createElement('input');
    input.type        = 'text';
    input.className   = 'clue-inline-input';
    input.value       = word.clue || '';
    input.placeholder = 'Enter clue…';
    cell.appendChild(input);
    input.focus();

    let finished = false;
    const finish = (save) => {
        if (finished) return;
        finished = true;
        if (save) {
            _inlineClueSave = _saveInlineClue(seq, direction, input.value.trim());
        } else {
            renderPuzzleEditorRhs();
        }
    };
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter')  { e.preventDefault(); finish(true); }
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); finish(false); }
    });
    input.addEventListener('blur', () => finish(true));
}

async function _saveInlineClue(seq, direction, clue) {
    const sw = AppState.selectedWord;
    if (!sw || sw.seq !== seq || sw.direction !== direction) {
        renderPuzzleEditorRhs();
        return;
    }
    sw.draftClue = clue;
    const result = await completeSelectedWordEdit();
    if (!result.error) renderPuzzleEditor();
}

// ---------------------------------------------------------------------------
// Stats and fill-order panels
// ---------------------------------------------------------------------------

function renderStatsPanel(stats) {
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

// Open the word editor on a word picked from the stats or fill-order panel
async function _openWordFromPanel(seq, dir) {
    const result = await completeSelectedWordEdit({
        nextSelection: { seq, direction: dir }
    });
    if (result.error) return;
    await openWordEditor(seq, dir);
}

function setStatsSubTab(tab) {
    AppState.statsSubTab = (tab === 'words') ? 'words' : 'slots';
    renderPuzzleEditorRhs();
}

function _cellLettersKey(puzzleData) {
    if (!puzzleData?.puzzle?.cells) return '';
    return Object.entries(puzzleData.puzzle.cells)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([idx, cell]) => `${idx}:${cell.letter ?? ''}`)
        .join('|');
}

function renderFillOrderPanel(data) {
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

async function _refreshPuzzleStatsIfVisible() {
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

async function _refreshFillOrderIfVisible() {
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

// ---------------------------------------------------------------------------
// Grid mode operations
// ---------------------------------------------------------------------------

async function _applyGridModeUpdate(data) {
    AppState.puzzleData   = data;
    AppState.selectedWord = null;
    AppState.gridStructureChanged = true;
    renderPuzzleEditor();
    await _refreshPuzzleStatsIfVisible();
    await _refreshFillOrderIfVisible();
}

async function handleGridModeClick(event) {
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

// ---------------------------------------------------------------------------
// Undo / redo
// ---------------------------------------------------------------------------

export function _updatePuzzleUndoRedo() {
    const pd      = AppState.puzzleData;
    const mode    = _currentEditorMode();
    const editing = _isWordEditorOpen();
    const ub      = document.getElementById('puzzle-undo-btn');
    const rb      = document.getElementById('puzzle-redo-btn');
    if (!ub || !rb) return;
    const canUndo = !pd ? false : (mode === 'grid' ? !!pd.grid_can_undo : !!pd.puzzle_can_undo);
    const canRedo = !pd ? false : (mode === 'grid' ? !!pd.grid_can_redo : !!pd.puzzle_can_redo);
    ub.classList.toggle('w3-disabled', editing || !canUndo);
    rb.classList.toggle('w3-disabled', editing || !canRedo);
    _updatePuzzleToolbar();
}

export function _updatePuzzleToolbar() {
    const mode = _currentEditorMode();
    const eb = document.getElementById('puzzle-editword-btn');
    const cb = document.getElementById('puzzle-close-btn');
    const db = document.getElementById('puzzle-delete-btn');
    if (eb) {
        eb.classList.toggle('w3-disabled', mode !== 'puzzle' || !AppState.selectedWord || _isWordEditorOpen());
    }
    if (db) {
        db.classList.toggle('w3-disabled', _isWordEditorOpen());
        db.disabled = _isWordEditorOpen();
    }
    if (cb) {
        cb.classList.toggle('w3-disabled', _isWordEditorOpen());
        cb.disabled = _isWordEditorOpen();
    }
}

async function do_puzzle_undo() { await _puzzleUndoRedo('undo'); }
async function do_puzzle_redo() { await _puzzleUndoRedo('redo'); }

async function _puzzleUndoRedo(action) {
    if (_currentEditorMode() === 'puzzle') {
        await _peCommitWord();
    }
    const wn = AppState.puzzleWorkingName;
    const path = _currentEditorMode() === 'grid'
        ? `/api/puzzles/${encodeURIComponent(wn)}/grid/${action}`
        : `/api/puzzles/${encodeURIComponent(wn)}/${action}`;
    try {
        const data = await apiFetch('POST', path);
        AppState.puzzleData       = data;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'clues';
        AppState._statsData       = null;
        renderPuzzleEditor();
    } catch (e) { showRequestError(`Error during ${action}`, e); }
}

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------

async function _settlePuzzleEditingBeforeModeSwitch() {
    if (_isWordEditorOpen()) {
        const result = await completeSelectedWordEdit({ editorMode: 'puzzle' });
        if (result.error) {
            throw new Error('Could not save current word edit');
        }
        closeWordEditor();
        return;
    }
    if (AppState.selectedWord) {
        const result = await _peCommitWord();
        if (result && result.error) {
            throw new Error('Could not save current word edit');
        }
    }
}

export async function _settlePuzzleEditingBeforeSave() {
    if (_currentEditorMode() !== 'puzzle') return;
    await _settlePuzzleEditingBeforeModeSwitch();
}

async function _switchToGridModeConfirmed() {
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/grid`);
        AppState.puzzleData       = data;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab         = 'grid';
        AppState._statsData         = null;
        renderPuzzleEditor();
    } catch (e) { showRequestError('Error switching to Grid mode', e); }
}

async function do_switch_to_grid_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'grid') return;
    if (AppState.puzzleData.puzzle.words.some(w => w.locked)) return;
    messageBox(
        'Modify grid',
        'Are you sure you want to modify the grid?',
        null,
        async () => _switchToGridModeConfirmed()
    );
}

async function do_puzzle_clear() {
    if (_isWordEditorOpen()) return;
    const words = AppState.puzzleData.puzzle.words;
    const lockedCount    = words.filter(w => w.locked).length;
    const clearableCount = words.length - lockedCount;
    const lockedNote = lockedCount > 0
        ? ` ${lockedCount} locked word${lockedCount === 1 ? '' : 's'} will be skipped.`
        : '';
    messageBox(
        'Clear puzzle',
        `${clearableCount} word${clearableCount === 1 ? '' : 's'} will be cleared.${lockedNote}`,
        null,
        async () => {
            try {
                const data = await apiFetch('POST',
                    `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/clear`);
                AppState.puzzleData = data;
                if (AppState.selectedWord) {
                    _refreshSelectedWordFromPuzzleData();
                }
                renderPuzzleEditor();
            } catch (e) { showRequestError('Error clearing puzzle', e); }
        }
    );
}

async function do_switch_to_puzzle_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'puzzle') return;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/puzzle`);
        const hadGridStructureChange = AppState.gridStructureChanged;
        AppState.puzzleData   = data;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab         = 'clues';
        AppState._statsData         = null;
        AppState.gridStructureChanged = false;
        renderPuzzleEditor();
        if (hadGridStructureChange) {
            showMessageLine(
                'Back in Puzzle mode. Review recomputed entries and any clues that were cleared.',
                'notice'
            );
        }
    } catch (e) { showRequestError('Error switching to Puzzle mode', e); }
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
    } catch (e) { showRequestError('Error generating grid', e, MESSAGE_LINE_TIMEOUT_MS); }
    finally {
        if (btn) btn.classList.remove('w3-disabled');
    }
}

// ---------------------------------------------------------------------------
// Menu actions — Puzzle CRUD
// ---------------------------------------------------------------------------

async function do_puzzle_title() {
    const wn = AppState.puzzleWorkingName;
    const current = AppState.puzzleData && AppState.puzzleData.puzzle.title || '';
    inputBox('Set puzzle title', '<b>Puzzle title:</b>', current, async (title) => {
        try {
            await apiFetch('PUT', `/api/puzzles/${encodeURIComponent(wn)}/title`, { title });
            AppState.puzzleData = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
            renderPuzzleEditorLhs();
        } catch (e) { showRequestError('Error setting title', e); }
    });
}

async function do_puzzle_stats() {
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

async function do_puzzle_fill_order() {
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
