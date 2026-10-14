// Crossword Puzzle Editor — enabling and disabling the top menu's items

import { AppState } from '../core/state.js';
import { _currentEditorMode } from '../editor/editor.js';
import { _isWordEditorOpen } from '../editor/selection.js';

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

export function updateMenu() {
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
    el.classList.toggle('is-disabled', !enabled);
    el.style.pointerEvents = enabled ? '' : 'none';
    el.setAttribute('aria-disabled', enabled ? 'false' : 'true');
    el.tabIndex = enabled ? 0 : -1;
}
