// Crossword Puzzle Editor — the message box and input box dialogs

import { registerActions } from '../core/actions.js';
import { escapeHtml, hideElement, showElement } from '../core/dom.js';

registerActions({
    'close-dialog': (el) => { el.closest('.w3-modal').style.display = 'none'; },
});

export function messageBox(title, prompt, ok, okCallback, okLabel = 'OK') {
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

export function inputBox(title, label, value, onSubmit, { required = true, onCancel = null } = {}) {
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

export function multiInputBox(title, fields, onSubmit, { onCancel = null } = {}) {
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
