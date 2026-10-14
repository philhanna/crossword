// Crossword Puzzle Editor — the message line under the app bar

import { registerActions } from '../core/actions.js';
import { ApiError } from '../core/api.js';

registerActions({
    'message-line-close': () => clearMessageLine(),
});

// timeoutMs: how long a notice stays up, from /api/config at startup.
// timer: the pending timeout that will clear the line, if any.
const messageLine = { timeoutMs: 3000, timer: null };

export function messageLineTimeout() {
    return messageLine.timeoutMs;
}

export function setMessageLineTimeout(ms) {
    messageLine.timeoutMs = ms;
}

export function showMessageLine(text, level = 'notice', timeoutMs = messageLine.timeoutMs) {
    (level === 'error' ? console.error : console.log)(`[${level}] ${text}`);
    const ml = document.getElementById('ml');
    document.getElementById('ml-text').textContent = text;
    ml.classList.remove('message-line-notice', 'message-line-error');
    ml.classList.add(level === 'error' ? 'message-line-error' : 'message-line-notice');
    positionMessageLine();
    ml.style.display = 'flex';
    if (messageLine.timer) {
        clearTimeout(messageLine.timer);
        messageLine.timer = null;
    }
    if (timeoutMs > 0) {
        messageLine.timer = setTimeout(() => {
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
    if (messageLine.timer) {
        clearTimeout(messageLine.timer);
        messageLine.timer = null;
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
