def find_duplicate(candidate: str, existing_words) -> str | None:
    """Return the first word in existing_words that candidate duplicates
    or is a near-duplicate of, or None if there's no conflict."""
    for w in existing_words:
        if is_near_duplicate(candidate, w):
            return w
    return None


def is_near_duplicate(a: str, b: str) -> bool:
    """True if a and b are the same word, or one is a plain plural of the
    other, ignoring case."""
    a, b = a.upper(), b.upper()
    if a == b:
        return True
    return b in _plural_variants(a) or a in _plural_variants(b)


def _plural_variants(word: str) -> set[str]:
    """All plausible plural spellings of word, using simple English rules."""
    variants = {word + "S", word + "ES"}
    if word.endswith("Y") and len(word) > 1 and word[-2] not in "AEIOU":
        variants.add(word[:-1] + "IES")
    if word.endswith("FE"):
        variants.add(word[:-2] + "VES")
    elif word.endswith("F"):
        variants.add(word[:-1] + "VES")
    return variants
