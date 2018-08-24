from .SerializerBase import SerializerBase
import snappy

class SerializerSnappy(SerializerBase):

    def dumps(self, obj):
        return snappy.compress(obj)

    def loads(self, s):
        return snappy.decompress(s)
