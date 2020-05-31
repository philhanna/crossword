class NumberedCell:
    """ A data structure representing a numbered cell
    in a puzzle, which may be the start of either
    1. An across word
    2. A down word
    3. Both
    """

    def __init__(self, seq, r, c, a=0, d=0):
        self.seq = seq
        self.r = r
        self.c = c
        self.across_length = a
        self.down_length = d

    def __eq__(self, other):
        return self.seq == other.seq and \
                self.r == other.r and \
                self.c == other.c and \
                self.across_length == other.across_length and \
                self.down_length == other.down_length

    def __hash__(self):
        return id(self)

    def __str__(self):
        sb = f"NumberedCell(seq={self.seq},r={self.r},c={self.c}"
        if self.across_length:
            sb += f",a={self.across_length}"
        if self.down_length:
            sb += f",d={self.down_length}"
        sb += ")"
        return sb
