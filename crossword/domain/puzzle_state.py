"""
Puzzle lifecycle states and the pure auto-detection ladder.

See docs/dev/puzzle_state.md for the full lifecycle. The auto-detector only ever
assigns the completion-ladder states (draft/filled/finished); the remaining
states are user-owned and set from the dashboard.
"""

DRAFT = "draft"
FILLED = "filled"
FINISHED = "finished"
SUBMITTED = "submitted"
PUBLISHED = "published"
ARCHIVED = "archived"

ALL_STATES = [DRAFT, FILLED, FINISHED, SUBMITTED, PUBLISHED, ARCHIVED]

# states the auto-detector may assign, lowest -> highest
COMPLETION_LADDER = [DRAFT, FILLED, FINISHED]


def detect_completion_state(puzzle):
    """Pure ladder result: DRAFT | FILLED | FINISHED."""
    if not puzzle.is_filled():
        return DRAFT
    if puzzle.all_clues_complete():
        return FINISHED
    return FILLED
