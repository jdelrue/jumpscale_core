import imp

from Jumpscale import j
from .SchemaProperty import SchemaProperty

JSBASE = j.application.JSBaseClass
import copy
import os

class Schema(JSBASE):
    def __init__(self, text):
        JSBASE.__init__(self)
        self.properties = []
        self.lists = []
        self._template = None
        self._capnp_template = None
        self._obj_class = None
        self._capnp = None
        self._index_list = None
        self._SCHEMA = True
        self.url = ""
        self._schema_from_text(text)
        self.key = j.core.text.strip_to_ascii_dense(self.url).replace(".","_")


    @property
    def md5(self):
        return self._md5


    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))


    def error_raise(self,msg,e=None,schema=None):

        if self.url == "" and "url" in self._systemprops:
            self.url =  self._systemprops["url"]
        out="\nerror in schema:\n"
        out+="    url:%s\n"%self.url
        out+="    msg:%s\n"%j.core.text.prefix("    ",msg)
        if schema:
            out+="    schema:\n%s"%schema
        if e is not None:
            out+="\nERROR:\n"
            out+=j.core.text.prefix("        ",str(e))
        raise RuntimeError(out)

    def _proptype_get(self, txt):
        """
        if default value specified in the schema, will check how to convert it to a type
        :param txt:
        :return:
        """

        if "\\n" in txt:
            jumpscaletype = j.data.types.multiline
            defvalue = jumpscaletype.fromString(txt)

        elif "'" in txt or "\"" in txt:
            jumpscaletype = j.data.types.string
            defvalue = jumpscaletype.fromString(txt)

        elif "." in txt:
            jumpscaletype = j.data.types.float
            defvalue = jumpscaletype.fromString(txt)

        elif "true" in txt.lower() or "false" in txt.lower():
            jumpscaletype = j.data.types.bool
            defvalue = jumpscaletype.fromString(txt)

        elif "[]" in txt:
            jumpscaletype = j.data.types._list()
            jumpscaletype.SUBTYPE = j.data.types.string
            defvalue = []

        elif j.data.types.int.checkString(txt): #means is digit
            jumpscaletype = j.data.types.int
            defvalue = jumpscaletype.fromString(txt)

        else:
            raise RuntimeError("cannot find type for:%s" % txt)

        return (jumpscaletype, defvalue)

    def _schema_from_text(self, text):
        self.logger.debug("load schema:\n%s" % text)

        self.text = j.core.text.strip(text)

        self._md5 = j.data.schema._md5(text)

        systemprops = {}
        self.properties = []
        self._systemprops = systemprops

        def process(line):
            line_original = copy.copy(line)
            propname, line = line.split("=", 1)
            propname = propname.strip()
            line = line.strip()
            

            if "!" in line:
                line, pointer_type = line.split("!", 1)
                pointer_type = pointer_type.strip()
                line=line.strip()
            else:
                pointer_type = None

            if "#" in line:
                line, comment = line.split("#", 1)
                line = line.strip()
                comment = comment.strip()
            else:
                comment = ""

            if "(" in line:
                # if propname.find("farmer")!=-1:
                #     from pudb import set_trace; set_trace()
                line_proptype = line.split("(")[1].split(")")[0].strip().lower()
                line_wo_proptype = line.split("(")[0].strip()
                if line_proptype=="o": #special case where we have subject directly attached
                    jumpscaletype = j.data.types.get("jo")
                    jumpscaletype.SUBTYPE = pointer_type
                    defvalue = ""
                else:
                    jumpscaletype = j.data.types.get(line_proptype)
                    try:
                        if line_wo_proptype=="" or line_wo_proptype==None:
                            defvalue = jumpscaletype.get_default()
                        else:
                            defvalue = jumpscaletype.fromString(line_wo_proptype)
                    except Exception as e:
                        self.error_raise("error on line:%s"%line_original,e=e)                        
            else:
                jumpscaletype, defvalue = self._proptype_get(line)

            if ":" in propname:
                # self.logger.debug("alias:%s"%propname)
                propname, alias = propname.split(":", 1)
            else:
                alias = propname

            if alias[-1]=="*":
                alias=alias[:-1]

            if propname in ["id"]:
                self.error_raise("do not use 'id' in your schema, is reserved for system.",schema=text)

            return (propname, alias, jumpscaletype, defvalue, comment, pointer_type)

        nr = 0
        for line in text.split("\n"):
            line = line.strip()
            self.logger.debug("L:%s" % line)
            nr += 1
            if line.strip() == "":
                continue
            if line.startswith("@"):
                systemprop_name = line.split("=")[0].strip()[1:]
                systemprop_val = line.split("=")[1].strip()
                systemprops[systemprop_name] = systemprop_val.strip("\"").strip("'")
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                self.error_raise("did not find =, need to be there to define field",schema=text)

            propname, alias, jumpscaletype, defvalue, comment, pointer_type = process(line)

            p = SchemaProperty()

            if propname.endswith("*"):
                propname=propname[:-1]
                p.index=True

            p.name = propname
            p.default = defvalue
            p.comment = comment
            p.jumpscaletype = jumpscaletype
            p.alias = alias
            p.pointer_type = pointer_type

            if p.jumpscaletype.NAME is "list":
                self.lists.append(p)
            else:
                self.properties.append(p)

        for key, val in systemprops.items():
            self.__dict__[key] = val

        nr=0
        for s in self.properties:
            s.nr = nr
            self.__dict__["property_%s" % s.name] = s
            nr+=1

        for s in self.lists:
            s.nr = nr
            self.__dict__["property_%s" % s.name] = s
            nr+=1


    @property
    def capnp_id(self):
        if self.md5=="":
            raise RuntimeError("hash cannot be empty")
        return "f"+self.md5[1:16]  #first bit needs to be 1


    @property
    def capnp_schema(self):
        if not self._capnp:
            tpath = "%s/templates/schema.capnp"%self._path
            capnp_schema_text =  j.tools.jinja2.template_render(path=tpath,reload=False,obj=self,objForHash=self.md5)
            self._capnp =  j.data.capnp.getSchemaFromText(capnp_schema_text)
        return self._capnp

    @property
    def objclass(self):
        if self._obj_class is None:

            if self.md5 in [None,""]:
                raise RuntimeError("md5 cannot be None")

            tpath = "%s/templates/template_obj.py"%self._path
            #make sure the defaults render
            for prop in self.properties:
                prop.default_as_python_code
            for prop in self.lists:
                prop.default_as_python_code

            self._obj_class =j.tools.jinja2.code_python_render( obj_key="ModelOBJ",
                        path=tpath,obj=self,
                        objForHash=self.md5)

        return self._obj_class

    def get(self,data=None,capnpbin=None):
        """

        :param data:
        :param capnpbin:
        :param model: if a method given every change will call this method,
                        can be used to implement autosave
        :return:
        """
        if data is None:
            data = {}
        obj =  self.objclass(schema=self,data=data,capnpbin=capnpbin)
        return obj

    def new(self):
        """
        same as self.get() but with no data
        """
        return self.get()

    @property
    def index_list(self):
        if self._index_list==None:
            self._index_list = []
            for prop in self.properties:
                if prop.index:
                    self._index_list.append(prop.alias)
        return self._index_list

    @property
    def index_properties(self):
        _index_list = []
        for prop in self.properties:
            if prop.index:
                _index_list.append(prop)
        return _index_list
            
    def __str__(self):
        out=""
        for item in self.properties:
            out += str(item) + "\n"
        for item in self.lists:
            out += str(item) + "\n"
        return out

    __repr__=__str__
