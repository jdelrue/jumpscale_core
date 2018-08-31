"""Definition of several primitive type properties (integer, string,...)
"""

class Types(object):
    __jslocation__ = "j.data.types"

    # order here is critically important, see issue #109
    types = [ \
    ('PrimitiveTypes', 'Boolean', ('bool', 'boolean',), True, ('b',)),
    ('CollectionTypes', 'Dictionary', ('dict',), True, ()),
    ('CollectionTypes', 'List', ('list',), True, ('l',)),
    ('PrimitiveTypes', 'Bytes', ('bytes',), True, ()),
    ('CustomTypes', 'Guid', ('guid',), True, ()),
    ('PrimitiveTypes', 'Float', ('float',), True, ('f',)),
    ('PrimitiveTypes', 'Integer', ('int', 'integer',), True, ('i',)),
    ('PrimitiveTypes', 'StringMultiLine', ('multiline',
                                           'stringmultiline'), True, ()),
    ('PrimitiveTypes', 'String', ('string', 'str'), True, ('s',)),
    ('CustomTypes', 'Date', ('date',), False, ('d')),
    ('CustomTypes', 'Numeric', ('numeric',), False, ('n', 'num',)),
    ('PrimitiveTypes', 'Percent', ('percent',), True, ('p', 'perc',)),
    ('CollectionTypes', 'Hash', ('hash',), True, ('h',)),
    ('PrimitiveTypes', 'Object', ('object',), True, ('o',)),
    ('PrimitiveTypes', 'JSObject', ('jsobject',), True, ('jo',)),
    ('CustomTypes', 'Url', ('url',), True, ('u',)),

    ('CustomTypes', 'Email', ('email',), False, ()),
    ('CustomTypes', 'Path', ('path',), False, ()),
    ('CustomTypes', 'Tel', ('tel',), False, ('mobile',)),
    ('CustomTypes', 'IPRange', ('iprange',), False, ('ipaddressrange',)),
    ('CustomTypes', 'IPAddress', ('ipaddr', 'ipaddress'), False, ()),
    ('CustomTypes', 'IPPort', ('ipport',), False, ()),
    ('CollectionTypes', 'YAML', ('yaml',), False, ()),
    ('CollectionTypes', 'JSON', ('json',), False, ()),
    ('CollectionTypes', 'Set', ('set',), False, ()),
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
                self._ttypes[attr] = "_%s" % attrlist[0]
            for aattr in aliases:
                self._ttypes[aattr] = "_%s" % attrlist[0]

    def type_detect(self, val):
        """ check for most common types.  PLEASE NOTE: this function
            CRITICALLY depends on the order of Types.types, above.
            checks are called in order, and the FIRST ONE THAT SUCCEEDs
            is returned as the type of the object.

            therefore if there are potentially multiple matches
            for a given value, if the order is wrong the WRONG TYPE
            will be returned.
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
