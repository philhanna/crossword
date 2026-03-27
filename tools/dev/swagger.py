"""
Swagger UI for the Crossword API.

Serves a Swagger UI on http://localhost:5001 that documents all endpoints
served by the main app (http://localhost:5000).

Usage:
    python3 tools/swagger.py [--port 5001]
"""

import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# OpenAPI 3.0 specification
# ---------------------------------------------------------------------------

SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Crossword Puzzle Editor API",
        "version": "1.0.0",
        "description": "REST API served by the crossword HTTP server (default port 5000).",
    },
    "servers": [{"url": "http://localhost:5000", "description": "Local dev server"}],
    "tags": [
        {"name": "grids",   "description": "Grid CRUD and editing"},
        {"name": "puzzles", "description": "Puzzle CRUD and editing"},
        {"name": "words",   "description": "Word list / dictionary"},
        {"name": "export",  "description": "Export grids and puzzles"},
    ],

    # ---- reusable schemas -----------------------------------------------
    "components": {
        "schemas": {
            "GridData": {
                "type": "object",
                "properties": {
                    "size":  {"type": "integer", "example": 15},
                    "cells": {
                        "type": "array",
                        "items": {"type": "boolean"},
                        "description": "Flat row-major array (0-indexed). true = black cell.",
                    },
                },
            },
            "GridDataNamed": {
                "allOf": [{"$ref": "#/components/schemas/GridData"}],
                "properties": {
                    "name": {"type": "string", "example": "mygrid"},
                },
            },
            "PuzzleData": {
                "type": "object",
                "properties": {
                    "grid": {"$ref": "#/components/schemas/GridData"},
                    "puzzle": {
                        "type": "object",
                        "properties": {
                            "cells": {
                                "type": "object",
                                "description": "Map of flat-index → {letter?, number?}",
                                "additionalProperties": {
                                    "type": "object",
                                    "properties": {
                                        "letter": {"type": "string"},
                                        "number": {"type": "integer"},
                                    },
                                },
                            },
                            "words": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Word"},
                            },
                        },
                    },
                },
            },
            "Word": {
                "type": "object",
                "properties": {
                    "seq":       {"type": "integer"},
                    "direction": {"type": "string", "enum": ["across", "down"]},
                    "answer":    {"type": "string"},
                    "clue":      {"type": "string"},
                    "cells":     {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "description": "List of [row, col] pairs (1-indexed)",
                    },
                },
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                },
            },
            "WorkingCopySession": {
                "type": "object",
                "properties": {
                    "original_name": {"type": "string", "example": "mygrid"},
                    "working_name":  {"type": "string", "example": "__wc__a1b2c3d4",
                                      "description": "Temporary working copy name. Target all edits here until Save/Close."},
                },
            },
            "PreviewData": {
                "type": "object",
                "properties": {
                    "name":    {"type": "string"},
                    "heading": {"type": "string", "description": "Summary line, e.g. 'mygrid (42 words, 15-letter: 4)'"},
                    "width":   {"type": "number",  "description": "Scaled SVG width in pixels"},
                    "svgstr":  {"type": "string",  "description": "SVG XML string for thumbnail rendering"},
                },
            },
            "StatsData": {
                "type": "object",
                "properties": {
                    "valid":       {"type": "boolean"},
                    "errors":      {
                        "type": "object",
                        "description": "Validation error lists keyed by rule name",
                        "properties": {
                            "interlock":   {"type": "array", "items": {"type": "string"}},
                            "unchecked":   {"type": "array", "items": {"type": "string"}},
                            "wordlength":  {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "size":        {"type": "string", "example": "15 x 15"},
                    "wordcount":   {"type": "integer"},
                    "blockcount":  {"type": "integer"},
                    "wordlengths": {
                        "type": "object",
                        "description": "Map of word-length → {alist: [...], dlist: [...]}",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "alist": {"type": "array", "items": {"type": "integer"}},
                                "dlist": {"type": "array", "items": {"type": "integer"}},
                            },
                        },
                    },
                },
            },
        }
    },

    # ---- paths ----------------------------------------------------------
    "paths": {

        # ================================================================
        # GRIDS
        # ================================================================
        "/api/grids": {
            "get": {
                "tags": ["grids"],
                "summary": "List all grids",
                "responses": {
                    "200": {
                        "description": "List of grid names",
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "properties": {
                                "grids": {"type": "array", "items": {"type": "string"}},
                            },
                        }}},
                    },
                },
            },
            "post": {
                "tags": ["grids"],
                "summary": "Create a new grid",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["name", "size"],
                        "properties": {
                            "name": {"type": "string", "example": "mygrid"},
                            "size": {"type": "integer", "example": 15},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Created grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridData"}}}},
                    "400": {"description": "Validation error",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/{name}": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["grids"],
                "summary": "Load a grid by name",
                "responses": {
                    "200": {"description": "Grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
            "delete": {
                "tags": ["grids"],
                "summary": "Delete a grid",
                "responses": {
                    "200": {"description": "Deleted",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "deleted"},
                                    "name":   {"type": "string"},
                                },
                            }}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/{name}/copy": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["grids"],
                "summary": "Copy a grid to a new name (Save As)",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["new_name"],
                        "properties": {
                            "new_name": {"type": "string", "example": "mygrid-copy"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Copied grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridDataNamed"}}}},
                    "400": {"description": "Validation error",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "404": {"description": "Source not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/{name}/open": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["grids"],
                "summary": "Open a grid for editing (creates working copy)",
                "description": "Creates a temporary working copy of the grid. Direct all edits at `working_name`. On Save, copy `working_name` back to `original_name` then delete it. On Close without saving, just delete `working_name`.",
                "responses": {
                    "200": {"description": "Working copy session info",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WorkingCopySession"}}}},
                    "404": {"description": "Grid not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/{name}/cells/{r}/{c}": {
            "parameters": [
                {"name": "name", "in": "path", "required": True,  "schema": {"type": "string"}},
                {"name": "r",    "in": "path", "required": True,  "schema": {"type": "integer"},
                 "description": "Row (0-indexed, converted to 1-indexed internally)"},
                {"name": "c",    "in": "path", "required": True,  "schema": {"type": "integer"},
                 "description": "Column (0-indexed, converted to 1-indexed internally)"},
            ],
            "put": {
                "tags": ["grids"],
                "summary": "Toggle a black cell (and its 180° symmetric cell)",
                "responses": {
                    "200": {"description": "Updated grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/{name}/rotate": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["grids"],
                "summary": "Rotate grid 90° counterclockwise",
                "responses": {
                    "200": {"description": "Updated grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridData"}}}},
                },
            },
        },

        "/api/grids/{name}/undo": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["grids"],
                "summary": "Undo last black-cell operation",
                "responses": {
                    "200": {"description": "Updated grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridData"}}}},
                },
            },
        },

        "/api/grids/{name}/redo": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["grids"],
                "summary": "Redo last undone black-cell operation",
                "responses": {
                    "200": {"description": "Updated grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridData"}}}},
                },
            },
        },

        "/api/grids/{name}/preview": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["grids"],
                "summary": "Get a scaled-down SVG thumbnail and heading for a grid",
                "responses": {
                    "200": {"description": "Preview data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PreviewData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/{name}/stats": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["grids"],
                "summary": "Get statistics and validation results for a grid",
                "responses": {
                    "200": {"description": "Stats data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StatsData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/grids/from-puzzle": {
            "post": {
                "tags": ["grids"],
                "summary": "Create a grid extracted from an existing puzzle",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["puzzle_name", "grid_name"],
                        "properties": {
                            "puzzle_name": {"type": "string", "example": "mypuzzle"},
                            "grid_name":   {"type": "string", "example": "mygrid"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Created grid data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/GridDataNamed"}}}},
                    "400": {"description": "Validation error",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    "404": {"description": "Puzzle not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        # ================================================================
        # PUZZLES
        # ================================================================
        "/api/puzzles": {
            "get": {
                "tags": ["puzzles"],
                "summary": "List all puzzles",
                "responses": {
                    "200": {"description": "List of puzzle names",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "puzzles": {"type": "array", "items": {"type": "string"}},
                                },
                            }}}},
                },
            },
            "post": {
                "tags": ["puzzles"],
                "summary": "Create a new puzzle from an existing grid",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["name", "grid_name"],
                        "properties": {
                            "name":      {"type": "string", "example": "mypuzzle"},
                            "grid_name": {"type": "string", "example": "mygrid"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Created puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                    "400": {"description": "Validation error",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["puzzles"],
                "summary": "Load a puzzle by name",
                "responses": {
                    "200": {"description": "Puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
            "delete": {
                "tags": ["puzzles"],
                "summary": "Delete a puzzle",
                "responses": {
                    "200": {"description": "Deleted",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "deleted"},
                                    "name":   {"type": "string"},
                                },
                            }}}},
                },
            },
        },

        "/api/puzzles/{name}/copy": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["puzzles"],
                "summary": "Copy a puzzle to a new name (Save As)",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["new_name"],
                        "properties": {
                            "new_name": {"type": "string", "example": "mypuzzle-copy"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Copied puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                    "404": {"description": "Source not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}/open": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["puzzles"],
                "summary": "Open a puzzle for editing (creates working copy)",
                "description": "Creates a temporary working copy of the puzzle. Direct all edits at `working_name`. On Save, copy `working_name` back to `original_name` then delete it. On Close without saving, just delete `working_name`.",
                "responses": {
                    "200": {"description": "Working copy session info",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WorkingCopySession"}}}},
                    "404": {"description": "Puzzle not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}/title": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "put": {
                "tags": ["puzzles"],
                "summary": "Set the puzzle title",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["title"],
                        "properties": {
                            "title": {"type": "string", "example": "My Puzzle Title"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Updated",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "name":  {"type": "string"},
                                    "title": {"type": "string"},
                                },
                            }}}},
                },
            },
        },

        "/api/puzzles/{name}/cells/{r}/{c}": {
            "parameters": [
                {"name": "name", "in": "path", "required": True,  "schema": {"type": "string"}},
                {"name": "r",    "in": "path", "required": True,  "schema": {"type": "integer"},
                 "description": "Row (0-indexed)"},
                {"name": "c",    "in": "path", "required": True,  "schema": {"type": "integer"},
                 "description": "Column (0-indexed)"},
            ],
            "put": {
                "tags": ["puzzles"],
                "summary": "Set a letter in a puzzle cell",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["letter"],
                        "properties": {
                            "letter": {"type": "string", "maxLength": 1, "example": "A"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Cell updated",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "name":   {"type": "string"},
                                    "r":      {"type": "integer", "description": "1-indexed"},
                                    "c":      {"type": "integer", "description": "1-indexed"},
                                    "letter": {"type": "string"},
                                },
                            }}}},
                },
            },
        },

        "/api/puzzles/{name}/words/{seq}/{direction}": {
            "parameters": [
                {"name": "name",      "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "seq",       "in": "path", "required": True, "schema": {"type": "integer"}},
                {"name": "direction", "in": "path", "required": True, "schema": {"type": "string", "enum": ["across", "down"]}},
            ],
            "get": {
                "tags": ["puzzles"],
                "summary": "Get a word's current answer and clue",
                "responses": {
                    "200": {"description": "Word data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Word"}}}},
                },
            },
            "put": {
                "tags": ["puzzles"],
                "summary": "Set a word's text and/or clue",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "example": "HELLO",
                                     "description": "Answer text (undo-tracked). Optional."},
                            "clue": {"type": "string", "example": "A greeting",
                                     "description": "Clue text. Optional."},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Updated",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "name":      {"type": "string"},
                                    "seq":       {"type": "integer"},
                                    "direction": {"type": "string"},
                                    "clue":      {"type": "string"},
                                },
                            }}}},
                },
            },
        },

        "/api/puzzles/{name}/words/{seq}/{direction}/suggestions": {
            "parameters": [
                {"name": "name",      "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "seq",       "in": "path", "required": True, "schema": {"type": "integer"}},
                {"name": "direction", "in": "path", "required": True, "schema": {"type": "string", "enum": ["across", "down"]}},
            ],
            "get": {
                "tags": ["puzzles"],
                "summary": "Get ranked word suggestions for a puzzle word based on crossing constraints",
                "responses": {
                    "200": {"description": "Suggestions",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "suggestions": {"type": "array", "items": {"type": "string"}},
                                    "count":       {"type": "integer"},
                                },
                            }}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}/words/{seq}/{direction}/constraints": {
            "parameters": [
                {"name": "name",      "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "seq",       "in": "path", "required": True, "schema": {"type": "integer"}},
                {"name": "direction", "in": "path", "required": True, "schema": {"type": "string", "enum": ["across", "down"]}},
            ],
            "get": {
                "tags": ["puzzles"],
                "summary": "Get per-position letter constraints derived from crossing words",
                "responses": {
                    "200": {"description": "Constraint data",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "word":     {"type": "string",  "description": "Current word text (spaces as '.')"},
                                    "length":   {"type": "integer"},
                                    "pattern":  {"type": "string",  "description": "Regex pattern for suggestions query"},
                                    "crossers": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "pos":              {"type": "integer", "description": "0-indexed position in this word"},
                                                "letter":          {"type": "string"},
                                                "crossing_text":   {"type": "string"},
                                                "crossing_location": {"type": "string"},
                                                "crossing_index":  {"type": "integer", "description": "1-indexed position in crossing word"},
                                                "regexp":          {"type": "string"},
                                                "choices":         {"type": "array", "items": {"type": "string"}},
                                                "letter_freq":     {"type": "object",
                                                                    "additionalProperties": {"type": "integer"}},
                                            },
                                        },
                                    },
                                },
                            }}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}/words/{seq}/{direction}/reset": {
            "parameters": [
                {"name": "name",      "in": "path", "required": True, "schema": {"type": "string"}},
                {"name": "seq",       "in": "path", "required": True, "schema": {"type": "integer"}},
                {"name": "direction", "in": "path", "required": True, "schema": {"type": "string", "enum": ["across", "down"]}},
            ],
            "post": {
                "tags": ["puzzles"],
                "summary": "Clear letters not shared with any completed crossing word",
                "responses": {
                    "200": {"description": "Updated puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                },
            },
        },

        "/api/puzzles/{name}/undo": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["puzzles"],
                "summary": "Undo last cell-letter change",
                "responses": {
                    "200": {"description": "Updated puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                },
            },
        },

        "/api/puzzles/{name}/redo": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "post": {
                "tags": ["puzzles"],
                "summary": "Redo last undone cell-letter change",
                "responses": {
                    "200": {"description": "Updated puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                },
            },
        },

        "/api/puzzles/{name}/preview": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["puzzles"],
                "summary": "Get a scaled-down SVG thumbnail and heading for a puzzle",
                "responses": {
                    "200": {"description": "Preview data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PreviewData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}/stats": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["puzzles"],
                "summary": "Get statistics and validation results for a puzzle",
                "responses": {
                    "200": {"description": "Stats data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StatsData"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/puzzles/{name}/grid": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "put": {
                "tags": ["puzzles"],
                "summary": "Replace the underlying grid (preserves matching clues)",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {
                        "type": "object",
                        "required": ["new_grid_name"],
                        "properties": {
                            "new_grid_name": {"type": "string"},
                        },
                    }}},
                },
                "responses": {
                    "200": {"description": "Updated puzzle data",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PuzzleData"}}}},
                },
            },
        },

        # ================================================================
        # WORDS
        # ================================================================
        "/api/words/suggestions": {
            "get": {
                "tags": ["words"],
                "summary": "Get word suggestions matching a pattern",
                "parameters": [{
                    "name": "pattern", "in": "query", "required": True,
                    "schema": {"type": "string"},
                    "description": "Pattern using ? as wildcard, e.g. '?HALE'",
                    "example": "?HALE",
                }],
                "responses": {
                    "200": {"description": "Matching words",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "pattern":     {"type": "string"},
                                    "suggestions": {"type": "array", "items": {"type": "string"}},
                                    "count":       {"type": "integer"},
                                },
                            }}}},
                },
            },
        },

        "/api/words/validate": {
            "get": {
                "tags": ["words"],
                "summary": "Check whether a word is in the dictionary",
                "parameters": [{
                    "name": "word", "in": "query", "required": True,
                    "schema": {"type": "string"}, "example": "HELLO",
                }],
                "responses": {
                    "200": {"description": "Validation result",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "word":  {"type": "string"},
                                    "valid": {"type": "boolean"},
                                },
                            }}}},
                },
            },
        },

        "/api/words/all": {
            "get": {
                "tags": ["words"],
                "summary": "Get all words in the dictionary",
                "responses": {
                    "200": {"description": "All words",
                            "content": {"application/json": {"schema": {
                                "type": "object",
                                "properties": {
                                    "count": {"type": "integer"},
                                    "words": {"type": "array", "items": {"type": "string"}},
                                },
                            }}}},
                },
            },
        },

        # ================================================================
        # EXPORT
        # ================================================================
        "/api/export/grids/{name}/pdf": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["export"],
                "summary": "Export grid to PDF",
                "responses": {
                    "200": {"description": "PDF bytes",
                            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
                },
            },
        },

        "/api/export/grids/{name}/png": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["export"],
                "summary": "Export grid to PNG",
                "responses": {
                    "200": {"description": "PNG bytes",
                            "content": {"image/png": {"schema": {"type": "string", "format": "binary"}}}},
                },
            },
        },

        "/api/export/puzzles/{name}/acrosslite": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["export"],
                "summary": "Export puzzle to Across Lite format (ZIP containing .txt and .json)",
                "responses": {
                    "200": {"description": "ZIP archive",
                            "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/export/puzzles/{name}/nytimes": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["export"],
                "summary": "Export puzzle to NYTimes submission format (ZIP containing .html and .svg)",
                "responses": {
                    "200": {"description": "ZIP archive",
                            "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}},
                    "404": {"description": "Not found",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },

        "/api/export/puzzles/{name}/xml": {
            "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "tags": ["export"],
                "summary": "Export puzzle to Crossword Compiler XML",
                "responses": {
                    "200": {"description": "XML text",
                            "content": {"application/xml": {"schema": {"type": "string"}}}},
                },
            },
        },
    },
}

# ---------------------------------------------------------------------------
# Minimal HTTP server
# ---------------------------------------------------------------------------

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Crossword API — Swagger UI</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
<script>
  SwaggerUIBundle({
    url: "/openapi.json",
    dom_id: "#swagger-ui",
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "BaseLayout",
    deepLinking: true,
  });
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress request logging

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = SWAGGER_UI_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/openapi.json":
            body = json.dumps(SPEC, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


# ---------------------------------------------------------------------------
# --check: compare live routes against SPEC
# ---------------------------------------------------------------------------

def _normalize(path: str) -> str:
    """Replace all path parameters with {} for comparison.

    Works on both OpenAPI paths  (/api/grids/{name}/cells/{r}/{c})
    and regex-derived paths      (/api/grids/{}/cells/{}/{}).
    """
    import re
    return re.sub(r"\{[^}]*\}", "{}", path)


def _routes_from_app():
    """Return a set of (METHOD, normalized-path) pairs from the live app."""
    import re
    import os
    # Ensure project root is importable
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

    from crossword.http_server.main import register_routes

    class Collector:
        def __init__(self):
            self.routes = []
        def add_route(self, method, pattern, *_):
            # Convert regex pattern to a plain path
            path = pattern.strip("^$")
            path = re.sub(r"\([^)]+\)", "{}", path)
            self.routes.append((method.upper(), path))

    c = Collector()
    register_routes(c)
    return set(c.routes)


def check():
    """Compare routes registered in the app against paths declared in SPEC."""
    app_routes = _routes_from_app()

    # Build set of (METHOD, normalized-path) from SPEC
    spec_routes = set()
    for path, methods in SPEC["paths"].items():
        norm = _normalize(path)
        for method in methods:
            if method in ("get", "post", "put", "delete", "patch"):
                spec_routes.add((method.upper(), norm))

    # Static file routes are intentionally excluded from the spec
    SKIP = {"/", "/static/{}"}

    # Normalize app routes the same way (already using {})
    app_norm = {(m, _normalize(p)) for m, p in app_routes if _normalize(p) not in SKIP}

    missing_from_spec = app_norm - spec_routes
    extra_in_spec     = spec_routes - app_norm

    ok = True
    if missing_from_spec:
        ok = False
        print("❌  In app but MISSING from swagger spec:")
        for method, path in sorted(missing_from_spec):
            print(f"     {method:7s} {path}")
    if extra_in_spec:
        ok = False
        print("⚠️   In swagger spec but NOT registered in app:")
        for method, path in sorted(extra_in_spec):
            print(f"     {method:7s} {path}")
    if ok:
        print(f"✅  All {len(spec_routes)} spec routes match the app.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if "--check" in sys.argv:
        check()
        return

    port = 5001
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    url = f"http://localhost:{port}"
    print(f"Swagger UI → {url}")
    print("Press Ctrl-C to stop.")

    webbrowser.open(url)
    server = HTTPServer(("localhost", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
