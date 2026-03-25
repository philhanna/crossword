"""Shared validation for user-facing grid and puzzle names."""

WORKING_COPY_PREFIX = "__wc__"


def validate_public_name(kind: str, name: str) -> None:
    """Reject names reserved for internal working copies."""
    if isinstance(name, str) and name.startswith(WORKING_COPY_PREFIX):
        raise ValueError(
            f"{kind} names starting with '{WORKING_COPY_PREFIX}' are reserved for internal working copies"
        )


def validate_new_public_name(kind: str, name: str, existing_names: list[str]) -> None:
    """Reject reserved names and duplicates for newly created entities."""
    validate_public_name(kind, name)
    if name in existing_names:
        raise ValueError(f"{kind} '{name}' already exists")