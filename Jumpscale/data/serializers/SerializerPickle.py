
import pickle

from .SerializerBase import SerializerBase
from Jumpscale import j # J due to recursive import issue


class SerializerPickle(SerializerBase):

    def __init__(self):
        SerializerBase.__init__(self)

    def dumps(self, obj):
        return pickle.dumps(obj)

    def loads(self, s):
        return pickle.loads(s)
