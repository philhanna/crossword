from json import JSONDecoder

from crossword.cells import NumberedCell


class CrosswordJSONDecoder(JSONDecoder):
    def __init__(self):
        super().__init__(object_hook=self.dict_to_object)

    def dict_to_object(self, dobj):
        if '__type__' not in dobj:
            return dobj
        objtype = dobj.pop('__type__')
        if objtype == NumberedCell.__class__.__name__:
            return NumberedCell(**dobj)
        else:
            dobj['__type__'] = objtype
            return dobj
