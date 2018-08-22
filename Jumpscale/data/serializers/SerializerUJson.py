""" okaaaay, JSON can't cope with bytes, sets, or objects, or, well...
    anything significant, basically.  to deal with that, we use pickle
    instead. however... pickle can't be put into strings, because it's
    bytes.  soooo... we use base64 encoding.

    below is cobbled together from a couple of sources:

    https://stackoverflow.com/questions/30469575/how-to-pickle-and-unpickle-to-portable-string-in-python-3
    https://stackoverflow.com/questions/8230315/how-to-json-serialize-sets
"""

import json
import pickle
import codecs
from .SerializerBase import SerializerBase


def as_python_object(dct):
    if '_python_object' in dct:
        pickled = dct['_python_object']
        unpickled = pickle.loads(codecs.decode(pickled.encode(), 'base64'))
        return unpickled
    return dct


class BytesEncoder(json.JSONEncoder):

    ENCODING = 'ascii'

    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode(self.ENCODING)
        if not isinstance(obj, (list, dict, str, int, float, bool, type(None))):
            pickled = pickle.dumps(obj)
            pickled = codecs.encode(pickled, 'base64')
            pickled = pickled.decode()
            return json.dumps({'_python_object': pickled})
        return json.JSONEncoder.default(self, obj)


class Encoder(object):
    @staticmethod
    def get(encoding='ascii'):
        kls = BytesEncoder
        kls.ENCODING = encoding
        return kls


class SerializerUJson(SerializerBase):

    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj, sort_keys=False, indent=False, encoding='ascii'):
        return json.dumps( obj, ensure_ascii=False, sort_keys=sort_keys,
                           indent=indent, cls=Encoder.get( encoding=encoding))

    def loads(self, s):
        if isinstance(s, bytes):
            s = s.decode('utf-8')
        return json.loads(s, object_hook=as_python_object)
