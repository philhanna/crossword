# Standalone Desktop App (PyInstaller)

## Goal

Bundle the crossword app as a standalone desktop executable for offline use. No Python install,
no config required. User double-clicks `crossword.exe`, browser opens automatically.

## How PyInstaller works

PyInstaller bundles the Python interpreter, all dependencies, and the app's files into a single
folder. On Windows the user distributes that folder and double-clicks `crossword.exe`.

## Changes required

### 1. Launcher entry point — `crossword/desktop.py` (~30 lines)

- Starts the HTTP server in a background thread
- Picks a free port (avoids conflicts if already in use)
- Calls `webbrowser.open("http://localhost:<port>")` after a short delay
- Blocks until the user closes the window / kills the process

### 2. Resource path helper (~10 lines)

PyInstaller extracts bundled files to a temp dir (`sys._MEIPASS`). The server currently locates
`frontend/` relative to the source tree. A small helper redirects those lookups when running as
a bundled app.

### 3. SQLite data path

The DB file needs a stable home outside the bundle:

- Windows: `%APPDATA%/crossword/crossword.db`
- Linux/Mac: `~/.local/share/crossword/crossword.db`

The config system already supports SQLite — just default to this path when no config file exists.

### 4. PyInstaller `.spec` file

- Includes `frontend/` (HTML/CSS/JS) and word list files as data
- Sets `--noconsole` so no terminal window appears on Windows

## Windows-specific gotchas

- **Build on Windows** — PyInstaller is not cross-platform. A `.exe` must be built on Windows.
  Options: use a Windows machine directly, or a GitHub Actions workflow with a `windows-latest`
  runner that builds and uploads the `.exe` as a release artifact.
- **Antivirus false positives** — PyInstaller executables sometimes trigger Windows Defender.
  Code-signing fixes this (~$300/yr for a certificate). For personal use, "run anyway" is fine.
- **No installer** — Distribute a `.zip` of the output folder, not a `.msi`. An actual installer
  (e.g. Inno Setup) is optional extra work.

## Effort estimate

| Task                               | Effort    |
|------------------------------------|-----------|
| `desktop.py` launcher              | 1–2 hours |
| Resource path helper + wiring      | 1 hour    |
| SQLite default path logic          | 30 min    |
| PyInstaller `.spec` file           | 1 hour    |
| GitHub Actions Windows build       | 1–2 hours |
| Testing on Windows                 | variable  |

**Total: roughly one day of work**, assuming access to a Windows machine for final testing.

## End result

A `crossword.exe` (a folder with an exe) that:

- Runs fully offline, single-user (no login required)
- Stores data in `%APPDATA%/crossword/`
- Opens the browser automatically on launch
- Requires no Python or config file
