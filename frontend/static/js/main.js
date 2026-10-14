// Crossword Puzzle Editor — startup
//
// The page loads this one module; it pulls in the rest, each of which
// registers its data-action handlers as it loads. Module scripts run once the
// page has been parsed, so the DOM is ready by the time start() runs.

import { listenForActions } from './core/actions.js';
import { setMessageLineTimeout } from './state.js';
import { apiFetch, positionMessageLine, showView } from './ui.js';
import './dashboard.js';
import './puzzle-editor.js';
import './word-editor.js';
import './settings.js';

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
