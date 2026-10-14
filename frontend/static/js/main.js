// Crossword Puzzle Editor — startup
//
// The page loads this one module; it pulls in the rest, each of which
// registers its data-action handlers as it loads. Module scripts run once the
// page has been parsed, so the DOM is ready by the time start() runs.

import { listenForActions } from './core/actions.js';
import { setMessageLineTimeout } from './state.js';
import { apiFetch, positionMessageLine, showView } from './ui.js';
import './dashboard.js';
import './settings.js';
import './editor/clues-panel.js';
import './editor/editor.js';
import './editor/fill-order-panel.js';
import './editor/grid-mode.js';
import './editor/stats-panel.js';
import './editor/word-editor.js';
import './puzzle-file/export.js';
import './puzzle-file/import.js';
import './puzzle-file/lifecycle.js';

start();

async function start() {
    listenForActions();
    try {
        const cfg = await apiFetch('GET', '/api/config');
        if (cfg.message_line_timeout_ms != null) {
            setMessageLineTimeout(cfg.message_line_timeout_ms);
        }
    } catch (e) { /* use default */ }

    positionMessageLine();
    window.addEventListener('scroll', positionMessageLine, { passive: true });
    window.addEventListener('resize', positionMessageLine);
    showView('home');
}
