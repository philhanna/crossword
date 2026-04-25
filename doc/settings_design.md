# Settings Feature Design

## Overview

Add a Settings screen to the frontend that lets the user view and edit the
application configuration. The set of editable keys is defined by
`samples/config.yaml` (the canonical schema). The current values are read from
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

```
┌─────────────────────────────────────────────────┐
│  Settings                                [✕]    │
├──────────────────────────┬──────────────────────┤
│  host                    │  [text input        ]│
│  port                    │  [text input        ]│
│  dbfile                  │  [text input        ]│
│  word_file               │  [text input        ]│
│  log_level               │  [dropdown ▾       ]│
│  message_line_timeout_ms │  [text input        ]│
│  author_name             │  [text input        ]│
│  author_address          │  [text input        ]│
│  author_email            │  [text input        ]│
├──────────────────────────┴──────────────────────┤
│                              [Cancel]   [Save]  │
└─────────────────────────────────────────────────┘
```

- Left column: key names, right-aligned, styled as labels.
- Right column: input controls, left-aligned, full width of the column.
- `log_level` renders as a `<select>` with options: `CRITICAL`, `ERROR`,
  `WARNING`, `INFO`, `DEBUG`, `NOTSET` (in that order).
- All other keys render as `<input type="text">`.
- The two columns together fill the modal body; the panel is wide enough to
  avoid wrapping long file paths (min-width ~640 px).

### Keys (from `samples/config.yaml`)

| Key                        | Control type | Notes                                      |
|----------------------------|--------------|--------------------------------------------|
| `host`                     | text         |                                            |
| `port`                     | text         |                                            |
| `dbfile`                   | text         | Full path                                  |
| `word_file`                | text         | Full path                                  |
| `log_level`                | select       | CRITICAL / ERROR / WARNING / INFO / DEBUG / NOTSET |
| `message_line_timeout_ms`  | text         |                                            |
| `author_name`              | text         |                                            |
| `author_address`           | text         |                                            |
| `author_email`             | text         |                                            |

Keys are displayed in the order they appear in `samples/config.yaml`.
If a key is present in `samples/config.yaml` but absent from the user's
installed config, its input renders empty.

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

- The handler reads the key list from `samples/config.yaml` (loaded once at
  startup or on each request — startup is preferred).
- It then reads `~/.config/crossword/config.yaml` and returns only the
  matching keys, coercing values to strings.

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
  { key: 'host',                       type: 'text'   },
  { key: 'port',                       type: 'text'   },
  { key: 'dbfile',                     type: 'text'   },
  { key: 'word_file',                  type: 'text'   },
  { key: 'log_level',                  type: 'select',
    choices: ['CRITICAL','ERROR','WARNING','INFO','DEBUG','NOTSET'] },
  { key: 'message_line_timeout_ms',    type: 'text'   },
  { key: 'author_name',                type: 'text'   },
  { key: 'author_address',             type: 'text'   },
  { key: 'author_email',               type: 'text'   },
];
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
.settings-table td:first-child {
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
