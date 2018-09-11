
import struct
from Jumpscale import j

JSBASE = j.application.JSBaseClass


class SerializerTime(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)

    def dumps(self, obj):
        obj = struct.pack('<i', j.data.time.getTimeEpoch())
        return obj

    def loads(self, s):
        # epoch = struct.unpack('<i', s[0:2])
        return s[2:]
