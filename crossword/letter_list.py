class LetterList:
    """ Utility class that forms a regular expression from a list of letters """

    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @staticmethod
    def regexp(letters):

        # Make a list of the integer indices of the letters
        # pointing to the ALPHABET
        iset = set()
        for ch in letters:
            x = LetterList.ALPHABET.find(ch)
            if x > -1:
                iset.add(x)
        ilist = sorted(list(iset))

        # Easy cases - empty, single letter, or all letters
        if len(ilist) == 0:
            return ""
        if len(ilist) == 1:
            x = ilist[0]
            return LetterList.ALPHABET[x]
        if len(ilist) == len(LetterList.ALPHABET):
            a = LetterList.ALPHABET[0]
            z = LetterList.ALPHABET[-1]
            return "."

        # Not the easy cases...
        pattern1 = "[" + LetterList.get_pattern(ilist) + "]"
        pattern2 = "[^" + LetterList.get_pattern(LetterList.complement(ilist)) + "]"
        return pattern1 if len(pattern1) <= len(pattern2) else pattern2

    @staticmethod
    def get_pattern(ilist):
        pattern = ""
        for first, last in LetterList.get_blocks(ilist):
            pattern += LetterList.ALPHABET[first]
            if first < last:
                pattern += "-"
                pattern += LetterList.ALPHABET[last]
        return pattern

    @staticmethod
    def complement(ilist):
        xalphabet = [x for x in range(len(LetterList.ALPHABET))]
        for x in ilist:
            if x in xalphabet:
                xalphabet.remove(x)
        return xalphabet

    @staticmethod
    def get_blocks(ilist):
        first = last = ilist[0]
        for i in range(1, len(ilist)):
            x = ilist[i]
            if x == last + 1:  # Consecutive
                last = x
            else:
                yield first, last
                first = last = x
        yield first, last  # Last one
