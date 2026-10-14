// Crossword Puzzle Editor — the message line under the app bar

import { registerActions } from '../core/actions.js';
import { ApiError } from '../core/api.js';

registerActions({
    'message-line-close': () => clearMessageLine(),
});

export let MESSAGE_LINE_TIMEOUT_MS = 3000; // default; may be overridden by /api/config

export function setMessageLineTimeout(ms) {
    MESSAGE_LINE_TIMEOUT_MS = ms;
}

let _messageLineTimer = null;

export function showMessageLine(text, level = 'notice', timeoutMs = MESSAGE_LINE_TIMEOUT_MS) {
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

// Report a failed request on the message line: "<what>: <server message>"
// when the server explained itself, or just "<what>" when it didn't answer.
export function showRequestError(what, e, timeoutMs = 0) {
    const text = e instanceof ApiError ? `${what}: ${e.message}` : what;
    showMessageLine(text, 'error', timeoutMs);
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

export function positionMessageLine() {
    const ml = document.getElementById('ml');
    const ab = document.getElementById('action-bar');
    const appBar = document.querySelector('.app-bar');
    if (!ml || !appBar) return;
    const ref = (ab && ab.style.display !== 'none') ? ab : appBar;
    const rect = ref.getBoundingClientRect();
    ml.style.top = `${rect.bottom + 8}px`;
}
