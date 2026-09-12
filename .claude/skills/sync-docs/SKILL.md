---
name: sync-docs
description: Bring this project's documentation back in step with the code. Use when the user asks to update, refresh, sync, or check the docs, after a refactor or rename that moved modules around, when a tool or endpoint is added or deleted, or before cutting a release. Covers README.md and docs/**, including the generated endpoint reference and the code links inside the design docs.
---

# Sync the docs to the code

Work through the four steps below in order and report at the end. Do not
commit unless the user asks.

## Scope

In scope: `README.md` and every file under `docs/`.

Out of scope unless the user says otherwise:

- `CHANGELOG.md` and the version in `pyproject.toml` — those belong to the
  bump-version procedure, not to a doc sync.
- The GitHub wiki, a separate checkout at `../crossword.wiki`. README links
  into it for Installation, Configuration and Running the Server. If a change
  invalidates one of those pages, say so in the report rather than editing it.

## The three kinds of doc

Treat each file according to its kind. Getting this wrong is the main way
this task goes bad.

| Kind | Files | Rule |
|---|---|---|
| Generated | `docs/dev/endpoints.md`, `docs/dev/endpoints-wiki.md` | Never hand-edit. Run its generator, which writes both. |
| Living reference | `README.md`, `docs/dev/usecases.md` | Must describe the code as it is today. Edit freely. |
| Design doc | `docs/dev/no_duplicate_words.md`, `puzzle_content_snapshots.md`, `puzzle_save_comments.md`, `puzzle_state_history.md`, `word_editor_regex_search.md` | A point-in-time record of a proposal. **Do not rewrite the prose to match today's code.** Fix only the links. |

A design doc that argues for a design which shipped differently, or never
shipped at all, is still correct as a record of what was proposed. If one has
gone badly out of date, report it and let the user decide whether to add a
short status note at the top. Never silently rewrite its argument.

## Step 1 — Regenerate what is generated

```bash
python3 tools/dev/gen_endpoints_doc.py
git diff --stat docs/dev/endpoints.md docs/dev/endpoints-wiki.md
```

An empty diff means the route table has not moved. A non-empty diff is the
list of route changes to keep in mind for the rest of the pass.

`endpoints-wiki.md` is the same table with absolute GitHub links, written for
the wiki's `API-Reference` page. When it changes, the wiki page is stale until
someone copies the new file over it.

## Step 2 — Fix the links

```bash
python3 .claude/skills/sync-docs/check_links.py
```

It reports three kinds of rot across README and every doc: `broken` (the
target file is gone, almost always a rename), `anchor` (a `#L<n>` anchor runs
past the end of the file), and `absolute` (a `/home/...` path that should be
relative).

How to fix each:

- **Broken, renamed module.** Find where the code went, then re-point the
  link. Past renames: `http_server/puzzle_handlers.py` → `puzzle_routes.py`,
  `http_server/word_handlers.py` → `word_routes.py`. Confirm the new home with
  `ls crossword/http_server/` and a grep for the function named in the link
  text, rather than assuming the mapping still holds.
- **Broken, deleted code.** The thing is gone. In a living-reference doc,
  remove the claim. In a design doc, keep the sentence and drop the link,
  since the sentence is still part of the record.
- **Stale anchor.** Re-point to the current lines if the code still exists.
  If you cannot pin it down, link the file with no `#L` anchor. A file link
  that is merely imprecise beats a line link that is wrong.
- **Absolute path.** Rewrite relative to the markdown file.

The checker cannot tell that an in-range anchor now points at *different*
code. When a doc links into a file that this step already showed to be heavily
edited, open the linked lines and confirm they still say what the doc claims.

## Step 3 — Reconcile the living reference docs

Each check below is a list in a doc against a list from the code. Every item
in the code needs a row, and every row needs an item in the code.

**README architecture table** (`## Architecture`):

```bash
ls crossword/ports crossword/adapters crossword/use_cases frontend/static/js
```

**README tools tables** (`### User`, `### Dev`):

```bash
ls tools/user tools/dev
```

Each script gets one row with a one-line description. Delete rows for scripts
that no longer exist. For a new script, read its docstring for the
description instead of guessing from the filename.

**README running the server** (`## Running the server`):

```bash
ls run_server run_server.bat crossword.service
grep -n "host\|port" crossword/http_server/main.py
```

**usecases.md** — a class table plus one method table per class:

```bash
grep -n "^class \|^    def [a-z]" crossword/use_cases/*.py
grep -rn "UseCases(" crossword/wiring/__init__.py
```

Every public method belongs in its class's table with its real signature and
return type. Private helpers, the leading underscore ones, stay out. The
injected-ports column comes from each constructor. The doc's own convention
is that `user_id` is omitted from every signature, so keep omitting it.

## Step 4 — Sweep for stale names

Grep the docs for things the code no longer has. Build the list from whatever
step 1 and step 3 turned up, plus anything the user mentioned as removed.

```bash
grep -rn "<removed-name>" README.md docs/
```

Check the README table of contents still matches its headings, and that the
prose in `## Using the application` still describes the views the frontend
actually ships.

## Report

Close with a short list of what changed, then, separately, anything you left
for the user to decide: a design doc that has drifted from what shipped, a
wiki page that now looks wrong, a doc claim you could not verify from the
code. Say plainly which files you edited and that nothing is committed.
