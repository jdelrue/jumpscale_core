import base64
from .SerializerBase import SerializerBase


class SerializerBase64(SerializerBase):

    def dumps(self, s):
        if self.j.data.types.string.check(s):
            b = s.encode()
        else:
            b = s
        return base64.b64encode(b).decode()

    def loads(self, b):
        if self.j.data.types.string.check(b):
            b = b.encode()
        return base64.b64decode(b).decode()
