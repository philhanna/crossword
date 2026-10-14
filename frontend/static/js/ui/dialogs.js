// Crossword Puzzle Editor — the message box and input box dialogs
//
// Each function opens a dialog and returns a promise that settles when the
// user closes it, so a sequence of questions reads top to bottom:
//
//     const name = await askText('Save as', 'Puzzle name:');
//     if (name === null) return;   // cancelled
//
// Titles, labels and prompts are HTML; escape any user text in them.

import { registerActions } from '../core/actions.js';
import { escapeHtml, hideElement, showElement } from '../core/dom.js';

registerActions({
    'close-dialog':       (el) => { el.closest('.modal').style.display = 'none'; },
    'message-box-ok':     () => closeMessageBox(true),
    'message-box-cancel': () => closeMessageBox(false),
    'input-box-submit':   (el, e) => { e.preventDefault(); closeInputBox(true); },
    'input-box-cancel':   () => closeInputBox(false),
});

// ---------------------------------------------------------------------------
// Message box (OK / Cancel)
// ---------------------------------------------------------------------------

// Resolves the open message box's promise; null when none is open
let messageBoxDone = null;

// Ask a yes/no question. Resolves true for OK, false for Cancel or ×.
export function askConfirm(title, prompt, okLabel = 'OK') {
    return openMessageBox(title, prompt, okLabel);
}

// Tell the user something. Resolves when they close the box either way.
export async function showAlert(title, prompt) {
    await openMessageBox(title, prompt, 'OK');
}

function openMessageBox(title, prompt, okLabel) {
    closeMessageBox(false);  // settle any box this one replaces
    document.getElementById('mb-title').innerHTML = title;
    document.getElementById('mb-prompt').innerHTML = prompt;
    document.getElementById('mb-ok').textContent = okLabel;
    showElement('mb');
    return new Promise(resolve => { messageBoxDone = resolve; });
}

function closeMessageBox(result) {
    const done = messageBoxDone;
    messageBoxDone = null;
    if (!done) return;
    hideElement('mb');
    done(result);
}

// ---------------------------------------------------------------------------
// Input box (one or more text fields + OK / Cancel)
// ---------------------------------------------------------------------------

// Resolves the open input box's promise; collectValues reads its fields
let inputBoxDone = null;
let collectValues = null;

// Ask for one line of text. Resolves to what was typed, or null on Cancel.
export function askText(title, label, value = '', { required = true } = {}) {
    const fieldsHtml = `
      <div class="form-field">
        <label id="ib-label" class="form-label">${label}</label>
        <input type="text" id="ib-input" name="ib-input" class="form-input"${required ? ' required' : ''}>
      </div>`;
    return openInputBox(title, fieldsHtml, () => {
        const input = document.getElementById('ib-input');
        input.value = value;
        return () => input.value;
    });
}

// Ask for several fields at once: fields is [{ name, label, value?, required? }].
// Resolves to { name: value, ... }, or null on Cancel.
export function askFields(title, fields) {
    const fieldsHtml = fields.map((field, idx) => `
      <div class="form-field">
        <label class="form-label" for="ib-input-${idx}">${field.label}</label>
        <input type="text" id="ib-input-${idx}" name="${field.name}" class="form-input"
               value="${escapeHtml(field.value || '')}"${field.required === false ? '' : ' required'}>
      </div>`).join('');
    return openInputBox(title, fieldsHtml, () => () => {
        const values = {};
        fields.forEach((field, idx) => {
            values[field.name] = document.getElementById(`ib-input-${idx}`).value;
        });
        return values;
    });
}

// Show the input box with the given fields. setUp fills them in once they
// are on the page and returns the function that reads them back on OK.
function openInputBox(title, fieldsHtml, setUp) {
    closeInputBox(false);  // settle any box this one replaces
    document.getElementById('ib-title').innerHTML = title;
    document.getElementById('ib-prompt').innerHTML = '';
    document.getElementById('ib-fields').innerHTML = fieldsHtml;
    collectValues = setUp();
    showElement('ib');
    const first = document.querySelector('#ib-fields input');
    if (first) first.focus();
    return new Promise(resolve => { inputBoxDone = resolve; });
}

function closeInputBox(submitted) {
    const done = inputBoxDone;
    inputBoxDone = null;
    if (!done) return;
    const result = submitted ? collectValues() : null;
    hideElement('ib');
    done(result);
}
