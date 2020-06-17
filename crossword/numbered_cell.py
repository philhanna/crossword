import json


class NumberedCell:
    """ A data structure representing a numbered cell
    in a puzzle, which may be the start of either
    1. An across word
    2. A down word
    3. Both
    """

    @staticmethod
    def from_json(jsonstr):
        obj = json.loads(jsonstr)
        return NumberedCell(
            obj['seq'],
            obj['r'],
            obj['c'],
            obj['across_length'],
            obj['down_length']
        )

    def __init__(self, seq, r, c, a=0, d=0):
        self.seq = seq
        self.r = r
        self.c = c
        self.across_length = a
        self.down_length = d

    def contains_across(self, r, c):
        result = r == self.r and c < self.c + self.across_length
        return result

    def contains_down(self, r, c):
        result = c == self.c and r < self.c + self.down_length
        return result

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
