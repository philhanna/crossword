import json


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
        self.a = a
        self.d = d

    def contains_across(self, r, c):
        result = r == self.r and c < self.c + self.a
        return result

    def contains_down(self, r, c):
        result = c == self.c and r < self.c + self.d
        return result

    def __eq__(self, other):
        if type(other) != NumberedCell:
            return False
        return self.seq == other.seq and \
               self.r == other.r and \
               self.c == other.c and \
               self.a == other.a and \
               self.d == other.d

    def __hash__(self):
        return id(self)

    def __repr__(self):
        output = f"{self.__class__.__name__}({self.seq},{self.r},{self.c},{self.a},{self.d})"
        return output

    def __str__(self):
        sb = f"NumberedCell(seq={self.seq},r={self.r},c={self.c}"
        if self.a:
            sb += f",a={self.a}"
        if self.d:
            sb += f",d={self.d}"
        sb += ")"
        return sb
