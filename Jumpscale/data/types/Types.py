"""Definition of several primitive type properties (integer, string,...)
"""

class Types(object):
    __jslocation__ = "j.data.types"

    types = [ \
    # CustomTypes
    ('CustomTypes', 'Guid', ('guid',), True, ()),
    ('CustomTypes', 'Email', ('email',), False, ()),
    ('CustomTypes', 'Path', ('path',), False, ()),
    ('CustomTypes', 'Url', ('url',), True, ('u',)),
    ('CustomTypes', 'Tel', ('tel',), False, ('mobile',)),
    ('CustomTypes', 'IPRange', ('iprange',), False, ('ipaddressrange',)),
    ('CustomTypes', 'IPAddress', ('ipaddr', 'ipaddress'), False, ()),
    ('CustomTypes', 'IPPort', ('ipport',), False, ()),
    ('CustomTypes', 'Numeric', ('numeric',), False, ('n', 'num',)),
    ('CustomTypes', 'Date', ('date',), False, ('d')),
    # CollectionTypes
    ('CollectionTypes', 'YAML', ('yaml',), False, ()),
    ('CollectionTypes', 'JSON', ('json',), False, ()),
    ('CollectionTypes', 'Dictionary', ('dict',), True, ()),
    ('CollectionTypes', 'List', ('list',), True, ('l',)),
    ('CollectionTypes', 'Hash', ('hash',), True, ('h',)),
    ('CollectionTypes', 'Set', ('set',), False, ()),
    # PrimitiveTypes
    ('PrimitiveTypes', 'String', ('string', 'str'), True, ('s',)),
    ('PrimitiveTypes', 'StringMultiLine', ('multiline'), True, ()),
    ('PrimitiveTypes', 'Bytes', ('bytes',), True, ()),
    ('PrimitiveTypes', 'Boolean', ('bool', 'boolean',), True, ('b',)),
    ('PrimitiveTypes', 'Integer', ('int', 'integer',), True, ('i',)),
    ('PrimitiveTypes', 'Float', ('float',), True, ('f',)),
    ('PrimitiveTypes', 'Percent', ('percent',), True, ('p', 'perc',)),
    ('PrimitiveTypes', 'Object', ('object',), True, ('o',)),
    ('PrimitiveTypes', 'JSObject', ('jsobject',), True, ('jo',)),
    ]

    def __init__(self):
        self.types_list = []
        self._ttypes = {}
        for (module, kls, attrlist, in_list, aliases) in self.types:
            #print ("register", ename)
            module = "Jumpscale.data.types.%s" % module
            for (idx, attr) in enumerate(attrlist):
                _attr = "_%s" % attr
                ekls = self._add_kls(_attr, module, kls, dynamicname=attr)
                self._add_instance(attr, module, kls, dynamicname=attr)
                # store first instance of type in types_list
                if idx == 0 and in_list:
                    self.types_list.append(attr)
            for aattr in aliases:
                self._ttypes[aattr] = "_%s" % attrlist[0]

    def type_detect(self, val):
        """
        check for most common types
        """
        for ttypename in self.types_list:
            ttype = getattr(self, ttypename)
            if ttype.check(val):
                return ttype
        raise RuntimeError("did not detect val for :%s" % val)

    def get(self, ttype, return_class=False):
        """
        type is one of following: see Types.types for canonical list
        - s, str, string
        - i, int, integer
        - f, float
        - b, bool,boolean
        - tel, mobile
        - d, date
        - n, numeric
        - h, hash (set of 2 int)
        - p, percent
        - o, jsobject
        - ipaddr, ipaddress
        - ipport, tcpport
        - iprange
        - email
        - multiline
        - list
        - dict
        - yaml
        - set
        - guid
        - url, u
        """
        ttype = ttype.lower().strip()

        # special-case for list, have to create a new instance
        # and there are several sub-types (TODO: list them properly in ttype)
        if ttype.startswith("l"):
            tt = self._list()  # need to create new instance
            if return_class:
                raise RuntimeError("cannot return class if subtype specified")
            if len(ttype) == 2:
                tt.SUBTYPE = self.get(ttype[1], return_class=True)()
                return tt
            elif len(ttype) == 1:
                assert tt.SUBTYPE is None
                return tt
            else:
                raise RuntimeError("list type len needs to be 1 or 2")

        # straight check, is it in the self._ttypes dict
        try:
            res = getattr(self, self._ttypes[ttype])
        except KeyError:
            raise self.j.exceptions.RuntimeError(
                "did not find type:'%s'" % ttype)

        # returns either instance or class
        if return_class:
            return res
        else:
            return res()
