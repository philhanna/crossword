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

async function apiFetch(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const resp = await fetch(path, opts);
    return resp.json();
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

function inputBox(title, label, value, onSubmit) {
    document.getElementById('ib-title').innerHTML = title;
    document.getElementById('ib-label').innerHTML = label;
    document.getElementById('ib-input').value = value;
    const form = document.getElementById('ib-form');
    form.onsubmit = (e) => {
        e.preventDefault();
        const entered = document.getElementById('ib-input').value;
        hideElement('ib');
        onSubmit(entered);
    };
    showElement('ib');
    document.getElementById('ib-input').focus();
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

async function rejectIfNameExists(kind, name, listExistingNames) {
    const existingNames = await listExistingNames();
    if (!existingNames.includes(name)) {
        return false;
    }
    messageBox(
        `Duplicate ${kind} name`,
        `${kind.charAt(0).toUpperCase() + kind.slice(1)} <b>${escapeHtml(name)}</b> already exists. Choose a different ${kind} name when creating a new ${kind}.`,
        null,
        null
    );
    return true;
}

function showChooser(title, items, onSelect) {
    document.getElementById('ch-title').innerHTML = title;
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '';
    for (const item of items) {
        const a = document.createElement('a');
        a.className = 'w3-bar-item w3-button w3-block w3-left-align';
        a.textContent = item;
        a.onclick = () => { hideElement('ch'); onSelect(item); };
        listEl.appendChild(a);
    }
    showElement('ch');
}

const CH_PAGE_SIZE = 5;
let _chPreviews  = [];
let _chPage      = 0;
let _chOnSelect  = null;
let _chSortOrder = 'recent';

async function showPreviewChooser(title, names, apiPrefix, onSelect) {
    _chPreviews  = [];
    _chPage      = 0;
    _chOnSelect  = onSelect;
    _chSortOrder = 'recent';
    document.querySelector('input[name="ch-sort"][value="recent"]').checked = true;

    document.getElementById('ch-title').innerHTML = title;
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '<div class="w3-container w3-padding">Loading previews…</div>';
    document.getElementById('ch-pagination').style.display = 'none';
    showElement('ch');

    _chPreviews = await Promise.all(
        names.map(name =>
            apiFetch('GET', `${apiPrefix}/${encodeURIComponent(name)}/preview`)
                .catch(() => ({ name, heading: name, svgstr: '', error: true }))
        )
    );

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
function chPageFirst() { _chPage = 0; _chRender(); }
function chPagePrev()  { if (_chPage > 0) { _chPage--; _chRender(); } }
function chPageNext()  { if ((_chPage + 1) * CH_PAGE_SIZE < _chPreviews.length) { _chPage++; _chRender(); } }
function chPageLast()  { _chPage = Math.ceil(_chPreviews.length / CH_PAGE_SIZE) - 1; _chRender(); }

// ---------------------------------------------------------------------------
// Menu enable / disable
// ---------------------------------------------------------------------------

const MENU_ITEMS = [
    'menu-puzzle-new', 'menu-puzzle-open',
    'menu-puzzle-save', 'menu-puzzle-save-as', 'menu-puzzle-rename', 'menu-puzzle-close', 'menu-puzzle-delete',
    'menu-puzzle-title', 'menu-puzzle-grid-mode', 'menu-puzzle-puzzle-mode',
    'menu-import-acrosslite', 'menu-import-puz', 'menu-import-xd',
    'menu-export-acrosslite', 'menu-export-puz', 'menu-export-xd', 'menu-export-cwcompiler', 'menu-export-nytimes', 'menu-export-solver-pdf',
];

function menuEnable(id)  {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('w3-disabled');
    el.style.pointerEvents = '';
    el.setAttribute('aria-disabled', 'false');
    el.tabIndex = 0;
}

function menuDisable(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('w3-disabled');
    el.style.pointerEvents = 'none';
    el.setAttribute('aria-disabled', 'true');
    el.tabIndex = -1;
}

function updateMenu() {
    const home   = AppState.view === 'home';
    const editor = AppState.view === 'editor';
    const canClosePuzzle = editor && !_isWordEditorOpen();

    home   ? menuEnable('menu-puzzle-new')     : menuDisable('menu-puzzle-new');
    home   ? menuEnable('menu-puzzle-open')    : menuDisable('menu-puzzle-open');
    home   ? menuEnable('menu-import-acrosslite')  : menuDisable('menu-import-acrosslite');
    home   ? menuEnable('menu-import-puz')         : menuDisable('menu-import-puz');
    home   ? menuEnable('menu-import-xd')          : menuDisable('menu-import-xd');
    editor ? menuEnable('menu-puzzle-save')    : menuDisable('menu-puzzle-save');
    editor ? menuEnable('menu-puzzle-save-as') : menuDisable('menu-puzzle-save-as');
    (editor && AppState.puzzleName) ? menuEnable('menu-puzzle-rename') : menuDisable('menu-puzzle-rename');
    canClosePuzzle ? menuEnable('menu-puzzle-close') : menuDisable('menu-puzzle-close');
    menuEnable('menu-puzzle-delete');

    const mode = editor ? _currentEditorMode() : null;
    mode === 'puzzle' ? menuEnable('menu-puzzle-title')       : menuDisable('menu-puzzle-title');
    mode === 'puzzle' ? menuEnable('menu-puzzle-grid-mode')   : menuDisable('menu-puzzle-grid-mode');
    mode === 'grid'   ? menuEnable('menu-puzzle-puzzle-mode') : menuDisable('menu-puzzle-puzzle-mode');

    menuEnable('menu-export-acrosslite');
    menuEnable('menu-export-puz');
    menuEnable('menu-export-xd');
    menuEnable('menu-export-cwcompiler');
    menuEnable('menu-export-nytimes');
    menuEnable('menu-export-solver-pdf');
}

// ---------------------------------------------------------------------------
// View management
// ---------------------------------------------------------------------------

function showView(view) {
    AppState.view = view;
    updateMenu();
    document.getElementById('lhs').innerHTML = '';
    document.getElementById('rhs').innerHTML = '';
    switch (view) {
        case 'home':
            updateAppBarPuzzleInfo();
            renderActionBar();
            renderHome();
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

function renderHome() {
    document.getElementById('lhs').innerHTML =
        `<div class="home-welcome">
  <p>Use the Puzzle menu to create or open a crossword for editing.</p>
</div>`;
}
