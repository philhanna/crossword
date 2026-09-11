"""
Request body models.

These describe the JSON the frontend sends. Fields the old server checked by
hand, so it could word the rejection itself, are declared optional here and
checked in the route that uses them.
"""

from pydantic import BaseModel


class CreatePuzzleBody(BaseModel):
    """POST /api/puzzles"""
    name: str
    size: int


class CopyPuzzleBody(BaseModel):
    """POST /api/puzzles/{name}/copy"""
    new_name: str | None = None
    comment: str | None = None


class RenamePuzzleBody(BaseModel):
    """POST /api/puzzles/{name}/rename"""
    new_name: str | None = None


class SetPuzzleTitleBody(BaseModel):
    """PUT /api/puzzles/{name}/title"""
    title: str


class SetPuzzleStateBody(BaseModel):
    """PUT /api/puzzles/{name}/state"""
    state: str
    publisher: str | None = None
    date_submitted: str | None = None
    date_published: str | None = None


class SetCellLetterBody(BaseModel):
    """PUT /api/puzzles/{name}/cells/{r}/{c}"""
    letter: str


class SetWordClueBody(BaseModel):
    """PUT /api/puzzles/{name}/words/{seq}/{direction}"""
    clue: str = ""
    text: str | None = None
    locked: bool | None = None


class ImportTextBody(BaseModel):
    """POST /api/import/{acrosslite,xd,ipuz,ccxml}"""
    name: str | None = None
    content: str | None = None


class ImportPuzBody(BaseModel):
    """POST /api/import/puz — the binary format arrives base64 encoded."""
    name: str | None = None
    content_b64: str | None = None
