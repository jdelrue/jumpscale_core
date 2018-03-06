'''Definition of several collection types (list, dict, set,...)'''

from .PrimitiveTypes import *

class YAML():
    '''Generic dictionary type'''

    NAME = 'yaml'
    BASETYPE = 'dictionary'

    def check(self, value):
        '''Check whether provided value is a dict'''
        return isinstance(value, dict)

    def get_default(self):
        return dict()

    def fromString(self, s):
        """
        return string from a dict
        """
        if j.data.types.dict.check(s):
            return s
        else:
            # s = s.replace("''", '"')
            j.data.serializer.yaml.loads(s)
            return s

    def toString(self, v):
        return j.data.serializer.yaml.dumps(v)

class JSON():
    
    NAME = 'json'
    BASETYPE = 'dictionary'

class Dictionary():
    '''Generic dictionary type'''

    NAME = 'dictionary'
    BASETYPE = 'dictionary'


    def check(self, value):
        '''Check whether provided value is a dict'''
        return isinstance(value, dict)

    def get_default(self):
        return dict()
        # if self._default is NO_DEFAULT:
        #     return dict()
        # return dict(self._default)

    def fromString(self, s):
        """
        return string from a dict
        """
        if j.data.types.dict.check(s):
            return s
        else:
            s = s.replace("''", '"')
            j.data.serializer.json.loads(s)
            return s

    def toString(self, v):
        return j.data.serializer.json.dumps(v, True, True)

class List():
    '''Generic list type'''
    NAME = 'list'
    BASETYPE = 'list'

    def __init__(self):
        self.SUBTYPE = None

    def check(self, value):
        '''Check whether provided value is a list'''
        return isinstance(value, (list, tuple))
        # self.list_check_1type(value)

    def get_default(self):
        return list()

    def list_check_1type(self, llist, die=True):
        if len(llist) == 0:
            return True
        ttype = j.data.types.type_detect(llist[0])
        for item in llist:
            res = ttype.check(item)
            if res == False:
                if die:
                    raise RuntimeError("List is not of 1 type.")
                else:
                    return False
        return True

    def fromString(self, v, ttype=None):
        if ttype is None:
            ttype = self.SUBTYPE
        if v == None:
            v = ""
        if ttype is not None:
            ttype = ttype.NAME
        v = j.data.text.getList(v, ttype)
        v = self.clean(v)
        if self.check(v):
            return v
        else:
            raise ValueError("List not properly formatted.")

    def clean(self, val, toml=False, sort=False, ttype=None):
        if ttype is None:
            ttype = self.SUBTYPE
        if len(val) == 0:
            return val
        if ttype == None:
            self.SUBTYPE = j.data.types.type_detect(val[0])
            ttype = self.SUBTYPE
        res = []
        for item in val:
            if not toml:
                item = ttype.clean(item)
            else:
                item = ttype.toml_string_get(item)
            if item not in res:
                res.append(item)
        res.sort()
        return res

    def toString(self, val, clean=True, sort=False):
        """
        will translate to what we need in toml
        """
        if clean:
            val = self.clean(val, toml=False, sort=sort)
        if len(str(val)) > 30:
            # multiline
            out = ""
            for item in val:
                out += "%s,\n" % item
            out += "\n"
        else:
            out = ""
            for item in val:
                out += " %s," % item
            out = out.strip().strip(",").strip()
        return out

    def python_code_get(self, value, sort=False):
        """
        produce the python code which represents this value
        """
        value = self.clean(value, toml=False, sort=sort)
        out = "[ "
        for item in value:
            out += "%s, "%self.SUBTYPE.python_code_get(item)
        out = out.strip(",")
        out += " ]"            
        return out
        

    def toml_string_get(self, val, key="", clean=True, sort=True):
        """
        will translate to what we need in toml
        """
        if clean:
            val = self.clean(val, toml=True, sort=sort)
        if key == "":
            raise NotImplemented()
        else:
            out = ""
            if len(str(val)) > 30:
                # multiline
                out += "%s = [\n" % key
                for item in val:
                    out += "    %s,\n" % item
                out += "]\n\n"
            else:
                out += "%s = [" % key
                for item in val:
                    out += " %s," % item
                out = out.rstrip(",")
                out += " ]\n"
        return out

    def toml_value_get(self, val, key=""):
        """
        will from toml string to value
        """
        if key == "":
            raise NotImplemented()
        else:
            return j.data.serializer.toml.loads(val)

class Set():
    '''Generic set type'''

    NAME = 'set'
    BASETYPE = 'set'

    def check(self, value):
        '''Check whether provided value is a set'''
        return isinstance(value, set)

    def get_default(self):
        return list()
