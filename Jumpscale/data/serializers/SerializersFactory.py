import os

class SerializersFactory:

    __jslocation__ = "j.data.serializers"

    serialisers = [
        ['int', 'SerializerInt', None],
        ['time', 'SerializerTime', None],
        ['base64', 'SerializerBase64', '6'],
        ['dict', 'SerializerDict', 'd'],
        ['blowfish', 'SerializerBlowfish', 'b'],
        ['json', 'SerializerUJson', 'j'],
        ['yaml' , 'SerializerYAML', 'y'],
        ['blosc', 'SerializerBlosc', 'c'],
        ['crc', 'SerializerCRC', None],
        ['lzma', 'SerializerLZMA', 'l'],
        ['msgpack', 'SerializerMSGPack', 'm'],
        ['pickle', 'SerializerPickle', 'p'],
        ['snappy', 'SerializerSnappy', 's'],
        ['toml', 'SerializerTOML', 't'],
    ]

    def __init__(self):
        self.types = {}
        self.packtypes = {}
        self._cache = {}

        fullpath = os.path.dirname(self.__jsfullpath__)
        print ("fullpath", fullpath)
        for s in self.serialisers:
            [attr, kls, packtype] = s
            module = 'Jumpscale.data.serializers.%s' % kls # same name
            mfullpath = os.path.join(fullpath, "%s.py" % kls)
            mod = self._add_instance(attr, module, kls, mfullpath, self.j)
            if packtype:
                self.packtypes[packtype] = attr # replaced in getSerializerType
                self.types[attr] = attr # replaced in getSerializerType

        for s in self.serialisers:
            print ("serializers", s)

    def get(self, serializationstr, key=""):
        """
        serializationstr FORMATS SUPPORTED FOR NOW
            m=MESSAGEPACK
            c=COMPRESSION WITH BLOSC
            b=blowfish
            s=snappy
            j=json
            6=base64
            l=lzma
            p=pickle
            r=bin (means is not object (r=raw)) # NOT LISTEED
            l=log # XXX CANNOT BE - CLASHES WITH LZMA
            d=dict (check if there is a dict to object,
                   if yes use that dict, removes the private
                   properties (starting with _))

             example serializationstr "mcb" would mean first use
             messagepack serialization then compress using blosc then
             encrypt (key will be used)

            this method returns
        """
        raise Exception('Issue #98 This function has not been completed? ' \
                        'The Serializer class is commented out?')
        k = "%s_%s" % (serializationstr, key)
        if k not in self._cache:
            if len(list(self._cache.keys())) > 100:
                self._cache = {}
            self._cache[k] = Serializer(serializationstr, key)
        return self._cache[k]

    def getSerializerType(self, typ, key=""):
        """
        serializationstr FORMATS SUPPORTED FOR NOW
            m=MESSAGEPACK
            c=COMPRESSION WITH BLOSC
            b=blowfish
            s=snappy
            j=json
            6=base64
            l=lzma
            p=pickle
            r=bin (means is not object (r=raw)) # XXX NOT LISTED
            l=log # XXX CANNOT BE - CLASHES WITH LZMA
        """
        attrname = self.packtypes.get(typ, None)
        if attrname is None:
            raise KeyError('getSerializerType %s not found' % typ)
        attr = self.types.get(attrname, None)
        if attr is None:
            raise KeyError('getSerializerType %s not found' % attrname)
        if isinstance(attr, str):
            attr = self.types[attr] = getattr(self, attr)
        return attr

    def fixType(self, val, default):
        """
        will convert val to type of default

        , separated string goes to [] if default = []
        """
        if val is None or val == "" or val == []:
            return default

        if j.data.types.list.check(default):
            res = []
            if j.data.types.list.check(val):
                for val0 in val:
                    if val0 not in res:
                        res.append(val0)
            else:
                val = str(val).replace("'", "")
                if "," in val:
                    val = [item.strip() for item in val.split(",")]
                    for val0 in val:
                        if val0 not in res:
                            res.append(val0)
                else:
                    if val not in res:
                        res.append(val)
        elif j.data.types.bool.check(default):
            if str(val).lower() in ['true', "1", "y", "yes"]:
                res = True
            else:
                res = False
        elif j.data.types.int.check(default):
            res = int(val)
        elif j.data.types.float.check(default):
            res = int(val)
        else:
            res = str(val)
        return res


# class Serializer(JSBASE):

#     def __init__(self, serializationstr, key=""):
#         JSBASE.__init__(self)
#         self.serializationstr = serializationstr
#         self.key = key
#         for k in self.serializationstr:
#             j.data.serializer.getSerializerType(k, self.key)

#     def dumps(self, val):
#         if self.serializationstr == "":
#             return val
#         for key in self.serializationstr:
#             # print "dumps:%s"%key
#             val = j.data.serializer.types[key].dumps(val)
#         return val

#     def loads(self, data):
#         if self.serializationstr == "":
#             return data

#         for key in reversed(self.serializationstr):
#             # print "loads:%s"%key
#             data = j.data.serializer.types[key].loads(data)
#         return data
