# Publish Feature — Implementation Plan

The Publish menu offers three export formats for puzzles:
- **Across Lite** (`.puz` ZIP) — `do_publish('puz')`
- **Crossword Compiler** (`.xml`) — `do_publish('xml')`
- **New York Times** (HTML + SVG ZIP) — `do_publish('nyt')`

All backend scaffolding (port, use cases, handlers, routes) is in place.
The export adapter is the missing piece; the frontend stub needs replacing.

---

## 1 — Backend: Export Adapter

Create `crossword/adapters/export_adapter.py` implementing `ExportPort`.

### 1a — AcrossLite format

- [ ] Study the AcrossLite text format spec (`.txt`): title, author, copyright, grid,
      across clues, down clues sections
- [ ] Implement `export_puzzle_to_acrosslite(puzzle) -> bytes`
  - Build the `.txt` file from puzzle grid + clues
  - Bundle `.txt` + `.json` (full puzzle backup) into a ZIP archive
  - Return ZIP as bytes

### 1b — Crossword Compiler XML format

- [ ] Implement `export_puzzle_to_xml(puzzle) -> str`
  - Emit well-formed XML with grid layout, numbered squares, and clue entries
  - Return XML string (UTF-8)

### 1c — New York Times submission format

- [ ] Implement `export_puzzle_to_nytimes(puzzle) -> bytes`
  - Generate an HTML clue sheet (title, author, copyright, across/down clues)
  - Generate an SVG grid image (numbered squares, black cells)
  - Bundle both into a ZIP archive
  - Return ZIP as bytes

### 1d — Stub out unused grid exports

- [ ] Add minimal `export_grid_to_pdf` and `export_grid_to_png` stubs that raise
      `ExportError("not implemented")` so the class satisfies the ABC contract

### 1e — Tests

- [ ] Write `crossword/tests/adapters/test_export_adapter.py` with a real `Puzzle`
      fixture; assert output is non-empty bytes/str with expected structural markers
      (e.g. `<ACROSS>` in `.txt`, root element in XML, ZIP magic bytes)

---

## 2 — Backend: Wire the Adapter

- [ ] In `crossword/wiring/__init__.py`, replace `export_adapter = None` with
      `export_adapter = ExportAdapter()` and import it
- [ ] Verify `export_uc` is no longer `None` in `AppContainer`

---

## 3 — Backend: HTTP Response Headers

The export handlers currently return raw bytes/strings; the server must also send
the correct `Content-Type` and `Content-Disposition` headers so browsers trigger
a file download.

- [ ] Investigate how other handlers (e.g. SVG preview) set custom response headers
- [ ] Update `handle_export_puzzle_to_acrosslite` — `application/zip`,
      `Content-Disposition: attachment; filename="<name>.zip"`
- [ ] Update `handle_export_puzzle_to_xml` — `application/xml`,
      `Content-Disposition: attachment; filename="<name>.xml"`
- [ ] Update `handle_export_puzzle_to_nytimes` — `application/zip`,
      `Content-Disposition: attachment; filename="<name>_nytimes.zip"`

---

## 4 — Frontend: `do_publish(format)` in `app.js`

Replace the Phase 5 stub with a real implementation.

### 4a — Determine the target puzzle

- [ ] If `AppState.view === 'puzzle-editor'`, use `AppState.puzzleName` directly
- [ ] Otherwise, invoke the preview chooser to let the user pick a puzzle first,
      then continue with the chosen name

### 4b — Trigger the download

- [ ] Build the export URL:
  - `puz` → `GET /api/export/puzzles/<name>/acrosslite`
  - `xml` → `GET /api/export/puzzles/<name>/xml`
  - `nyt` → `GET /api/export/puzzles/<name>/nytimes`
- [ ] Use `fetch()` to get the response as a `Blob`, create an object URL,
      click a temporary `<a download="...">` element, then revoke the URL
- [ ] On HTTP error, show a message-box with the server's error text

---

## 5 — End-to-end smoke test

- [ ] Open a completed puzzle in the puzzle editor
- [ ] Publish → Across Lite: confirm ZIP downloads and `.txt` content is valid
- [ ] Publish → Crossword Compiler: confirm `.xml` downloads and is well-formed
- [ ] Publish → New York Times: confirm ZIP downloads and contains `.html` + `.svg`
- [ ] From home view (no puzzle open): confirm chooser appears, selection triggers download
