// Crossword Puzzle Editor — puzzle editor rendering, CRUD, grid ops, undo/redo, export

// ---------------------------------------------------------------------------
// Puzzle editor — rendering
// ---------------------------------------------------------------------------

function _currentEditorMode() {
    return (AppState.puzzleData && AppState.puzzleData.mode) || 'puzzle';
}

function renderPuzzleEditor() {
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

function renderPuzzleEditorLhs() {
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
        ? `<div class="puzzle-title-display" onclick="do_puzzle_title()" style="cursor:pointer">${escapeHtml(puzzleTitle)}</div>`
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

function updateAppBarPuzzleInfo() {
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
    el.innerHTML =
        `<span class="puzzle-info-name">${escapeHtml(name)}</span>` +
        `<span class="${badgeClass}">${badgeText}</span>` +
        saveHtml;
}

function renderActionBar() {
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

    const modeSpecific = mode === 'grid' ? `
<div class="ab-group">
  <button class="ab-btn ab-mode-btn" onclick="do_switch_to_puzzle_mode()">Puzzle Mode</button>
  <button class="ab-btn ab-mode-btn ab-mode-active">Grid Mode</button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button class="ab-btn" onclick="do_puzzle_rotate_grid()">
    <i class="material-icons">rotate_right</i><span>Rotate</span>
  </button>
  <button id="puzzle-generate-btn" class="ab-btn${genDisabled}" onclick="do_puzzle_generate_grid()">
    <i class="material-icons">casino</i><span>Generate</span>
  </button>
  <button class="ab-btn" onclick="do_puzzle_stats()">
    <i class="material-icons">info</i><span>Stats</span>
  </button>
</div>` : `
<div class="ab-group">
  <button class="ab-btn ab-mode-btn ab-mode-active">Puzzle Mode</button>
  <button class="ab-btn ab-mode-btn" onclick="do_switch_to_grid_mode()">Grid Mode</button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button id="puzzle-editword-btn" class="ab-btn" onclick="do_puzzle_edit_word()">
    <i class="material-icons">edit</i><span>Edit word</span>
  </button>
  <button id="puzzle-fill-order-btn" class="ab-btn${fillOrderDisabled}" onclick="do_puzzle_fill_order()"${fillOrderDisabledAttr}>
    <i class="material-icons">format_list_numbered</i><span>Fill order</span>
  </button>
  <button class="ab-btn" onclick="do_puzzle_stats()">
    <i class="material-icons">info</i><span>Stats</span>
  </button>
</div>`;

    ab.innerHTML = `
<div class="ab-group">
  <button class="ab-btn" onclick="do_puzzle_save()">
    <i class="material-icons">save</i><span>Save</span>
  </button>
  <button id="puzzle-close-btn" class="ab-btn${closeDisabled}" onclick="do_puzzle_close()"${closeDisabledAttr}>
    <i class="material-icons">close</i><span>Close</span>
  </button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button id="puzzle-undo-btn" class="ab-btn" onclick="do_puzzle_undo()">
    <i class="material-icons">undo</i><span>Undo</span>
  </button>
  <button id="puzzle-redo-btn" class="ab-btn" onclick="do_puzzle_redo()">
    <i class="material-icons">redo</i><span>Redo</span>
  </button>
</div>
<div class="ab-divider"></div>
${modeSpecific}`;
}

function renderPuzzleEditorRhs() {
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
            case 'fill-order':
                contentHtml = AppState._fillOrderData
                    ? renderFillOrderPanel(AppState._fillOrderData)
                    : `<div class="sidebar-empty">Loading fill order…</div>`;
                break;
            default:
                contentHtml = renderClues();
        }
    }

    document.getElementById('rhs').innerHTML =
        renderSidebarTabs(activeTab, tabList) +
        `<div class="sidebar-content">${contentHtml}</div>`;
    _scrollCluesToFirstMissing();
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
                     onclick="switchSidebarTab('${t}')">${labels[t]}</button>`
        ).join('')
    }</div>`;
}

async function switchSidebarTab(tab) {
    if (tab === 'stats' && !AppState._statsData) {
        await do_puzzle_stats(); return;
    }
    if (tab === 'fill-order' && !AppState._fillOrderData) {
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

function switchClueDirection(dir) {
    _clueDirection = dir;
    renderPuzzleEditorRhs();
}

function _scrollCluesToFirstMissing() {
    const list = document.getElementById('clue-list-active');
    if (!list) return;
    const first = list.querySelector('[data-noclue]');
    if (first) first.scrollIntoView({ block: 'nearest' });
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
        return `<li class="clue-row${isSelected ? ' clue-row-selected' : ''}"${hasMissing ? ' data-noclue="1"' : ''}>` +
            `<a class="clue-row-link" onclick="selectWord(${w.seq},'${dir}');return false;">` +
            (hasMissing ? '<span class="clue-missing-dot"></span>' : '') +
            `<span class="clue-num">${w.seq}</span>` +
            `<span class="clue-text${hasMissing ? ' clue-text-missing' : ''}">${escapeHtml(w.clue || 'No clue')}</span>` +
            `</a>` +
            `<a class="clue-edit-link" onclick="do_puzzle_edit_word(${w.seq},'${dir}');return false;">edit</a>` +
            `</li>`;
    }).join('');

    return `
<div class="clue-toolbar">
  <div class="clue-dir-toggle">
    <button class="clue-dir-btn${dir === 'across' ? ' clue-dir-btn-active' : ''}" onclick="switchClueDirection('across')">Across</button>
    <button class="clue-dir-btn${dir === 'down'   ? ' clue-dir-btn-active' : ''}" onclick="switchClueDirection('down')">Down</button>
  </div>
  <span class="clue-count ${countClass}">${countLabel}</span>
</div>
<ul id="clue-list-active" class="clue-list-new">${items}</ul>`;
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
<div class="stat-section-title">Word lengths</div>
<table class="stat-table">
  <tr><th>Length</th><th>Across</th><th>Down</th></tr>
  ${wlRows}
</table>`;
}

function renderFillOrderPanel(data) {
    const rows = (data.fill_priority || []).map(item => {
        const countLabel = `${item.candidate_count} candidate${item.candidate_count === 1 ? '' : 's'}`;
        return `<tr onclick="_openWordFromFillOrder(${item.seq},'${item.direction}')">
  <td style="white-space:nowrap"><a onclick="return false">${escapeHtml(item.label)}</a></td>
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

function closeStatsPanel() {
    AppState.showingStats = false;
    AppState.sidebarTab   = 'clues';
    renderPuzzleEditorRhs();
}

async function _openWordFromFillOrder(seq, dir) {
    const result = await completeSelectedWordEdit({
        nextSelection: { seq, direction: dir }
    });
    if (result.error) return;
    await openWordEditor(seq, dir);
}

function closeFillOrderPanel() {
    AppState.showingFillOrder = false;
    AppState.sidebarTab       = 'clues';
    renderPuzzleEditorRhs();
}

async function _refreshPuzzleStatsIfVisible() {
    if (AppState.sidebarTab !== 'stats' || !AppState.puzzleWorkingName) return;
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/stats`);
        if (data.error) return;
        AppState._statsData = data;
        renderPuzzleEditorRhs();
    } catch (e) {
        // Keep the current panel if the refresh fails.
    }
}

async function _refreshFillOrderIfVisible() {
    if (AppState.sidebarTab !== 'fill-order' || !AppState.puzzleWorkingName || _currentEditorMode() !== 'puzzle') return;
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/fill-order`);
        if (data.error) return;
        AppState._fillOrderData = data;
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
        if (data.error) { showMessageLine(`Error updating grid: ${data.error}`, 'error', 0); return; }
        await _applyGridModeUpdate(data);
    } catch (e) {
        showMessageLine('Error updating grid', 'error', 0);
    }
}

// ---------------------------------------------------------------------------
// Undo / redo
// ---------------------------------------------------------------------------

function _updatePuzzleUndoRedo() {
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

function _updatePuzzleToolbar() {
    const mode = _currentEditorMode();
    const eb = document.getElementById('puzzle-editword-btn');
    const cb = document.getElementById('puzzle-close-btn');
    if (eb) {
        eb.classList.toggle('w3-disabled', mode !== 'puzzle' || !AppState.selectedWord || _isWordEditorOpen());
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
        if (data.error) { showMessageLine(`${action} failed: ${data.error}`, 'error', 0); return; }
        AppState.puzzleData       = data;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'clues';
        AppState._statsData       = null;
        AppState._fillOrderData   = null;
        renderPuzzleEditor();
    } catch (e) { showMessageLine(`Error during ${action}`, 'error', 0); }
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

async function _settlePuzzleEditingBeforeSave() {
    if (_currentEditorMode() !== 'puzzle') return;
    await _settlePuzzleEditingBeforeModeSwitch();
}

async function _switchToGridModeConfirmed() {
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/grid`);
        if (data.error) { showMessageLine(`Error switching modes: ${data.error}`, 'error', 0); return; }
        AppState.puzzleData       = data;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'grid';
        AppState._statsData       = null;
        AppState._fillOrderData   = null;
        renderPuzzleEditor();
    } catch (e) { showMessageLine('Error switching to Grid mode', 'error', 0); }
}

async function do_switch_to_grid_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'grid') return;
    messageBox(
        'Modify grid',
        'Are you sure you want to modify the grid?',
        null,
        async () => _switchToGridModeConfirmed()
    );
}

async function do_switch_to_puzzle_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'puzzle') return;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/puzzle`);
        if (data.error) { showMessageLine(`Error switching modes: ${data.error}`, 'error', 0); return; }
        const hadGridStructureChange = AppState.gridStructureChanged;
        AppState.puzzleData   = data;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'clues';
        AppState._statsData       = null;
        AppState._fillOrderData   = null;
        AppState.gridStructureChanged = false;
        renderPuzzleEditor();
        if (hadGridStructureChange) {
            showMessageLine(
                'Back in Puzzle mode. Review recomputed entries and any clues that were cleared.',
                'notice'
            );
        }
    } catch (e) { showMessageLine('Error switching to Puzzle mode', 'error', 0); }
}

async function do_puzzle_rotate_grid() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() !== 'grid') return;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/rotate`);
        if (data.error) { showMessageLine(`Error rotating grid: ${data.error}`, 'error', 0); return; }
        await _applyGridModeUpdate(data);
    } catch (e) { showMessageLine('Error rotating grid', 'error', 0); }
}

async function do_puzzle_generate_grid() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() !== 'grid') return;
    const btn = document.getElementById('puzzle-generate-btn');
    if (btn) btn.classList.add('w3-disabled');
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/generate`);
        if (data.notice) { showMessageLine(data.notice, 'notice'); return; }
        if (data.error) { showMessageLine(`Error generating grid: ${data.error}`, 'error'); return; }
        await _applyGridModeUpdate(data);
    } catch (e) { showMessageLine('Error generating grid', 'error'); }
    finally {
        if (btn) btn.classList.remove('w3-disabled');
    }
}

// ---------------------------------------------------------------------------
// Menu actions — Puzzle CRUD
// ---------------------------------------------------------------------------

async function _openPuzzleInEditor(name) {
    const openData = await apiFetch('POST', `/api/puzzles/${encodeURIComponent(name)}/open`);
    if (openData.error) {
        throw new Error(openData.error);
    }
    const wn = openData.working_name;
    const puzzleData = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
    if (puzzleData.error) {
        throw new Error(puzzleData.error);
    }
    AppState.puzzleName        = name;
    AppState.puzzleOriginalName = name;
    AppState.puzzleWorkingName = wn;
    AppState.puzzleData        = puzzleData;
    AppState.puzzleSavedHash   = _hash(puzzleData.puzzle);
    AppState.selectedWord      = null;
    AppState.showingStats      = false;
    AppState.showingFillOrder  = false;
    AppState.sidebarTab        = 'clues';
    AppState._statsData        = null;
    AppState._fillOrderData    = null;
    AppState.gridStructureChanged = false;
    showView('editor');
}

async function do_puzzle_open() {
    try {
        const listData = await apiFetch('GET', '/api/puzzles');
        if (listData.error) { showMessageLine(`Error: ${listData.error}`, 'error', 0); return; }
        const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
        if (puzzles.length === 0) {
            showMessageLine('No saved puzzles found.', 'notice');
            return;
        }
        showPreviewChooser('Open puzzle', puzzles, '/api/puzzles', async (name) => {
            try {
                await _openPuzzleInEditor(name);
            } catch (e) { showMessageLine('Error opening puzzle', 'error', 0); }
        });
    } catch (e) {
        showMessageLine('Error listing puzzles', 'error', 0);
    }
}

async function do_puzzle_import() {
    const fileInput = document.getElementById('acrosslite-file-input');
    // Reset so the same file can be selected again
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        // Pre-populate name from filename (strip .txt extension)
        const defaultName = file.name.replace(/\.txt$/i, '');

        inputBox(
            'Import AcrossLite puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    const data = await apiFetch('POST', '/api/import/acrosslite', { name, content });
                    if (data.error) { showMessageLine(`Import failed: ${data.error}`, 'error', 0); return; }
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showMessageLine(`Import error: ${e.message || e}`, 'error', 0);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_import_xd() {
    const fileInput = document.getElementById('xd-file-input');
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        const defaultName = file.name.replace(/\.xd$/i, '');

        inputBox(
            'Import xd puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    const data = await apiFetch('POST', '/api/import/xd', { name, content });
                    if (data.error) { showMessageLine(`Import failed: ${data.error}`, 'error', 0); return; }
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showMessageLine(`Import error: ${e.message || e}`, 'error', 0);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_import_puz() {
    const fileInput = document.getElementById('puz-file-input');
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        const defaultName = file.name.replace(/\.puz$/i, '');

        inputBox(
            'Import .puz puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content_b64;
                try {
                    const buf = await file.arrayBuffer();
                    content_b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    const data = await apiFetch('POST', '/api/import/puz', { name, content_b64 });
                    if (data.error) { showMessageLine(`Import failed: ${data.error}`, 'error', 0); return; }
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showMessageLine(`Import error: ${e.message || e}`, 'error', 0);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_new() {
    function promptForSize(sizeVal = '') {
        inputBox(
            'New puzzle',
            '<b>Puzzle size:</b> <em>(an odd positive integer, e.g. 15)</em>',
            sizeVal,
            (enteredSize) => {
                const n = Number(enteredSize);
                if (!enteredSize || isNaN(n)) {
                    messageBox(
                        'Invalid puzzle size',
                        `${escapeHtml(enteredSize)} is not a number.`,
                        null,
                        () => promptForSize(enteredSize)
                    );
                    return;
                }
                if (n % 2 === 0) {
                    messageBox(
                        'Invalid puzzle size',
                        `${n} is not an odd number.`,
                        null,
                        () => promptForSize(enteredSize)
                    );
                    return;
                }
                if (n < 1) {
                    messageBox(
                        'Invalid puzzle size',
                        `${n} is not a positive number.`,
                        null,
                        () => promptForSize(enteredSize)
                    );
                    return;
                }
                (async () => {
                    try {
                        const internalName = '__new__' + Math.random().toString(36).slice(2, 10);
                        const data = await apiFetch('POST', '/api/puzzles', { name: internalName, size: n });
                        if (data.error) { showMessageLine(`Error creating puzzle: ${data.error}`, 'error', 0); return; }
                        await _openPuzzleInEditor(internalName);
                        AppState.puzzleName         = null;        // no user-facing name yet
                        AppState.puzzleOriginalName = internalName;
                        renderPuzzleEditorLhs();
                    } catch (e) { showMessageLine('Error creating puzzle', 'error', 0); }
                })();
            }
        );
    }

    promptForSize();
}

async function do_puzzle_save() {
    const wn   = AppState.puzzleWorkingName;
    const name = AppState.puzzleName;
    if (!name) { do_puzzle_save_as(); return; }
    try {
        await _settlePuzzleEditingBeforeSave();
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: name });
        if (data.error) { showMessageLine(`Save failed: ${data.error}`, 'error', 0); return; }
        AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
        renderPuzzleEditor();
        showMessageLine(`Puzzle ${name} saved.`, 'notice');
    } catch (e) { showMessageLine('Error saving puzzle', 'error', 0); }
}

async function _listSavedPuzzleNames() {
    const listData = await apiFetch('GET', '/api/puzzles');
    if (listData.error) {
        throw new Error(listData.error);
    }
    return (listData.puzzles || []).filter(p => p && !p.startsWith('__'));
}

async function _savePuzzleAsName(newName) {
    const wn = AppState.puzzleWorkingName;
    const data = await apiFetch('POST',
        `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: newName });
    if (data.error) {
        throw new Error(data.error);
    }
    AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
    if (!AppState.puzzleName) {
        // New (never-saved) puzzle: assign the name and clean up the __new__ entry
        const oldOriginal = AppState.puzzleOriginalName;
        AppState.puzzleName         = newName;
        AppState.puzzleOriginalName = newName;
        if (oldOriginal && oldOriginal !== newName) {
            try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(oldOriginal)}`); }
            catch (e) { /* ignore */ }
        }
    }
    renderPuzzleEditor();
    // For an existing named puzzle (true Save As), keep the editor on the original.
    showMessageLine(`Puzzle saved as "${newName}".`, 'notice');
}

async function do_puzzle_save_as() {
    inputBox('Save puzzle as', 'Puzzle name:', AppState.puzzleName || '', async (newName) => {
        if (!newName) return;
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            await _settlePuzzleEditingBeforeSave();
            await confirmOverwriteIfExists(
                'puzzle',
                newName,
                _listSavedPuzzleNames,
                () => _savePuzzleAsName(newName)
            );
        } catch (e) { showMessageLine('Error saving puzzle', 'error', 0); }
    });
}

async function do_puzzle_rename() {
    const currentName = AppState.puzzleName;
    if (!currentName) return;
    inputBox('Rename puzzle', 'New name:', currentName, async (newName) => {
        if (!newName || newName === currentName) return;
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            const existing = await _listSavedPuzzleNames();
            if (existing.includes(newName)) {
                const confirmed = await new Promise(resolve =>
                    messageBox(`A puzzle named "${newName}" already exists. Overwrite?`,
                        [{ label: 'Overwrite', value: true }, { label: 'Cancel', value: false }],
                        resolve)
                );
                if (!confirmed) return;
            }
            const data = await apiFetch('POST',
                `/api/puzzles/${encodeURIComponent(currentName)}/rename`, { new_name: newName });
            if (data.error) { showMessageLine(`Error renaming puzzle: ${data.error}`, 'error', 0); return; }
            AppState.puzzleName         = newName;
            AppState.puzzleOriginalName = newName;
            renderPuzzleEditorLhs();
            updateMenu();
            showMessageLine(`Puzzle renamed to ${newName}.`, 'notice');
        } catch (e) { showMessageLine('Error renaming puzzle', 'error', 0); }
    });
}

async function _doPuzzleCloseConfirmed() {
    document.removeEventListener('keydown', _peKeydown);
    document.removeEventListener('keydown', _weKeydown);
    document.removeEventListener('mousedown', _peOutsideMousedown);
    const wn           = AppState.puzzleWorkingName;
    const originalName = AppState.puzzleOriginalName;
    const savedName    = AppState.puzzleName;
    AppState.puzzleName         = null;
    AppState.puzzleOriginalName = null;
    AppState.puzzleWorkingName  = null;
    AppState.puzzleData         = null;
    AppState.puzzleSavedHash    = null;
    AppState.selectedWord       = null;
    AppState.showingStats       = false;
    AppState.showingFillOrder   = false;
    AppState.sidebarTab         = 'clues';
    AppState._statsData         = null;
    AppState._fillOrderData     = null;
    AppState.gridStructureChanged = false;
    if (wn) {
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(wn)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    if (!savedName && originalName) {
        // Puzzle was never given a user name — delete the internal __new__ original too
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(originalName)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    showView('home');
}

async function do_puzzle_close() {
    if (_isWordEditorOpen()) return;
    const isDirty = AppState.puzzleData &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    if (isDirty) {
        const name = AppState.puzzleName || '(No name)';
        messageBox(
            'Close puzzle',
            `Puzzle <b>${escapeHtml(name)}</b> has unsaved changes. Close without saving?`,
            null,
            () => _doPuzzleCloseConfirmed()
        );
    } else {
        await _doPuzzleCloseConfirmed();
    }
}

async function do_puzzle_title() {
    const wn = AppState.puzzleWorkingName;
    const current = AppState.puzzleData && AppState.puzzleData.puzzle.title || '';
    inputBox('Set puzzle title', '<b>Puzzle title:</b>', current, async (title) => {
        try {
            const data = await apiFetch('PUT',
                `/api/puzzles/${encodeURIComponent(wn)}/title`, { title });
            if (data.error) { showMessageLine(`Error: ${data.error}`, 'error', 0); return; }
            const fresh = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
            if (!fresh.error) { AppState.puzzleData = fresh; renderPuzzleEditorLhs(); }
        } catch (e) { showMessageLine('Error setting title', 'error', 0); }
    });
}

async function do_puzzle_stats() {
    const wn = AppState.puzzleWorkingName;
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/stats`);
        if (data.error) { showMessageLine(`Error: ${data.error}`, 'error', 0); return; }
        AppState._statsData       = data;
        AppState.showingFillOrder = false;
        AppState.showingStats     = true;
        AppState.sidebarTab       = 'stats';
        renderPuzzleEditor();
    } catch (e) { showMessageLine('Error fetching stats', 'error', 0); }
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
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/fill-order`);
        if (data.error) { showMessageLine(`Error: ${data.error}`, 'error', 0); return; }
        AppState._fillOrderData   = data;
        AppState.showingStats     = false;
        AppState.showingFillOrder = true;
        AppState.sidebarTab       = 'fill-order';
        renderPuzzleEditor();
    } catch (e) { showMessageLine('Error fetching fill order', 'error', 0); }
    finally {
        AppState.fillOrderLoading = false;
        renderActionBar();
    }
}

async function do_puzzle_delete() {
    try {
        const puzzles = await _listSavedPuzzleNames();
        if (puzzles.length === 0) {
            showMessageLine('No saved puzzles found.', 'notice');
            return;
        }
        showPreviewChooser('Delete puzzle', puzzles, '/api/puzzles', async (name) => {
            messageBox(
                'Delete puzzle',
                `Are you sure you want to delete puzzle <b>'${escapeHtml(name)}'</b>?`,
                null,
                async () => {
                    try {
                        const data = await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
                        if (data && data.error) { showMessageLine(`Error deleting puzzle: ${data.error}`, 'error', 0); return; }
                        if (AppState.puzzleName === name) {
                            await _doPuzzleCloseConfirmed();
                            return;
                        }
                        showMessageLine(`Puzzle ${name} deleted.`, 'notice');
                    } catch (e) { showMessageLine('Error deleting puzzle', 'error', 0); }
                }
            );
        });
    } catch (e) {
        showMessageLine('Error listing puzzles', 'error', 0);
    }
}

// ---------------------------------------------------------------------------
// Menu actions — Export
// ---------------------------------------------------------------------------

async function _downloadExport(name, format) {
    const endpointMap = { puz: 'acrosslite', puzbin: 'puz', xd: 'xd', xml: 'xml', nyt: 'nytimes', solver: 'solver-pdf' };
    const filenameMap = { puz: `acrosslite-${name}.txt`, puzbin: `${name}.puz`, xd: `${name}.xd`, xml: `${name}.xml`, nyt: `nytimes-${name}.pdf`, solver: `${name}-solver.pdf` };
    const labelMap  = { puz: 'Across Lite', puzbin: '.puz Binary', xd: 'xword xd', xml: 'Crossword Compiler XML', nyt: 'New York Times', solver: 'Solver PDF' };
    const endpoint = endpointMap[format];
    const filename = filenameMap[format];
    try {
        const resp = await fetch(`/api/export/puzzles/${encodeURIComponent(name)}/${endpoint}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showMessageLine(err.error || `Export failed: HTTP ${resp.status}`, 'error');
            return;
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showMessageLine(`Exported "${name}" as ${labelMap[format]}: ${filename}`, 'notice');
    } catch (e) {
        showMessageLine('Export request failed.', 'error');
    }
}

async function do_export(format) {
    if (AppState.view === 'editor' && AppState.puzzleName) {
        await _downloadExport(AppState.puzzleName, format);
    } else {
        try {
            const listData = await apiFetch('GET', '/api/puzzles');
            if (listData.error) { showMessageLine(`Error: ${listData.error}`, 'error', 0); return; }
            const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
            if (puzzles.length === 0) {
                showMessageLine('No saved puzzles found.', 'notice');
                return;
            }
            showPreviewChooser('Choose a puzzle to export', puzzles, '/api/puzzles', async (name) => {
                await _downloadExport(name, format);
            });
        } catch (e) {
            showMessageLine('Error listing puzzles', 'error', 0);
        }
    }
}
