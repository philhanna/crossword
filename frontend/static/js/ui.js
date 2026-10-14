// Crossword Puzzle Editor — UI primitives, modals, menu, view management

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

function _hash(obj) {
    // This is the djb2 hash function
    const s = JSON.stringify(obj);
    let h = 5381;
    for (let i = 0; i < s.length; i++)
        h = (h * 33 ^ s.charCodeAt(i)) >>> 0;
    return h;
}

function showElement(id) { document.getElementById(id).style.display = 'block'; }
function hideElement(id) { document.getElementById(id).style.display = 'none'; }

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function _closeSidePanels() {
    AppState.showingStats     = false;
    AppState.showingFillOrder = false;
    AppState.sidebarTab       = 'clues';
}

// A request the server answered with an error status. `message` is the
// server's own explanation from its {"error": ...} body when it sent one.
class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

// Send a JSON request and return the parsed response body. Throws ApiError
// when the server answers with an error status, and lets network failures
// propagate as they are.
async function apiFetch(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const resp = await fetch(path, opts);
    const data = await resp.json().catch(() => null);
    if (!resp.ok) {
        throw new ApiError((data && data.error) || `HTTP ${resp.status}`, resp.status);
    }
    return data;
}

// Report a failed request on the message line: "<what>: <server message>"
// when the server explained itself, or just "<what>" when it didn't answer.
function showRequestError(what, e, timeoutMs = 0) {
    const text = e instanceof ApiError ? `${what}: ${e.message}` : what;
    showMessageLine(text, 'error', timeoutMs);
}

// ---------------------------------------------------------------------------
// Modal dialogs
// ---------------------------------------------------------------------------

let _messageLineTimer = null;

function positionMessageLine() {
    const ml = document.getElementById('ml');
    const ab = document.getElementById('action-bar');
    const appBar = document.querySelector('.app-bar');
    if (!ml || !appBar) return;
    const ref = (ab && ab.style.display !== 'none') ? ab : appBar;
    const rect = ref.getBoundingClientRect();
    ml.style.top = `${rect.bottom + 8}px`;
}

function clearMessageLine() {
    const ml = document.getElementById('ml');
    ml.style.display = 'none';
    ml.classList.remove('message-line-notice', 'message-line-error');
    document.getElementById('ml-text').textContent = '';
    if (_messageLineTimer) {
        clearTimeout(_messageLineTimer);
        _messageLineTimer = null;
    }
}

function showMessageLine(text, level = 'notice', timeoutMs = MESSAGE_LINE_TIMEOUT_MS) {
    (level === 'error' ? console.error : console.log)(`[${level}] ${text}`);
    const ml = document.getElementById('ml');
    document.getElementById('ml-text').textContent = text;
    ml.classList.remove('message-line-notice', 'message-line-error');
    ml.classList.add(level === 'error' ? 'message-line-error' : 'message-line-notice');
    positionMessageLine();
    ml.style.display = 'flex';
    if (_messageLineTimer) {
        clearTimeout(_messageLineTimer);
        _messageLineTimer = null;
    }
    if (timeoutMs > 0) {
        _messageLineTimer = setTimeout(() => {
            clearMessageLine();
        }, timeoutMs);
    }
}

function messageBox(title, prompt, ok, okCallback, okLabel = 'OK') {
    document.getElementById('mb-title').innerHTML = title;
    document.getElementById('mb-prompt').innerHTML = prompt;
    const mbOk = document.getElementById('mb-ok');
    mbOk.textContent = okLabel;
    if (okCallback) {
        mbOk.removeAttribute('href');
        mbOk.onclick = () => { hideElement('mb'); okCallback(); };
    } else if (ok) {
        mbOk.onclick = null;
        mbOk.setAttribute('href', ok);
    } else {
        mbOk.removeAttribute('href');
        mbOk.onclick = () => hideElement('mb');
    }
    showElement('mb');
}

function inputBox(title, label, value, onSubmit, { required = true, onCancel = null } = {}) {
    document.getElementById('ib-title').innerHTML = title;
    document.getElementById('ib-prompt').innerHTML = '';
    const fieldsEl = document.getElementById('ib-fields');
    fieldsEl.innerHTML = `
      <div class="form-field">
        <label id="ib-label" class="form-label"></label>
        <input type="text" id="ib-input" name="ib-input" class="form-input" value="">
      </div>`;
    document.getElementById('ib-label').innerHTML = label;
    const input = document.getElementById('ib-input');
    input.value = value;
    input.required = required;
    const dismiss = () => { hideElement('ib'); if (onCancel) onCancel(); };
    document.getElementById('ib-cancel').onclick = dismiss;
    document.getElementById('ib-close').onclick = dismiss;
    document.getElementById('ib-form').onsubmit = (e) => {
        e.preventDefault();
        hideElement('ib');
        onSubmit(input.value);
    };
    showElement('ib');
    input.focus();
}

function multiInputBox(title, fields, onSubmit, { onCancel = null } = {}) {
    document.getElementById('ib-title').innerHTML = title;
    document.getElementById('ib-prompt').innerHTML = '';
    const fieldsEl = document.getElementById('ib-fields');
    fieldsEl.innerHTML = fields.map((field, idx) => `
      <div class="form-field">
        <label class="form-label" for="ib-input-${idx}">${field.label}</label>
        <input type="text" id="ib-input-${idx}" name="${field.name}" class="form-input"
               value="${escapeHtml(field.value || '')}"${field.required === false ? '' : ' required'}>
      </div>`).join('');
    const dismiss = () => { hideElement('ib'); if (onCancel) onCancel(); };
    document.getElementById('ib-cancel').onclick = dismiss;
    document.getElementById('ib-close').onclick = dismiss;
    document.getElementById('ib-form').onsubmit = (e) => {
        e.preventDefault();
        hideElement('ib');
        const values = {};
        fields.forEach((field, idx) => {
            values[field.name] = document.getElementById(`ib-input-${idx}`).value;
        });
        onSubmit(values);
    };
    showElement('ib');
    const firstInput = document.getElementById('ib-input-0');
    if (firstInput) firstInput.focus();
}

async function confirmOverwriteIfExists(kind, name, listExistingNames, onConfirmSave) {
    const existingNames = await listExistingNames();
    if (!existingNames.includes(name)) {
        await onConfirmSave();
        return;
    }
    messageBox(
        `Overwrite ${kind}`,
        `${kind.charAt(0).toUpperCase() + kind.slice(1)} <b>${escapeHtml(name)}</b> already exists. Overwrite it?`,
        null,
        async () => {
            try {
                await onConfirmSave();
            } catch (e) {
                showMessageLine(`Save failed: ${e.message}`, 'error', 0);
            }
        },
        'Overwrite'
    );
}

function validateUserFacingName(kind, name) {
    if (name.startsWith('__wc__')) {
        messageBox(
            `Invalid ${kind} name`,
            `Names starting with <b>__wc__</b> are reserved for internal working copies used while editing a ${kind}. Please choose a different ${kind} name.`,
            null,
            null
        );
        return false;
    }
    return true;
}

const CH_PAGE_SIZE = 5;
let _chPreviews  = [];
let _chPage      = 0;
let _chOnSelect  = null;
let _chSortOrder = 'recent';
let _chLoadItems = null;
let _chEmptyMessage = 'No items found.';
let _chStateFilter = 'all';
let _chApiPrefix = '';

async function _chLoadPreviewsFromNames(names, apiPrefix) {
    return await Promise.all(
        names.map(name =>
            apiFetch('GET', `${apiPrefix}/${encodeURIComponent(name)}/preview`)
                .catch(() => ({ name, heading: name, svgstr: '', error: true }))
        )
    );
}

async function _chReload() {
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '<div class="w3-container w3-padding">Loading previews...</div>';
    document.getElementById('ch-pagination').style.display = 'none';

    const names = await _chLoadItems(_chStateFilter);
    _chPreviews = await _chLoadPreviewsFromNames(names, _chApiPrefix);
    _chRender();
}

async function showPreviewChooser(title, names, apiPrefix, onSelect, options = {}) {
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

// ---------------------------------------------------------------------------
// Right-click context menu
// ---------------------------------------------------------------------------

let _ctxMenuDismiss = null;

function hideContextMenu() {
    const el = document.getElementById('context-menu');
    if (el) el.remove();
    if (_ctxMenuDismiss) {
        document.removeEventListener('mousedown', _ctxMenuDismiss, true);
        document.removeEventListener('keydown', _ctxMenuDismiss, true);
        window.removeEventListener('scroll', _ctxMenuDismiss, true);
        _ctxMenuDismiss = null;
    }
}

// items: [{ label, onClick }, ...]
function showContextMenu(x, y, items) {
    hideContextMenu();

    const menu = document.createElement('div');
    menu.id = 'context-menu';
    menu.className = 'context-menu';
    items.forEach(item => {
        const entry = document.createElement('div');
        entry.className = 'context-menu-item';
        entry.textContent = item.label;
        entry.onclick = () => { hideContextMenu(); item.onClick(); };
        menu.appendChild(entry);
    });
    document.body.appendChild(menu);

    // Clamp to viewport so the menu never renders off-screen.
    const rect = menu.getBoundingClientRect();
    const left = Math.min(x, window.innerWidth - rect.width - 4);
    const top = Math.min(y, window.innerHeight - rect.height - 4);
    menu.style.left = `${Math.max(0, left)}px`;
    menu.style.top = `${Math.max(0, top)}px`;

    _ctxMenuDismiss = (e) => {
        if (e.type === 'mousedown' && menu.contains(e.target)) return;
        if (e.type === 'keydown' && e.key !== 'Escape') return;
        hideContextMenu();
    };
    document.addEventListener('mousedown', _ctxMenuDismiss, true);
    document.addEventListener('keydown', _ctxMenuDismiss, true);
    window.addEventListener('scroll', _ctxMenuDismiss, true);
}

// ---------------------------------------------------------------------------
// Menu enable / disable
// ---------------------------------------------------------------------------

// One rule per top-menu item: the item is enabled exactly when its rule
// returns true for the current menu context (see _menuContext).
const MENU_RULES = [
    { id: 'menu-puzzle-new',         enabledWhen: (s) => s.onDashboard },
    { id: 'menu-puzzle-open',        enabledWhen: (s) => s.onDashboard },
    { id: 'menu-puzzle-save',        enabledWhen: (s) => s.inEditor },
    { id: 'menu-puzzle-save-as',     enabledWhen: (s) => s.inEditor },
    { id: 'menu-puzzle-rename',      enabledWhen: (s) => s.inEditor && s.hasName },
    { id: 'menu-puzzle-close',       enabledWhen: (s) => s.inEditor && !s.wordEditorOpen },
    { id: 'menu-puzzle-delete',      enabledWhen: () => true },
    { id: 'menu-puzzle-title',       enabledWhen: (s) => s.mode === 'puzzle' },
    { id: 'menu-puzzle-grid-mode',   enabledWhen: (s) => s.mode === 'puzzle' },
    { id: 'menu-puzzle-puzzle-mode', enabledWhen: (s) => s.mode === 'grid' },

    // Importing opens the imported puzzle, so it's only offered from the dashboard
    { id: 'menu-import-puz',         enabledWhen: (s) => s.onDashboard },
    { id: 'menu-import-acrosslite',  enabledWhen: (s) => s.onDashboard },
    { id: 'menu-import-ipuz',        enabledWhen: (s) => s.onDashboard },
    { id: 'menu-import-xd',          enabledWhen: (s) => s.onDashboard },
    { id: 'menu-import-ccxml',       enabledWhen: (s) => s.onDashboard },

    // Exporting works on the open puzzle, or asks which one from the dashboard
    { id: 'menu-export-puz',         enabledWhen: () => true },
    { id: 'menu-export-acrosslite',  enabledWhen: () => true },
    { id: 'menu-export-ipuz',        enabledWhen: () => true },
    { id: 'menu-export-xd',          enabledWhen: () => true },
    { id: 'menu-export-cwcompiler',  enabledWhen: () => true },
    { id: 'menu-export-nytimes',     enabledWhen: () => true },
    { id: 'menu-export-solver-pdf',  enabledWhen: () => true },
    { id: 'menu-export-solved-pdf',  enabledWhen: () => true },
];

function updateMenu() {
    const context = _menuContext();
    for (const rule of MENU_RULES) {
        setMenuItemEnabled(rule.id, rule.enabledWhen(context));
    }
}

function _menuContext() {
    const inEditor = AppState.view === 'editor';
    return {
        onDashboard: AppState.view === 'dashboard',
        inEditor,
        hasName: !!AppState.puzzleName,
        mode: inEditor ? _currentEditorMode() : null,
        wordEditorOpen: _isWordEditorOpen(),
    };
}

function setMenuItemEnabled(id, enabled) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('w3-disabled', !enabled);
    el.style.pointerEvents = enabled ? '' : 'none';
    el.setAttribute('aria-disabled', enabled ? 'false' : 'true');
    el.tabIndex = enabled ? 0 : -1;
}

// ---------------------------------------------------------------------------
// View management
// ---------------------------------------------------------------------------

function showView(view) {
    // 'home' is an alias for the dashboard, which replaced the welcome screen.
    if (view === 'home') view = 'dashboard';
    AppState.view = view;
    updateMenu();
    const workspace = document.getElementById('workspace');
    document.getElementById('lhs').innerHTML = '';
    document.getElementById('rhs').innerHTML = '';
    if (workspace) workspace.classList.toggle('workspace--full', view === 'dashboard');
    switch (view) {
        case 'dashboard':
            updateAppBarPuzzleInfo();
            renderActionBar();
            renderDashboard();
            break;
        case 'editor':
            renderPuzzleEditor();
            break;
        default:
            renderActionBar();
            document.getElementById('lhs').innerHTML =
                `<div class="home-welcome"><p>Unknown view: ${view}</p></div>`;
    }
}
