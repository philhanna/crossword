# Issue 196 Migration Design

This note turns question 3 from [issue-196-questions.md](/home/saspeh/dev/python/crossword/docs/notes/issue-196-questions.md) into a concrete migration plan.

## Goal

Issue `#196` is now understood as a true data-model merge:

- `Grid` is no longer a first-class saved artifact.
- Saved grids become early-stage puzzles.
- The application should eventually persist only one user-facing content type.

That means existing rows in the `grids` table need a migration path into the merged puzzle model.

## Recommendation

Use a one-time migration tool plus a short compatibility window.

The migration should:

1. Read every saved grid from the `grids` table.
2. Convert it into a puzzle-shaped record in the merged model.
3. Mark the migrated record as being in `grid` mode, or equivalent draft state.
4. Preserve the original name when possible.
5. Leave the original `grids` row in place during the first rollout.
6. Cut the UI over to the merged puzzle flow.
7. Remove legacy grid reads only after the migrated data has been verified.

This is safer than an in-place destructive rewrite because issue `#196` changes both persistence semantics and UI assumptions at the same time.

## Target Model

After the merge, each saved item should be one puzzle record with enough state to support both editing modes.

Minimum additional state likely needed:

- `editor_mode`: `grid` or `puzzle`
- `created_from_legacy_grid`: boolean
- Optional migration metadata for auditing:
  - `migrated_at`
  - `migration_source`
  - `legacy_grid_name`

If you do not want to expand the JSON shape permanently, the migration metadata can be temporary and removed after rollout. But `editor_mode` or an equivalent concept probably belongs in the merged model.

## Migration Rules

For each legacy grid row:

1. Load the `Grid` object from `grids.jsonstr`.
2. Create a merged puzzle object using that grid layout.
3. Initialize all fill cells as blank.
4. Initialize all clues as blank.
5. Set the saved mode/state to `grid`.
6. Reset undo/redo history.
7. Save the result as a puzzle record under the migrated name.

This matches the product decision that grids are just early-stage puzzles.

## Naming Policy

Default policy:

- If a grid name does not conflict with an existing puzzle name, reuse it as the puzzle name.
- If there is a conflict, append a deterministic suffix such as ` (from grid)` or `_grid`.

Recommendation:

- Prefer a human-readable suffix over opaque IDs.
- Log every rename in the migration output.
- Make collision handling deterministic so reruns behave predictably.

Example:

- Grid `Saturday15` -> Puzzle `Saturday15`
- Grid `Themeless` with existing puzzle `Themeless` -> Puzzle `Themeless (from grid)`

## Rollout Plan

### Phase 1: Add merged-puzzle support

Implement the new merged puzzle representation and persistence path first.

At the end of this phase, the code can read and write the new model, but legacy grids may still exist.

### Phase 2: Run migration tool

Create a tool such as `tools/migrate_issue_196.py` that:

- Connects to the existing SQLite database
- Reads every public grid row
- Writes corresponding merged puzzle rows
- Skips working-copy rows such as names starting with `__wc__`
- Emits a report of:
  - migrated rows
  - renamed rows
  - skipped rows
  - failures

### Phase 3: Compatibility window

For one release or one local verification cycle:

- Keep legacy `grids` rows in the database
- Hide the old Grid menu in the UI
- Stop creating new standalone grids
- Prefer opening migrated puzzle records only

This gives you a safe window to verify that migrated content behaves correctly in the new editor.

### Phase 4: Cleanup

Once verified:

- Remove legacy grid-only UI
- Remove grid creation/open flows
- Optionally drop or archive the `grids` table
- Remove temporary migration compatibility code

## Safety Rules

The migration tool should be conservative:

- Never overwrite an existing puzzle row silently
- Never delete source grid rows during the first run
- Be safe to rerun
- Produce a dry-run mode
- Print a summary at the end

Recommended CLI shape:

```text
python tools/migrate_issue_196.py --db samples.db --dry-run
python tools/migrate_issue_196.py --db samples.db --apply
```

## Working Copies

Legacy working copies should not be migrated as user content.

Skip any grid whose name starts with `__wc__`.

Reason:

- They are editor session artifacts, not canonical saved content.
- They may be stale or abandoned.
- Migrating them would clutter the merged puzzle list.

If you want cleanup, that should remain a separate maintenance step.

## Rollback

Rollback should be operationally simple:

- The migration only adds merged puzzle rows.
- It does not delete the original grid rows during initial rollout.
- If the merged editor has a problem, you can revert code and still retain the source data.

That is the strongest reason to avoid destructive migration on the first pass.

## Open Implementation Choices

These still need decisions before writing the tool:

1. Where does `editor_mode` live: top-level DB column, JSON field, or inferred state?
2. Should migrated puzzles get a visible marker in the chooser, at least temporarily?
3. Should renamed collisions be permanent, or should the app prompt the user later?
4. Do you want one-shot migration only, or temporary lazy migration on first open?

## Recommendation Summary

The best first implementation is:

- Add the merged puzzle model.
- Write a one-time, non-destructive migration script.
- Convert each saved grid into a blank puzzle in `grid` mode.
- Skip working copies.
- Preserve names unless there is a conflict.
- Keep legacy grid rows until verification is complete.

That gives you a safe path from the old two-artifact world into the new single-artifact model without forcing risky in-place deletion.
