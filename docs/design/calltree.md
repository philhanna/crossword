# Backend Call Tree

This is a static call hierarchy of backend execution paths, rooted at `crossword.http_server.__main__.py`.

```text
crossword/http_server/__main__.py
└── __main__
    └── run_http_server()                       [crossword/http_server/main.py]
        ├── make_app(config)                    [crossword/wiring/__init__.py]
        │   ├── init_config()                   [crossword/__init__.py] (when config is None)
        │   ├── SQLitePersistenceAdapter(dbfile)
        │   ├── SQLiteDictionaryAdapter()
        │   │   ├── load_from_database(dbfile)
        │   │   └── load_from_file(word_file)   (fallback)
        │   ├── BasicExportAdapter()
        │   ├── GridUseCases(persistence)
        │   ├── PuzzleUseCases(persistence)
        │   ├── WordUseCases(word_adapter)
        │   └── ExportUseCases(persistence, export_adapter)
        ├── create_server(host, port)           [crossword/http_server/server.py]
        │   ├── Router()
        │   └── HTTPServer((host, port), RequestHandler)
        ├── register_routes(router)             [crossword/http_server/main.py]
        │   └── Router.add_route(method, regex, handler)
        └── start_server(server, router, app)
            └── server.serve_forever()
                └── RequestHandler.do_GET/do_POST/do_PUT/do_DELETE
                    └── RequestHandler._handle_request(method)
                        ├── urlparse(self.path)
                        ├── parse_qs(query)
                        ├── json.loads(body)                         (POST/PUT)
                        ├── _parse_session_token()
                        ├── Router.find_route(method, path)
                        │   └── Route.matches() + Route.extract_params()
                        ├── handler(..., app=AppContainer)
                        └── response encoding
                            ├── _send_json(dict)
                            ├── _send_bytes(bytes)
                            ├── _send_text(str)
                            └── _send_error(status, message)

Request Handlers (by route family)

Static routes
├── GET /                               -> handle_get_index
│   ├── get_frontend_dir()
│   ├── open(frontend/index.html)
│   └── request_handler._send_bytes(..., text/html)
└── GET /static/(.+)                    -> handle_get_static
    ├── get_frontend_dir()
    ├── path traversal checks
    ├── open(frontend/static/<file>)
    └── request_handler._send_bytes(..., inferred content-type)

Grid routes
├── GET /api/grids                      -> handle_list_grids
│   └── app.grid_uc.list_grids(user_id)
│       └── GridUseCases.list_grids
│           └── persistence.list_grids
│               └── SQLitePersistenceAdapter.list_grids (SELECT)
├── POST /api/grids                     -> handle_create_grid
│   ├── app.grid_uc.create_grid(user_id, name, size)
│   │   └── GridUseCases.create_grid
│   │       ├── Grid(size)
│   │       └── persistence.save_grid
│   │           └── SQLitePersistenceAdapter.save_grid
│   │               └── grid.to_json()
│   │                   ├── Grid.get_black_cells
│   │                   └── Grid.get_numbered_cells
│   └── app.grid_uc.load_grid(user_id, name)
│       └── GridUseCases.load_grid
│           └── persistence.load_grid
│               └── SQLitePersistenceAdapter.load_grid
│                   └── Grid.from_json
├── POST /api/grids/from-puzzle         -> handle_create_grid_from_puzzle
│   └── app.grid_uc.create_grid_from_puzzle(user_id, puzzle_name, grid_name)
│       └── GridUseCases.create_grid_from_puzzle
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── grid = puzzle.grid
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid
├── GET /api/grids/{name}               -> handle_load_grid
│   └── app.grid_uc.load_grid(...)      -> GridUseCases.load_grid -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
├── DELETE /api/grids/{name}            -> handle_delete_grid
│   └── app.grid_uc.delete_grid(...)
│       └── GridUseCases.delete_grid
│           └── persistence.delete_grid -> SQLitePersistenceAdapter.delete_grid (DELETE)
├── POST /api/grids/{name}/copy         -> handle_copy_grid
│   └── app.grid_uc.copy_grid(...)
│       └── GridUseCases.copy_grid
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid -> grid.to_json
├── POST /api/grids/{name}/open         -> handle_open_grid_for_editing
│   └── app.grid_uc.open_grid_for_editing(...)
│       └── GridUseCases.open_grid_for_editing
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid
├── PUT /api/grids/{name}/cells/{r}/{c} -> handle_toggle_black_cell
│   └── app.grid_uc.toggle_black_cell(...)
│       └── GridUseCases.toggle_black_cell
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           ├── Grid.is_black_cell
│           ├── Grid.add_black_cell / Grid.remove_black_cell
│           │   └── Grid.symmetric_point
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid -> grid.to_json
├── POST /api/grids/{name}/rotate       -> handle_rotate_grid
│   └── app.grid_uc.rotate_grid(...)
│       └── GridUseCases.rotate_grid
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           ├── Grid.rotate
│           │   ├── Grid.rotate_stack
│           │   ├── Grid.rotate_coordinates
│           │   └── Grid.add_black_cell(..., undo=False)
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid -> grid.to_json
├── POST /api/grids/{name}/undo         -> handle_undo_grid
│   └── app.grid_uc.undo_grid(...)
│       └── GridUseCases.undo_grid
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           ├── Grid.undo -> Grid.undoredo
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid
├── POST /api/grids/{name}/redo         -> handle_redo_grid
│   └── app.grid_uc.redo_grid(...)
│       └── GridUseCases.redo_grid
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           ├── Grid.redo -> Grid.undoredo
│           └── persistence.save_grid   -> SQLitePersistenceAdapter.save_grid
├── GET /api/grids/{name}/preview       -> handle_get_grid_preview
│   └── app.grid_uc.get_grid_preview(...)
│       └── GridUseCases.get_grid_preview
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           ├── GridToSVG(grid)
│           └── ToSVG.generate_xml
│               ├── generate_root
│               ├── generate_enclosing_square
│               ├── generate_vertical_lines
│               ├── generate_horizontal_lines
│               ├── generate_cells
│               └── generate_word_numbers
└── GET /api/grids/{name}/stats         -> handle_get_grid_stats
    └── app.grid_uc.get_grid_stats(...)
        └── GridUseCases.get_grid_stats
            ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
            └── Grid.get_statistics
                ├── Grid.validate
                │   ├── Grid.validate_interlock
                │   ├── Grid.validate_unchecked_squares
                │   └── Grid.validate_minimum_word_length
                ├── Grid.get_word_count
                └── Grid.get_word_lengths

Puzzle routes
├── GET /api/puzzles                    -> handle_list_puzzles
│   └── app.puzzle_uc.list_puzzles(...) -> PuzzleUseCases.list_puzzles -> SQLitePersistenceAdapter.list_puzzles
├── POST /api/puzzles                   -> handle_create_puzzle
│   ├── app.puzzle_uc.create_puzzle(...)
│   │   └── PuzzleUseCases.create_puzzle
│   │       ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│   │       ├── Puzzle(grid)
│   │       │   ├── Grid.get_black_cells
│   │       │   ├── Grid.get_numbered_cells
│   │       │   └── Puzzle.initialize_words
│   │       │       ├── AcrossWord(self, seq)
│   │       │       └── DownWord(self, seq)
│   │       └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle -> puzzle.to_json
│   └── app.puzzle_uc.load_puzzle(...)  -> PuzzleUseCases.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
├── GET /api/puzzles/{name}             -> handle_load_puzzle
│   └── app.puzzle_uc.load_puzzle(...)  -> PuzzleUseCases.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
├── DELETE /api/puzzles/{name}          -> handle_delete_puzzle
│   └── app.puzzle_uc.delete_puzzle(...) -> PuzzleUseCases.delete_puzzle -> SQLitePersistenceAdapter.delete_puzzle
├── POST /api/puzzles/{name}/copy       -> handle_copy_puzzle
│   └── app.puzzle_uc.copy_puzzle(...)
│       └── PuzzleUseCases.copy_puzzle
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle -> puzzle.to_json
├── POST /api/puzzles/{name}/open       -> handle_open_puzzle_for_editing
│   └── app.puzzle_uc.open_puzzle_for_editing(...)
│       └── PuzzleUseCases.open_puzzle_for_editing
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle
├── PUT /api/puzzles/{name}/title       -> handle_set_puzzle_title
│   └── app.puzzle_uc.set_puzzle_title(...)
│       └── PuzzleUseCases.set_puzzle_title
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── puzzle.title = title
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle
├── POST /api/puzzles/{name}/words/{seq}/{dir}/reset -> handle_reset_word
│   └── app.puzzle_uc.reset_word(...)
│       └── PuzzleUseCases.reset_word
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── word = puzzle.across_words[seq] | puzzle.down_words[seq]
│           ├── word.get_clear_word
│           │   ├── Word.get_crossing_words
│           │   │   └── AcrossWord.get_crossing_word / DownWord.get_crossing_word
│           │   │       └── puzzle.get_numbered_cell -> puzzle.get_down_word/get_across_word
│           │   ├── Word.is_complete
│           │   └── Word.get_text
│           ├── word.set_text
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle
├── PUT /api/puzzles/{name}/cells/{r}/{c} -> handle_set_cell_letter
│   └── app.puzzle_uc.set_cell_letter(...)
│       └── PuzzleUseCases.set_cell_letter
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── puzzle.is_black_cell
│           ├── puzzle.set_cell
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle
├── GET /api/puzzles/{name}/words/{seq}/{dir} -> handle_get_word_at
│   └── app.puzzle_uc.get_word_at(...)
│       └── PuzzleUseCases.get_word_at
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           └── return puzzle.across_words[seq] | puzzle.down_words[seq]
├── PUT /api/puzzles/{name}/words/{seq}/{dir} -> handle_set_word_clue
│   └── app.puzzle_uc.set_word_clue(...)
│       └── PuzzleUseCases.set_word_clue
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── (optional) puzzle.set_text(seq, direction, text)
│           │   ├── puzzle.get_word
│           │   └── Word.set_text -> puzzle.set_cell
│           ├── word.set_clue
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle
├── POST /api/puzzles/{name}/undo       -> handle_undo_puzzle
│   └── app.puzzle_uc.undo_puzzle(...)
│       └── PuzzleUseCases.undo_puzzle
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── puzzle.undo
│           │   ├── puzzle.get_text
│           │   └── puzzle.set_text(..., undo=False)
│           └── persistence.save_puzzle (if changed)
├── POST /api/puzzles/{name}/redo       -> handle_redo_puzzle
│   └── app.puzzle_uc.redo_puzzle(...)
│       └── PuzzleUseCases.redo_puzzle
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── puzzle.redo
│           │   ├── puzzle.get_text
│           │   └── puzzle.set_text(..., undo=False)
│           └── persistence.save_puzzle (if changed)
├── PUT /api/puzzles/{name}/grid        -> handle_replace_puzzle_grid
│   └── app.puzzle_uc.replace_puzzle_grid(...)
│       └── PuzzleUseCases.replace_puzzle_grid
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           ├── puzzle.replace_grid
│           │   ├── puzzle.to_json (snapshot)
│           │   ├── Puzzle.initialize_words
│           │   └── clue reconstruction from old across/down text map
│           └── persistence.save_puzzle -> SQLitePersistenceAdapter.save_puzzle
├── GET /api/puzzles/{name}/preview     -> handle_get_puzzle_preview
│   └── app.puzzle_uc.get_puzzle_preview(...)
│       └── PuzzleUseCases.get_puzzle_preview
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           ├── PuzzleToSVG(puzzle)
│           └── ToSVG.generate_xml
└── GET /api/puzzles/{name}/stats       -> handle_get_puzzle_stats
    └── app.puzzle_uc.get_puzzle_stats(...)
        └── PuzzleUseCases.get_puzzle_stats
            ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
            └── Puzzle.get_statistics
                ├── Puzzle.validate
                │   ├── grid.validate_interlock
                │   ├── grid.validate_unchecked_squares
                │   ├── grid.validate_minimum_word_length
                │   └── Puzzle.validate_duplicate_words
                ├── Puzzle.get_word_count -> Grid.get_word_count
                └── Puzzle.get_word_lengths -> Grid.get_word_lengths

Word routes
├── GET /api/words/suggestions?pattern=... -> handle_get_suggestions
│   └── app.word_uc.get_suggestions(pattern)
│       └── WordUseCases.get_suggestions
│           ├── WordUseCases._pattern_to_regex
│           └── word_list.get_matches(regex)
│               └── SQLiteDictionaryAdapter.get_matches (re.compile + fullmatch over in-memory set)
├── GET /api/words/all                  -> handle_get_all_words
│   └── app.word_uc.get_all_words
│       └── WordUseCases.get_all_words
│           └── word_list.get_all_words -> SQLiteDictionaryAdapter.get_all_words
├── GET /api/words/validate?word=...    -> handle_validate_word
│   └── app.word_uc.validate_word(word)
│       └── WordUseCases.validate_word
│           └── word_list.get_all_words -> SQLiteDictionaryAdapter.get_all_words
├── GET /api/puzzles/{name}/words/{seq}/{dir}/constraints -> handle_get_word_constraints
│   ├── app.puzzle_uc.get_word_at(...)  -> PuzzleUseCases.get_word_at -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│   └── app.word_uc.get_word_constraints(word)
│       └── WordUseCases.get_word_constraints
│           ├── Word.get_crossing_words
│           │   └── AcrossWord.get_crossing_word / DownWord.get_crossing_word
│           ├── word_list.get_matches(crossing_pattern)   -> SQLiteDictionaryAdapter.get_matches
│           └── regexp(letter_set)             [crossword/domain/letter_list.py]
└── GET /api/puzzles/{name}/words/{seq}/{dir}/suggestions -> handle_get_ranked_suggestions
    ├── app.puzzle_uc.get_word_at(...)  -> PuzzleUseCases.get_word_at -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
    └── app.word_uc.get_ranked_suggestions(word)
        └── WordUseCases.get_ranked_suggestions
            ├── WordUseCases.get_word_constraints
            ├── WordUseCases._pattern_to_regex
            └── word_list.get_matches(regex)              -> SQLiteDictionaryAdapter.get_matches

Export routes
├── GET /api/export/grids/{name}/pdf    -> handle_export_grid_to_pdf
│   └── app.export_uc.export_grid_to_pdf(...)
│       └── ExportUseCases.export_grid_to_pdf
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           └── export.export_grid_to_pdf(grid)
│               └── BasicExportAdapter.export_grid_to_pdf -> raises ExportError (stub)
├── GET /api/export/grids/{name}/png    -> handle_export_grid_to_png
│   └── app.export_uc.export_grid_to_png(...)
│       └── ExportUseCases.export_grid_to_png
│           ├── persistence.load_grid   -> SQLitePersistenceAdapter.load_grid -> Grid.from_json
│           └── export.export_grid_to_png(grid)
│               └── BasicExportAdapter.export_grid_to_png -> raises ExportError (stub)
├── GET /api/export/puzzles/{name}/acrosslite -> handle_export_puzzle_to_acrosslite
│   └── app.export_uc.export_puzzle_to_acrosslite(...)
│       └── ExportUseCases.export_puzzle_to_acrosslite
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           └── export.export_puzzle_to_acrosslite(puzzle)
│               └── BasicExportAdapter.export_puzzle_to_acrosslite
│                   ├── _build_acrosslite_txt(puzzle)
│                   │   ├── puzzle.is_black_cell / puzzle.get_cell
│                   │   ├── puzzle.across_words[seq].get_clue
│                   │   └── puzzle.down_words[seq].get_clue
│                   ├── puzzle.to_json
│                   └── ZipFile.writestr("puzzle.txt", "puzzle.json")
├── GET /api/export/puzzles/{name}/xml  -> handle_export_puzzle_to_xml
│   └── app.export_uc.export_puzzle_to_xml(...)
│       └── ExportUseCases.export_puzzle_to_xml
│           ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
│           └── export.export_puzzle_to_xml(puzzle)
│               └── BasicExportAdapter._build_xml
│                   ├── puzzle.is_black_cell / puzzle.get_cell
│                   ├── puzzle.get_numbered_cell
│                   └── puzzle.get_clue(seq, Word.ACROSS|Word.DOWN)
└── GET /api/export/puzzles/{name}/nytimes -> handle_export_puzzle_to_nytimes
    └── app.export_uc.export_puzzle_to_nytimes(...)
        └── ExportUseCases.export_puzzle_to_nytimes
            ├── persistence.load_puzzle -> SQLitePersistenceAdapter.load_puzzle -> Puzzle.from_json
            └── export.export_puzzle_to_nytimes(puzzle)
                └── BasicExportAdapter.export_puzzle_to_nytimes
                    ├── PuzzleToSVG(puzzle).generate_xml
                    ├── _build_nytimes_html(puzzle, svg)
                    └── ZipFile.writestr("puzzle.html", "puzzle.svg")
```

Notes
- The tree above follows actual call sites in the backend modules, not tests.
- `BasicExportAdapter.export_grid_to_pdf` and `BasicExportAdapter.export_grid_to_png` are currently stubs that always raise `ExportError`.
- Runtime dispatch to handlers is regex-based (`Router.find_route`) and unified for all HTTP verbs through `RequestHandler._handle_request`.
