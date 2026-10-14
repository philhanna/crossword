// Crossword Puzzle Editor — the editor screen
//
// Draws the editor (app-bar info, action bar, grid pane and sidebar) and
// switches between Grid mode and Puzzle mode. The sidebar's panels each come
// from their own module; this one picks which to show.

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { escapeHtml } from '../core/dom.js';
import { _hash } from '../core/hash.js';
import { AppState } from '../core/state.js';
import { askConfirm, askText } from '../ui/dialogs.js';
import { updateMenu } from '../ui/menu.js';
import { showMessageLine, showRequestError } from '../ui/message-line.js';
import { renderClues, restoreCluesScroll, saveCluesScroll } from './clues-panel.js';
import {
    cachedFillOrder, do_puzzle_fill_order, fillOrder, forgetFillOrders,
    isFillOrderLoading, renderFillOrderPanel,
} from './fill-order-panel.js';
import { _focusPuzzleSvg, _peOutsideMousedown, handlePuzzleClick } from './grid-clicks.js';
import {
    forgetGridChanges, handleGridModeClick, renderGridModePanel,
    takeGridStructureChanged,
} from './grid-mode.js';
import { _peKeydown } from './keyboard.js';
import {
    _getSelectedWordCursorIdx, _isWordEditorOpen, _peCommitWord,
    _refreshSelectedWordFromPuzzleData, clearSelection,
    completeSelectedWordEdit, getSelectedWord,
} from './selection.js';
import { do_puzzle_stats, forgetStats, renderStatsPanel, statsLoaded } from './stats-panel.js';
import { closeWordEditor, openWordEditor, renderWordEditorPanel } from './word-editor.js';
import { buildPuzzleSvg } from '../svg/grid-svg.js';

registerActions({
    'puzzle-title': () => do_puzzle_title(),
    'puzzle-clear': () => do_puzzle_clear(),
    'puzzle-undo':  () => do_puzzle_undo(),
    'puzzle-redo':  () => do_puzzle_redo(),
    'puzzle-mode':  () => do_switch_to_puzzle_mode(),
    'grid-mode':    () => do_switch_to_grid_mode(),
    'sidebar-tab':  (el) => switchSidebarTab(el.dataset.tab),
});

// Which sidebar panel shows: 'clues', 'word', 'stats' or 'fill-order' in
// Puzzle mode; 'grid' or 'stats' in Grid mode. While the word editor is open
// it shows regardless.
const sidebar = { tab: 'clues' };

export function getSidebarTab() {
    return sidebar.tab;
}

export function setSidebarTab(tab) {
    sidebar.tab = tab;
}

// Forget everything the editor knew about the previous puzzle; called when a
// puzzle is opened or closed.
export function resetEditor() {
    clearSelection();
    sidebar.tab = 'clues';
    forgetStats();
    forgetFillOrders();
    forgetGridChanges();
}

// ---------------------------------------------------------------------------
// Rendering
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

    const sw  = getSelectedWord();
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
    const genDisabled = (size >= 9 && size % 2 === 1) ? '' : ' is-disabled';
    const fillOrderDisabled = isFillOrderLoading() ? ' is-disabled' : '';
    const fillOrderDisabledAttr = isFillOrderLoading() ? ' disabled' : '';
    const closeDisabled = _isWordEditorOpen() ? ' is-disabled' : '';
    const closeDisabledAttr = _isWordEditorOpen() ? ' disabled' : '';
    const hasLockedWords = !!(pd && pd.puzzle.words.some(w => w.locked));
    const gridModeDisabled = hasLockedWords ? ' is-disabled' : '';
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
        contentHtml = activeTab === 'stats' && statsLoaded()
            ? renderStatsPanel()
            : renderGridModePanel();
    } else {
        switch (activeTab) {
            case 'word':
                contentHtml = _isWordEditorOpen()
                    ? renderWordEditorPanel()
                    : `<div class="sidebar-empty">Select a word in the grid, then click <b>Edit word</b> to edit it here.</div>`;
                break;
            case 'stats':
                contentHtml = statsLoaded()
                    ? renderStatsPanel()
                    : `<div class="sidebar-empty">Loading stats…</div>`;
                break;
            case 'fill-order': {
                const fillOrder = cachedFillOrder();
                contentHtml = fillOrder
                    ? renderFillOrderPanel(fillOrder)
                    : `<div class="sidebar-empty">Loading fill order…</div>`;
                break;
            }
            default:
                contentHtml = renderClues();
        }
    }

    const cluesScroll = saveCluesScroll();
    document.getElementById('rhs').innerHTML =
        renderSidebarTabs(activeTab, tabList) +
        `<div class="sidebar-content">${contentHtml}</div>`;
    restoreCluesScroll(cluesScroll);
}

function _getActiveTab(mode) {
    if (mode === 'grid') return sidebar.tab === 'stats' ? 'stats' : 'grid';
    if (_isWordEditorOpen()) return 'word';
    return sidebar.tab;
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
    if (tab === 'stats' && !statsLoaded()) {
        await do_puzzle_stats(); return;
    }
    if (tab === 'fill-order' && !cachedFillOrder()) {
        await do_puzzle_fill_order(); return;
    }
    const sw = getSelectedWord();
    if (tab === 'word' && !_isWordEditorOpen() && sw) {
        await openWordEditor(sw.seq, sw.direction); return;
    }
    sidebar.tab = tab;
    renderPuzzleEditorRhs();
}

export function _updatePuzzleUndoRedo() {
    const pd      = AppState.puzzleData;
    const mode    = _currentEditorMode();
    const editing = _isWordEditorOpen();
    const ub      = document.getElementById('puzzle-undo-btn');
    const rb      = document.getElementById('puzzle-redo-btn');
    if (!ub || !rb) return;
    const canUndo = !pd ? false : (mode === 'grid' ? !!pd.grid_can_undo : !!pd.puzzle_can_undo);
    const canRedo = !pd ? false : (mode === 'grid' ? !!pd.grid_can_redo : !!pd.puzzle_can_redo);
    ub.classList.toggle('is-disabled', editing || !canUndo);
    rb.classList.toggle('is-disabled', editing || !canRedo);
    _updatePuzzleToolbar();
}

export function _updatePuzzleToolbar() {
    const mode = _currentEditorMode();
    const eb = document.getElementById('puzzle-editword-btn');
    const cb = document.getElementById('puzzle-close-btn');
    const db = document.getElementById('puzzle-delete-btn');
    if (eb) {
        eb.classList.toggle('is-disabled', mode !== 'puzzle' || !getSelectedWord() || _isWordEditorOpen());
    }
    if (db) {
        db.classList.toggle('is-disabled', _isWordEditorOpen());
        db.disabled = _isWordEditorOpen();
    }
    if (cb) {
        cb.classList.toggle('is-disabled', _isWordEditorOpen());
        cb.disabled = _isWordEditorOpen();
    }
}

// ---------------------------------------------------------------------------
// Undo / redo
// ---------------------------------------------------------------------------

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
        AppState.puzzleData = await apiFetch('POST', path);
        clearSelection();
        sidebar.tab = 'clues';
        forgetStats();
        renderPuzzleEditor();
    } catch (e) { showRequestError(`Error during ${action}`, e); }
}

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------

export async function _settlePuzzleEditingBeforeModeSwitch() {
    if (_isWordEditorOpen()) {
        const result = await completeSelectedWordEdit({ editorMode: 'puzzle' });
        if (result.error) {
            throw new Error('Could not save current word edit');
        }
        closeWordEditor();
        return;
    }
    if (getSelectedWord()) {
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

async function do_switch_to_grid_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'grid') return;
    if (AppState.puzzleData.puzzle.words.some(w => w.locked)) return;
    if (!await askConfirm('Modify grid', 'Are you sure you want to modify the grid?')) return;
    await _switchToGridModeConfirmed();
}

async function _switchToGridModeConfirmed() {
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        AppState.puzzleData = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/grid`);
        clearSelection();
        sidebar.tab = 'grid';
        forgetStats();
        renderPuzzleEditor();
    } catch (e) { showRequestError('Error switching to Grid mode', e); }
}

async function do_switch_to_puzzle_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'puzzle') return;
    try {
        AppState.puzzleData = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/puzzle`);
        const hadGridStructureChange = takeGridStructureChanged();
        clearSelection();
        sidebar.tab = 'clues';
        forgetStats();
        renderPuzzleEditor();
        if (hadGridStructureChange) {
            showMessageLine(
                'Back in Puzzle mode. Review recomputed entries and any clues that were cleared.',
                'notice'
            );
        }
    } catch (e) { showRequestError('Error switching to Puzzle mode', e); }
}

// ---------------------------------------------------------------------------
// Whole-puzzle edits
// ---------------------------------------------------------------------------

async function do_puzzle_clear() {
    if (_isWordEditorOpen()) return;
    const words = AppState.puzzleData.puzzle.words;
    const lockedCount    = words.filter(w => w.locked).length;
    const clearableCount = words.length - lockedCount;
    const lockedNote = lockedCount > 0
        ? ` ${lockedCount} locked word${lockedCount === 1 ? '' : 's'} will be skipped.`
        : '';
    const confirmed = await askConfirm('Clear puzzle',
        `${clearableCount} word${clearableCount === 1 ? '' : 's'} will be cleared.${lockedNote}`);
    if (!confirmed) return;
    try {
        AppState.puzzleData = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/clear`);
        if (getSelectedWord()) {
            _refreshSelectedWordFromPuzzleData();
        }
        renderPuzzleEditor();
    } catch (e) { showRequestError('Error clearing puzzle', e); }
}

async function do_puzzle_title() {
    const wn = AppState.puzzleWorkingName;
    const current = AppState.puzzleData && AppState.puzzleData.puzzle.title || '';
    const title = await askText('Set puzzle title', '<b>Puzzle title:</b>', current);
    if (title === null) return;
    try {
        await apiFetch('PUT', `/api/puzzles/${encodeURIComponent(wn)}/title`, { title });
        AppState.puzzleData = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
        renderPuzzleEditorLhs();
    } catch (e) { showRequestError('Error setting title', e); }
}
