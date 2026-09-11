#!/usr/bin/env python3
"""
Check every relative markdown link in README.md and docs/**/*.md.

Reports three kinds of rot:
  - broken     the target file no longer exists (usually a renamed module)
  - anchor     a #L<n> line anchor points past the end of the file
  - absolute   the link is an absolute filesystem path instead of a relative one

Exits 1 if anything was reported, 0 if all links are clean.

Usage:
    python3 .claude/skills/sync-docs/check_links.py
"""

import os
import re
import sys

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

LINK_RE = re.compile(r"\[[^\]^]*?\]\(([^)\s]+)\)")
ANCHOR_RE = re.compile(r"#L(\d+)(?:-L(\d+))?$")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")


def main():
    problems = []
    for md_path in sorted(iter_markdown_files()):
        problems.extend(check_file(md_path))

    if not problems:
        print("All links OK")
        return 0

    for kind, where, target, detail in problems:
        print(f"{kind:8}  {where}  {target}")
        if detail:
            print(f"          {detail}")
    print(f"\n{len(problems)} problem(s)")
    return 1


def iter_markdown_files():
    yield os.path.join(ROOT, "README.md")
    for dirpath, _, filenames in os.walk(os.path.join(ROOT, "docs")):
        for filename in filenames:
            if filename.endswith(".md"):
                yield os.path.join(dirpath, filename)


def check_file(md_path):
    rel_md = os.path.relpath(md_path, ROOT)
    with open(md_path, encoding="utf-8") as f:
        text = f.read()

    problems = []
    for match in LINK_RE.finditer(text):
        target = match.group(1)
        if target.startswith(SKIP_PREFIXES):
            continue
        where = f"{rel_md}:{line_number_of(text, match.start())}"
        problems.extend(check_link(md_path, where, target))
    return problems


def line_number_of(text, offset):
    return text.count("\n", 0, offset) + 1


def check_link(md_path, where, target):
    if os.path.isabs(target):
        return [("absolute", where, target, "use a path relative to the markdown file")]

    path_part, first_line, last_line = split_anchor(target)
    resolved = os.path.normpath(os.path.join(os.path.dirname(md_path), path_part))
    if not os.path.exists(resolved):
        return [("broken", where, target, f"no such file: {os.path.relpath(resolved, ROOT)}")]

    if first_line is None or os.path.isdir(resolved):
        return []

    total = count_lines(resolved)
    wanted = last_line or first_line
    if wanted > total:
        return [("anchor", where, target, f"file has {total} lines")]
    return []


def split_anchor(target):
    path_part, _, fragment = target.partition("#")
    match = ANCHOR_RE.search(target)
    if not match:
        return path_part or fragment, None, None
    first = int(match.group(1))
    last = int(match.group(2)) if match.group(2) else None
    return path_part, first, last


def count_lines(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f)


if __name__ == "__main__":
    sys.exit(main())
