// Crossword Puzzle Editor — settings dialog and bootstrap

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

const SETTINGS_SCHEMA = [
  {
    key: 'server',
    title: 'Server',
    desc: 'Server host and port settings.',
    fields: [
      {
        key: 'host',
        label: 'Host',
        type: 'text',
      },
      {
        key: 'port',
        label: 'Port',
        type: 'text',
      },
    ],
  },
  {
    key: 'dbfile',
    title: 'dbfile',
    desc: 'Fully qualified path to the SQLite 3 database',
    fields: [
      {
        key: 'dbfile',
        label: 'Value',
        type: 'text',
      },
    ],
  },
  {
    key: 'word_file',
    title: 'word_file',
    desc: 'Fully qualified path to the ASCII word list file',
    fields: [
      {
        key: 'word_file',
        label: 'Value',
        type: 'text',
      },
    ],
  },
  {
    key: 'log_level',
    title: 'log_level',
    desc: 'One of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET',
    fields: [
      {
        key: 'log_level',
        label: 'Value',
        type: 'select',
        choices: ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
      },
    ],
  },
  {
    key: 'message_line_timeout_ms',
    title: 'message_line_timeout_ms',
    desc: 'How many milliseconds for the message line to remain visible',
    fields: [
      {
        key: 'message_line_timeout_ms',
        label: 'Value',
        type: 'text',
      },
    ],
  },
  {
    key: 'theme_color',
    title: 'theme_color',
    desc: 'Theme color in RGB notation, like #FFFFF2',
    fields: [
      {
        key: 'theme_color',
        label: 'Value',
        type: 'text',
      },
    ],
  },
  {
    key: 'author',
    title: 'Author',
    desc: 'NYTimes submission: author info printed on the grid page',
    fields: [
      {
        key: 'author_name',
        label: 'Name',
        type: 'text',
      },
      {
        key: 'author_address',
        label: 'Address',
        type: 'text',
      },
      {
        key: 'author_email',
        label: 'Email',
        type: 'text',
      },
    ],
  },
];

const SETTINGS_FIELDS = SETTINGS_SCHEMA.flatMap((tab) => tab.fields);

function _activateSettingsTab(key) {
    const tabs = document.querySelectorAll('.settings-tab');
    const panels = document.querySelectorAll('.settings-panel-card');

    for (const tab of tabs) {
        const isActive = tab.dataset.key === key;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
        tab.setAttribute('tabindex', isActive ? '0' : '-1');
    }

    for (const panel of panels) {
        const isActive = panel.dataset.key === key;
        panel.classList.toggle('active', isActive);
        panel.hidden = !isActive;
    }
}

function _renderSettingsRows(values) {
    const tabs = document.getElementById('settings-tabs');
    const panels = document.getElementById('settings-panels');
    tabs.innerHTML = '';
    panels.innerHTML = '';

    for (const tabDef of SETTINGS_SCHEMA) {
        const tab = document.createElement('button');
        tab.type = 'button';
        tab.className = 'settings-tab';
        tab.id = `settings-tab-${tabDef.key}`;
        tab.dataset.key = tabDef.key;
        tab.setAttribute('role', 'tab');
        tab.setAttribute('aria-controls', `settings-panel-${tabDef.key}`);
        tab.textContent = tabDef.title;
        tab.addEventListener('click', () => _activateSettingsTab(tabDef.key));
        tabs.appendChild(tab);

        const panel = document.createElement('section');
        panel.id = `settings-panel-${tabDef.key}`;
        panel.className = 'settings-panel-card';
        panel.dataset.key = tabDef.key;
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('aria-labelledby', `settings-tab-${tabDef.key}`);

        const title = document.createElement('h2');
        title.className = 'settings-panel-title';
        title.textContent = tabDef.title;
        panel.appendChild(title);

        const desc = document.createElement('p');
        desc.className = 'settings-panel-desc';
        desc.textContent = tabDef.desc || 'No description available.';
        panel.appendChild(desc);

        for (const field of tabDef.fields) {
            const formField = document.createElement('div');
            formField.className = 'settings-form-field';

            const label = document.createElement('label');
            label.className = 'settings-input-label';
            label.setAttribute('for', `setting-${field.key}`);
            label.textContent = field.label;
            formField.appendChild(label);

            let control;
            if (field.type === 'select') {
                control = document.createElement('select');
                for (const ch of field.choices) {
                    const opt = document.createElement('option');
                    opt.value = ch;
                    opt.textContent = ch;
                    if (ch === (values[field.key] ?? '')) opt.selected = true;
                    control.appendChild(opt);
                }
            } else {
                control = document.createElement('input');
                control.type = 'text';
                control.value = values[field.key] ?? '';
            }
            control.id = `setting-${field.key}`;
            control.className = 'settings-input';
            formField.appendChild(control);
            panel.appendChild(formField);
        }
        panels.appendChild(panel);
    }

    if (SETTINGS_SCHEMA.length > 0) {
        _activateSettingsTab(SETTINGS_SCHEMA[0].key);
    }
}

async function do_settings() {
    try {
        const values = await apiFetch('GET', '/api/settings');
        _renderSettingsRows(values);
        showElement('settings-panel');
    } catch (e) {
        showMessageLine('Failed to load settings.', 'error');
    }
}

async function do_settings_save() {
    const values = {};
    for (const field of SETTINGS_FIELDS) {
        const el = document.getElementById(`setting-${field.key}`);
        if (el) values[field.key] = el.value;
    }
    try {
        const result = await apiFetch('PUT', '/api/settings', values);
        hideElement('settings-panel');
        if (result.restart_required) {
            showMessageLine('Settings saved. Restart the server for some changes to take effect.', 'notice', 0);
        } else {
            showMessageLine('Settings saved.');
        }
    } catch (e) {
        showMessageLine('Failed to save settings.', 'error');
    }
}

function do_settings_cancel() {
    hideElement('settings-panel');
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const cfg = await (await fetch('/api/config')).json();
        if (cfg.message_line_timeout_ms != null) {
            MESSAGE_LINE_TIMEOUT_MS = cfg.message_line_timeout_ms;
        }
    } catch (e) { /* use default */ }

    positionMessageLine();
    window.addEventListener('scroll', positionMessageLine, { passive: true });
    window.addEventListener('resize', positionMessageLine);
    showView('home');
});
