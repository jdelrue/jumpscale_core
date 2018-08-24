class SerializerCRC:

    def dumps(self, obj):
        self.j.data.hash.crc32_string(obj)
        return obj

    def loads(self, s):
        return s[4:]
