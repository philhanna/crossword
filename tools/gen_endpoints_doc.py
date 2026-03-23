#!/usr/bin/env python3
"""
Generate docs/design/endpoints.md from live route registrations.

Imports register_routes() to discover all routes and their handler functions,
then uses inspect to find source file and line number for each handler.
Pretty path names (with named parameters) are sourced from the Swagger SPEC.
git ss
The only manual upkeep needed: if you add a route that's not in the
swagger SPEC and has path parameters, add an entry to _EXTRA_PATHS in
the script so the param names come out correctly instead of {param}.

Usage:
    python3 tools/gen_endpoints_doc.py
"""

import importlib.util
import inspect
import os
import re
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(ROOT, "docs", "design", "endpoints.md")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# Load swagger SPEC for pretty path names (e.g. {name} instead of ([^/]+))
# ---------------------------------------------------------------------------

def _load_swagger_spec():
    spec = importlib.util.spec_from_file_location(
        "swagger", os.path.join(TOOLS_DIR, "swagger.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SPEC


def _build_spec_map(swagger_spec):
    """
    Return a dict mapping (METHOD, normalized_path) -> display_path.

    normalized_path replaces all {param} with {} for matching against regex-derived paths.
    display_path is the original OpenAPI path, with required query params appended.
    """
    path_map = {}
    for pretty_path, path_data in swagger_spec["paths"].items():
        norm = re.sub(r"\{[^}]+\}", "{}", pretty_path)
        shared_params = path_data.get("parameters", [])
        for method_name, method_data in path_data.items():
            if method_name not in ("get", "post", "put", "delete", "patch"):
                continue
            all_params = shared_params + method_data.get("parameters", [])
            query_params = [
                p["name"] for p in all_params
                if p.get("in") == "query" and p.get("required")
            ]
            display = pretty_path
            if query_params:
                display += "?" + "&".join(f"{p}=" for p in query_params)
            path_map[(method_name.upper(), norm)] = display
    return path_map

# ---------------------------------------------------------------------------
# Collect routes from the app
# ---------------------------------------------------------------------------

class _Collector:
    def __init__(self):
        self.routes = []

    def add_route(self, method, pattern, handler):
        self.routes.append((method.upper(), pattern, handler))


def _normalize_pattern(pattern):
    """Strip anchors and replace capture groups with {}."""
    p = pattern.strip("^$")
    return re.sub(r"\([^)]+\)", "{}", p)


def _fallback_display(pattern):
    """Last-resort human-readable path when not found in SPEC."""
    p = pattern.strip("^$")
    return re.sub(r"\([^)]+\)", "{param}", p)


# ---------------------------------------------------------------------------
# Handler → markdown link
# ---------------------------------------------------------------------------

def _handler_link(handler_func):
    src_file = inspect.getfile(handler_func)
    _, start_line = inspect.getsourcelines(handler_func)
    # Path relative to docs/design/ so the link works from that directory
    link_path = os.path.relpath(src_file, os.path.join(ROOT, "docs", "design"))
    return f"[{handler_func.__name__}]({link_path}#L{start_line})"


def _module_name(handler_func):
    return os.path.basename(inspect.getfile(handler_func))


# Routes not in the swagger SPEC — provide pretty display paths manually.
_EXTRA_PATHS = {
    ("POST",   "/api/grids/{}/from-puzzle"):                    "/api/grids/from-puzzle",
    ("GET",    "/api/grids/{}/preview"):                        "/api/grids/{name}/preview",
    ("GET",    "/api/grids/{}/stats"):                          "/api/grids/{name}/stats",
    ("GET",    "/api/puzzles/{}/preview"):                      "/api/puzzles/{name}/preview",
    ("GET",    "/api/puzzles/{}/stats"):                        "/api/puzzles/{name}/stats",
    ("GET",    "/api/puzzles/{}/words/{}/{}/constraints"):      "/api/puzzles/{name}/words/{seq}/{direction}/constraints",
    ("GET",    "/api/export/puzzles/{}/acrosslite"):            "/api/export/puzzles/{name}/acrosslite",
    ("GET",    "/api/export/puzzles/{}/nytimes"):               "/api/export/puzzles/{name}/nytimes",
}

# ---------------------------------------------------------------------------
# Section assignment
# ---------------------------------------------------------------------------

SECTION_ORDER = ["Static", "Grids", "Puzzles", "Words", "Export"]

def _section(norm_path):
    if norm_path.startswith("/api/grids"):
        return "Grids"
    if norm_path.startswith("/api/puzzles") and not norm_path.endswith("/constraints"):
        return "Puzzles"
    if norm_path.startswith("/api/words") or norm_path.endswith("/constraints"):
        return "Words"
    if norm_path.startswith("/api/export"):
        return "Export"
    return "Static"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from crossword.http_server.main import register_routes

    swagger_spec = _load_swagger_spec()
    spec_map = _build_spec_map(swagger_spec)

    collector = _Collector()
    register_routes(collector)

    sections = {s: [] for s in SECTION_ORDER}

    for method, pattern, handler in collector.routes:
        norm = _normalize_pattern(pattern)
        section = _section(norm)
        display = spec_map.get((method, norm)) \
               or _EXTRA_PATHS.get((method, norm)) \
               or _fallback_display(pattern)
        sections[section].append((method, display, handler))

    lines = [
        "# API Endpoints",
        "",
        "All routes are registered in `crossword/http_server/main.py` → `register_routes()`.",
        "Handler modules are in `crossword/http_server/`.",
        "",
        "> Generated by `tools/gen_endpoints_doc.py` — do not edit by hand.",
        "",
    ]

    for section in SECTION_ORDER:
        routes = sections[section]
        if not routes:
            continue
        lines.append(f"## {section}")
        lines.append("")
        lines.append("| Method | Path | Handler | Module |")
        lines.append("|--------|------|---------|--------|")
        for method, display, handler in routes:
            lines.append(
                f"| {method} | `{display}` | {_handler_link(handler)} | `{_module_name(handler)}` |"
            )
        lines.append("")

    output = "\n".join(lines)

    with open(OUT_PATH, "w") as f:
        f.write(output)
    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    main()
