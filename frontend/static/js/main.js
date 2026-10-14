// Crossword Puzzle Editor — startup
//
// The page loads this one module; it pulls in the rest. Module scripts run
// once the page has been parsed, so the DOM is ready by the time start() runs.

import './legacy-globals.js';
import { setMessageLineTimeout } from './state.js';
import { apiFetch, positionMessageLine, showView } from './ui.js';

start();

async function start() {
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
