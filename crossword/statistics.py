class Statistics:
    """ Metadata about a grid or puzzle

    :param obj is either a grid or puzzle (duck typing; both have the required methods)

    """
    def __init__(self, obj):
        self.obj = obj
        ok, errors = obj.validate()
        self.valid = ok
        self.errors = errors
        self.size = f"{obj.n} x {obj.n}"
        self.wordcount = self.get_wordcount()
        self.wordlengths = self.get_wordlengths()
        pass

    def get_wordcount(self):
        """ Returns the number of words in the grid or puzzle """
        count = 0
        for nc in self.obj.get_numbered_cells():
            if nc.a:
                count += 1
            if nc.d:
                count += 1
        return count

    def get_wordlengths(self):
        """ Returns a list of word lengths and words of that length """
        table = {}
        for nc in self.obj.get_numbered_cells():
            length = nc.a
            if length:
                if length not in table:
                    table[length] = {
                        'alist': [],
                        'dlist': [],
                    }
                table[length]['alist'].append(nc.seq)
            length = nc.d
            if length:
                if length not in table:
                    table[length] = {
                        'alist': [],
                        'dlist': [],
                    }
                table[length]['dlist'].append(nc.seq)
        return table


