from json import JSONEncoder


class CrosswordJSONEncoder(JSONEncoder):
    def default(self, obj):
        from crossword.cells import NumberedCell
        if isinstance(obj, NumberedCell):
            jdict = {
                '__type__': NumberedCell.__name__,
                'seq': obj.seq,  # index number
                'r': obj.r,  # row (1..n)
                'c': obj.c,  # column (1..n)
                'a': obj.a,  # across length
                'd': obj.d,  # down length
            }
            return jdict
        else:
            return JSONEncoder.default(self, obj)
