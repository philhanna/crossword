# Settings Feature Design

## Overview

Add a Settings screen to the frontend that lets the user view and edit the
application configuration. The set of editable keys, their descriptions, and
their control types are a static snapshot hardcoded in the frontend as
`SETTINGS_SCHEMA` (derived from `samples/config.yaml` at design time, not
loaded at runtime). The current values are read at runtime from
`~/.config/crossword/config.yaml` (the user's installed config file).

---

## Menu Entry

Add a **Settings…** button to the app bar, to the left of Help, always enabled
(no state gating):

```html
<!-- in index.html, inside <nav id="top-menu"> -->
<a class="app-nav-btn" onclick="do_settings()">Settings…</a>
```

Like Help, it is a plain `<a>` — no dropdown, always clickable regardless of
whether a grid or puzzle is open.

---

## Settings Screen

Settings opens as a **full-screen modal panel** (a new `<div id="settings-panel">`),
overlaying the workspace. It is not one of the three editor states; it is a
layer on top, dismissed with Cancel or Save.

### Layout

Each key is preceded by a full-width description row (spanning both columns)
drawn from the comment above that key in `samples/config.yaml`.

```
┌──────────────────────────────────────────────────────────┐
│  Settings                                         [✕]    │
├──────────────────────────────────────────────────────────┤
│  IP address the server will bind to                      │
│  host                    │  [text input                ]  │
│                                                          │
│  TCP port the server will listen on                      │
│  port                    │  [text input                ]  │
│                                                          │
│  Fully qualified path to the SQLite 3 database           │
│  dbfile                  │  [text input                ]  │
│                                                          │
│  Fully qualified path to the ASCII word list file        │
│  word_file               │  [text input                ]  │
│                                                          │
│  One of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET    │
│  log_level               │  [dropdown ▾               ]  │
│                                                          │
│  How many milliseconds for the message line to remain    │
│  visible                                                 │
│  message_line_timeout_ms │  [text input                ]  │
│                                                          │
│  NYTimes submission: author info printed on the grid     │
│  page                                                    │
│  author_name             │  [text input                ]  │
│  author_address          │  [text input                ]  │
│  author_email            │  [text input                ]  │
├──────────────────────────────────────────────────────────┤
│                                  [Cancel]   [Save]       │
└──────────────────────────────────────────────────────────┘
```

- Description row: spans both columns, styled as subdued italicized text,
  no top padding, sits flush above its key row.
- Left column: key name, right-aligned, styled as a label.
- Right column: input control, left-aligned, full width of the column.
- `log_level` renders as a `<select>` with options: `CRITICAL`, `ERROR`,
  `WARNING`, `INFO`, `DEBUG`, `NOTSET` (in that order).
- All other keys render as `<input type="text">`.
- Keys that share a comment block in `samples/config.yaml` (e.g.
  `author_name`, `author_address`, `author_email`) share one description row
  above the first of them; the remaining sibling keys have no description row.
- The panel is wide enough to avoid wrapping long file paths (min-width ~640 px).

### Keys (from `samples/config.yaml`)

| Key                        | Control type | Description (from config comment)                          |
|----------------------------|--------------|------------------------------------------------------------|
| `host`                     | text         | IP address the server will bind to                         |
| `port`                     | text         | TCP port the server will listen on                         |
| `dbfile`                   | text         | Fully qualified path to the SQLite 3 database              |
| `word_file`                | text         | Fully qualified path to the ASCII word list file           |
| `log_level`                | select       | One of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET       |
| `message_line_timeout_ms`  | text         | How many milliseconds for the message line to remain visible |
| `author_name`              | text         | NYTimes submission: author info printed on the grid page   |
| `author_address`           | text         | *(shares description with `author_name`)*                  |
| `author_email`             | text         | *(shares description with `author_name`)*                  |

Keys are displayed in the order defined by `SETTINGS_SCHEMA`.
If a key is absent from the user's installed config, its input renders empty.

---

## Backend — API Endpoints

### `GET /api/settings`

Returns the current user config values for the keys defined in
`samples/config.yaml`.

**Response** `200 OK`:

```json
{
  "host": "127.0.0.1",
  "port": "5000",
  "dbfile": "/home/user/crossword.db",
  "word_file": "/home/user/words.txt",
  "log_level": "INFO",
  "message_line_timeout_ms": "2000",
  "author_name": "Your Name",
  "author_address": "123 Main St, City, ST 12345",
  "author_email": "you@example.com"
}
```

All values are returned as strings. Keys missing from the installed config are
included with an empty string value `""`.

**Implementation notes:**

- The key list is fixed (it mirrors `SETTINGS_SCHEMA` in the frontend); the
  handler does not read `samples/config.yaml` at runtime.
- The handler reads `~/.config/crossword/config.yaml` and returns the values
  for those keys, coercing each to a string.

### `PUT /api/settings`

Writes updated values back to `~/.config/crossword/config.yaml`.

**Request body** (JSON, same shape as GET response):

```json
{
  "host": "127.0.0.1",
  "port": "5000",
  ...
}
```

**Behavior:**

- Merge the submitted values into the existing config file, preserving any
  keys in the installed config that are not part of the schema (e.g.
  `database_url` set via environment variable).
- Write the result back to `~/.config/crossword/config.yaml` using
  `yaml.safe_dump`.
- The server does **not** hot-reload the running config; a restart is required
  for server-side settings (host, port, log_level, dbfile, word_file) to take
  effect. The response body should include a `restart_required` boolean so the
  frontend can show an appropriate message.

**Response** `200 OK`:

```json
{ "restart_required": true }
```

`restart_required` is `true` when any of `host`, `port`, `log_level`,
`dbfile`, or `word_file` changed.

**Error responses:**

| Status | Condition |
|--------|-----------|
| `400`  | Malformed JSON body |
| `500`  | Config file could not be written (permissions, etc.) |

---

## Frontend — JavaScript

### `do_settings()`

Called by the Settings… menu item.

1. `fetch('GET /api/settings')` to retrieve current values.
2. Populate the settings panel inputs from the response.
3. Show `#settings-panel` (add CSS class `visible` or set `display: block`).

### `do_settings_save()`

Called by the Save button.

1. Collect values from all inputs into a JSON object.
2. `fetch('PUT /api/settings', { body: JSON.stringify(values) })`.
3. On success:
   - Hide the settings panel.
   - If `restart_required` is true, show a message:
     `"Settings saved. Restart the server for some changes to take effect."`
   - Otherwise show: `"Settings saved."`
4. On error, show the error on the message line.

### `do_settings_cancel()`

Called by Cancel or the ✕ button. Hides the panel without saving.

---

## HTML Structure

```html
<!-- Settings panel — add to index.html after the existing modals -->
<div id="settings-panel" class="settings-panel" style="display:none">
  <div class="settings-header">
    <span class="settings-title">Settings</span>
    <button class="settings-close-btn" onclick="do_settings_cancel()">✕</button>
  </div>
  <div class="settings-body">
    <table class="settings-table">
      <tbody id="settings-rows">
        <!-- populated by do_settings() -->
      </tbody>
    </table>
  </div>
  <div class="settings-footer">
    <button class="w3-button w3-white w3-border" onclick="do_settings_cancel()">Cancel</button>
    <button class="w3-button w3-black" onclick="do_settings_save()">Save</button>
  </div>
</div>
```

The table rows are generated dynamically by JavaScript from the GET response,
so the key order and control types are driven by a client-side schema constant
that mirrors `samples/config.yaml`:

```js
const SETTINGS_SCHEMA = [
  { key: 'host',
    desc: 'IP address the server will bind to',
    type: 'text' },
  { key: 'port',
    desc: 'TCP port the server will listen on',
    type: 'text' },
  { key: 'dbfile',
    desc: 'Fully qualified path to the SQLite 3 database',
    type: 'text' },
  { key: 'word_file',
    desc: 'Fully qualified path to the ASCII word list file',
    type: 'text' },
  { key: 'log_level',
    desc: 'One of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET',
    type: 'select',
    choices: ['CRITICAL','ERROR','WARNING','INFO','DEBUG','NOTSET'] },
  { key: 'message_line_timeout_ms',
    desc: 'How many milliseconds for the message line to remain visible',
    type: 'text' },
  { key: 'author_name',
    desc: 'NYTimes submission: author info printed on the grid page',
    type: 'text' },
  { key: 'author_address',
    type: 'text' },
  { key: 'author_email',
    type: 'text' },
];
```

When `desc` is present, the table rendering inserts a full-width row above the
key row:

```js
function renderSettingsRows(values) {
  const tbody = document.getElementById('settings-rows');
  tbody.innerHTML = '';
  for (const field of SETTINGS_SCHEMA) {
    if (field.desc) {
      const descRow = document.createElement('tr');
      descRow.className = 'settings-desc-row';
      const td = document.createElement('td');
      td.colSpan = 2;
      td.className = 'settings-desc';
      td.textContent = field.desc;
      descRow.appendChild(td);
      tbody.appendChild(descRow);
    }
    const row = document.createElement('tr');
    const labelTd = document.createElement('td');
    labelTd.className = 'settings-key';
    labelTd.textContent = field.key;
    const inputTd = document.createElement('td');
    let control;
    if (field.type === 'select') {
      control = document.createElement('select');
      control.id = `setting-${field.key}`;
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
      control.id = `setting-${field.key}`;
      control.value = values[field.key] ?? '';
    }
    inputTd.appendChild(control);
    row.appendChild(labelTd);
    row.appendChild(inputTd);
    tbody.appendChild(row);
  }
}
```

---

## CSS

Add to `static/css/style.css`:

```css
.settings-panel {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 1000;
  background: #fff;
  display: flex;
  flex-direction: column;
  min-width: 640px;
}
.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ccc;
}
.settings-title { font-size: 1.25rem; font-weight: 600; }
.settings-close-btn { background: none; border: none; font-size: 1.25rem; cursor: pointer; }
.settings-body { flex: 1; overflow-y: auto; padding: 1.5rem; }
.settings-table { width: 100%; border-collapse: collapse; }
.settings-table td { padding: 0.4rem 0.75rem; vertical-align: middle; }
.settings-desc-row td { padding: 0.75rem 0.75rem 0; }
.settings-desc {
  font-style: italic;
  font-size: 0.875rem;
  color: #666;
}
.settings-key {
  width: 220px;
  text-align: right;
  font-weight: 500;
  color: #444;
  white-space: nowrap;
}
.settings-table td:last-child { width: 100%; }
.settings-table input[type="text"],
.settings-table select {
  width: 100%;
  padding: 0.25rem 0.4rem;
  font-family: inherit;
  font-size: 0.95rem;
  border: 1px solid #bbb;
  border-radius: 3px;
}
.settings-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #ccc;
}
```

---

## Files to Change

| File | Change |
|------|--------|
| `frontend/index.html` | Add Settings… nav item; add `#settings-panel` HTML |
| `frontend/static/css/style.css` | Add settings panel CSS |
| `frontend/static/js/app.js` | Add `SETTINGS_SCHEMA`, `do_settings()`, `do_settings_save()`, `do_settings_cancel()` |
| `crossword/http_server.py` | Add routes `GET /api/settings` and `PUT /api/settings` |
| `crossword/adapters/settings_adapter.py` | New file: read/write config.yaml |

---

## Out of Scope

- Hot-reloading server config without a restart.
- Validation of field values (e.g. port must be numeric) — left to a follow-up.
- Creating the config file if it does not exist.
- Editing keys not present in `samples/config.yaml`.
