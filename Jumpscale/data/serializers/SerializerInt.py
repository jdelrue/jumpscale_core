from jumpscale import j
JSBASE = j.application.jsbase_get_class()


class SerializerInt(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)

    def dumps(self, obj):
        return str(obj)

    def loads(self, s):
        return int(s)
