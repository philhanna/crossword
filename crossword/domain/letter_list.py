import string

ALPHABET = string.ascii_uppercase


def regexp(letters):
    """ Forms a regular expression from a list of letters """

    # Make a list of the integer indices of the letters
    # pointing to the ALPHABET
    iset = set()
    for ch in letters:
        x = ALPHABET.find(ch)
        if x > -1:
            iset.add(x)
    ilist = sorted(list(iset))

    # Easy cases - empty, single letter, or all letters
    if len(ilist) == 0:
        return ""
    if len(ilist) == 1:
        return ALPHABET[ilist[0]]
    if len(ilist) == len(ALPHABET):
        return "."

    # Not the easy cases...
    pattern1 = "[" + _get_pattern(ilist) + "]"
    pattern2 = "[^" + _get_pattern(_complement(ilist)) + "]"
    return pattern1 if len(pattern1) <= len(pattern2) else pattern2


def _get_pattern(ilist):
    pattern = ""
    for first, last in _get_blocks(ilist):
        pattern += ALPHABET[first]
        if first < last:
            pattern += "-"
            pattern += ALPHABET[last]
    return pattern


def _complement(ilist):
    xalphabet = list(range(len(ALPHABET)))
    for x in ilist:
        if x in xalphabet:
            xalphabet.remove(x)
    return xalphabet


def _get_blocks(ilist):
    first = last = ilist[0]
    for i in range(1, len(ilist)):
        x = ilist[i]
        if x == last + 1:  # Consecutive
            last = x
        else:
            yield first, last
            first = last = x
    yield first, last  # Last one
