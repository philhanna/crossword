// Crossword Puzzle Editor — switching between the dashboard and the editor

import { registerActions } from '../core/actions.js';
import { AppState } from '../core/state.js';
import { updateMenu } from './menu.js';
import { renderDashboard } from '../dashboard/dashboard.js';
import { renderActionBar, renderPuzzleEditor, updateAppBarPuzzleInfo } from '../editor/editor.js';

registerActions({
    'show-dashboard': () => showView('dashboard'),
});

export function showView(view) {
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
