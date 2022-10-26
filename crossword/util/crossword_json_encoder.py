from json import JSONEncoder

from crossword.cells import NumberedCell


class CrosswordJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, NumberedCell):
            return {
                '__type__': NumberedCell.__class__.__name__,
                'seq': obj.seq,     # index number
                'r': obj.r,         # row (1..n)
                'c': obj.c,         # column (1..n)
                'a': obj.a,         # across length
                'd': obj.d,         # down length
            }
        else:
            return JSONEncoder.default(self, obj)