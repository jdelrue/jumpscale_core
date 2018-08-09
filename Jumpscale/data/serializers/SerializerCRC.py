
# import struct
from jumpscale import j

JSBASE = j.application.jsbase_get_class()


class SerializerCRC(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)

    def dumps(self, obj):
        j.data.hash.crc32_string(obj)
        return obj

    def loads(self, s):
        return s[4:]
