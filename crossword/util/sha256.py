import hashlib


def sha256(s):
    """ Computes a sha256 checksum for a string """
    if s is None:
        s = ""
    elif type(s) != str:
        s = str(s)
    m = hashlib.sha256()
    m.update(bytes(s, 'utf-8'))
    value = m.digest()
    return value
