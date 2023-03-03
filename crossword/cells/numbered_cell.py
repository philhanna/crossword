import json


class NumberedCell:
    """ A data structure representing a numbered cell
    in a puzzle, which may be the start of either
    1. An across word
    2. A down word
    3. Both
    """

    def __init__(self, seq: int, r: int, c: int, a=0, d=0):
        self.seq = seq
        self.r = r
        self.c = c
        self.a = a
        self.d = d

    def to_json(self) -> str:
        from crossword.util import CrosswordJSONEncoder
        jsonstr: str = json.dumps(self, cls=CrosswordJSONEncoder)
        return jsonstr

    @staticmethod
    def from_json(jsonstr: str) -> "NumberedCell":
        from crossword.util import CrosswordJSONDecoder
        obj: NumberedCell = json.loads(jsonstr, cls=CrosswordJSONDecoder)
        return obj

    def contains_across(self, r, c) -> bool:
        result = r == self.r and c < self.c + self.a
        return result

    def contains_down(self, r, c) -> bool:
        result = c == self.c and r < self.c + self.d
        return result

    def __eq__(self, other) -> bool:
        if type(other) != NumberedCell:
            return False
        return self.seq == other.seq and \
               self.r == other.r and \
               self.c == other.c and \
               self.a == other.a and \
               self.d == other.d

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        output = f"{self.__class__.__name__}({self.seq},{self.r},{self.c},{self.a},{self.d})"
        return output

    def __str__(self) -> str:
        sb = f"NumberedCell(seq={self.seq},r={self.r},c={self.c}"
        if self.a:
            sb += f",a={self.a}"
        if self.d:
            sb += f",d={self.d}"
        sb += ")"
        return sb
