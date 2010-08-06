
class TIter(object):
    def __init__(self, d):
        self.cls = d.__class__
        self._message = d._message
        self._segname = d.segname
        self.i = d.data.__iter__()
    def __iter__(self):
        return self
    def next(self):
        data = self.i.next()
        return self.cls(self._message, data, self._segname)

class FieldTransform(object):
    def __init__(self, obj, data, compname):
        from composites import composite_revs
        self.data = data
        self._message = obj._message
        self._version = obj._message._version
        self.compname = compname
        cr = composite_revs[self._version]
        self._transform = cr.transforms[self.compname]

    def __cmp__(self, data):
        return cmp(self.data, data.data)

    def __str__(self):
        return str(self.data)

    def __iter__(self):
        return TIter(self).__iter__()

    def __getitem__(self, key):
        if isinstance(key, int):
            if key > len(self.data):
                return None
            return self.fieldcheck(self.data[key])
        return self.__class__(self.data[key])

    def __getattr__(self, key):
        if isinstance(key, int):
            if key > len(self.data):
                return None
            return self.fieldcheck(self.data[key])
        tf = self.get_transform(key)
        idx = tf[0]
        typ = tf[1]
        if idx >= len(self.data):
            return None
        val = self.data[idx]
        if typ is None:
            val = self.fieldcheck(val)
        if typ and val is not None:
            val = typ(self, self.data, val)
        return val

    def fieldcheck(self, val):
        if len(val) == 0:
            return None
        if len(val) == 1:
            if val[0] == u'':
                return None
            return val[0]
        return val

    def get_transform(self, key):
        return self._transform[key]

def fieldtransform(obj, data, val, compname):
    if isinstance(val, list):
        if len(val) == 0:
            return None
        if len(val) == 1 and len(val[0]) == 0:
            return None
    return FieldTransform(obj, val, compname)

import composites
composites.fieldtransform = fieldtransform
import compositetrans
compositetrans.fieldtransform = fieldtransform
composites.fieldtransform = fieldtransform

