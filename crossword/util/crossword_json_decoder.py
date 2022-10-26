from json import JSONDecoder


class CrosswordJSONDecoder(JSONDecoder):
    def __init__(self):
        super().__init__(object_hook=self.dict_to_object)

    def dict_to_object(self, dobj):
        if '__type__' not in dobj:
            return dobj
        objtype = dobj.pop('__type__')
        from crossword.cells import NumberedCell
        if objtype == NumberedCell.__name__:
            return NumberedCell(**dobj)
        else:
            dobj['__type__'] = objtype
            return dobj
