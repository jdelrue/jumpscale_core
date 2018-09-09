import os
import fnmatch
from pathlib import Path
from jinja2 import Template

class JSModule():

    def __init__(self,j):
        self._j = j
        self.path = ""
        self.imports = []
        self.location = ""
        self.name = ""
        self.js_lib_path = ""

        self.lines_changed = {}
        self.method_names = {}

    def line_change_add(self,nr,line):
        self.lines_changed[nr]=line

    def method_add(self,nr,method_name):
        self.method_names[nr] = method_name

    @property
    def importlocation(self):
        """
        :return: e.g. clients.tarantool.TarantoolFactory
        """
        c = self.path.replace(self.js_lib_path,"").lstrip("/")
        #c is e.g. clients/tarantool/TarantoolFactory.py
        c=c[:-3] #remove the py part
        c=c.replace("/",".")
        return c

    @property
    def jname(self):
        """
        e.g. redis
        """
        return self.location.split(".")[-1]

    @property
    def jdir(self):
        """
        e.g. j.clients
        """
        return ".".join(self.location.split(".")[:-1])

    def __repr__(self):
        out = "jsmodule:%s:%s\n"%(self.name,self.path)
        out += "    location: %s\n"%self.location
        imports = ",".join(self.imports)
        out += "    imports: %s\n"%imports
        return out

    __str__ = __repr__

class JSClass():
    """
    e.g. j.tools
    """

    def __init__(self,j,md,jdir):
        self._j = j
        self.md = md
        self.jdir = jdir

    @property
    def name(self):
        if not self.jdir.startswith("j."):
            raise RuntimeError("jdir:%s needs to start with j."%self.jdir)
        d= self.jdir[2:]
        d=d[0].upper()+d[1:].lower()
        return d

    @property
    def jsmodules(self):
        """
        e.g. j.clients
        """
        res=[]
        for item in self.md.jsmodules:
            if item.jdir == self.jdir:
                res.append(item)
        return res

class Metadata():

    def __init__(self,j):
        self._j = j
        self.jsmodules = []
        self._jsclasses = []


    @property
    def syspaths(self):
        """
        paths which need to be available in sys.paths
        :return:
        """
        res=[]
        for item in self.jsmodules:
            if not item.js_lib_path in res:
                res.append(item.js_lib_path)
        return res


    @property
    def jdirs(self):
        """

        :return: ["j.clients",
        """
        res=[]
        for item in self.jsmodules:
            if not item.jdir in res:
                res.append(item.jdir)
        return res

    @property
    def jclasses(self):
        """
        object which represents a class which needs to be added to e.g. j.clients ...
        """
        if self._jsclasses == []:
            for jdirname in self.jdirs:
                self._jsclasses.append(JSClass(self._j,self,jdirname))
        return self._jsclasses


    def __repr__(self):
        return str(self.jsmodules)

    __str__ = __repr__

class JSGenerator():

    __jscorelocation__ = "j.core.jsgenerator"

    def __init__(self, j):
        """
        """
        self._j = j
        self.md = Metadata(j)

        self._locations_error=["j.errorhandler","j.core","j.application",
                               "j.exceptions","j.logger",
                               "j.application", "j.dirs"]

    def _process_file(self,js_lib_path,path):
        res = self._findJumpscaleLocationsInFile(path)
        for name,jsmodule in res.items():
            jsmodule.name = name
            jsmodule.js_lib_path = js_lib_path
            self.md.jsmodules.append(jsmodule)

    def _check_jlocation(self,location):
        """
        will return true if the location is ok
        :param location:
        :return:
        """
        location = location.lower()
        for item in self._locations_error:
            if location.startswith(item):
                return False
        if len(location.split(".")) is not 3:
            return False
        return True



    def _log(self,msg):
        print("**: %s"%msg)

    def _render(self):
        template_path = os.path.join(os.path.dirname(__file__),"templates","template_jumpscale.py")
        template = Path(template_path).read_text()
        t=Template(template)
        C = t.render(md=self.md)
        dpath = "%s/jumpscale_generated.py"%self._j.dirs.TMPDIR
        file = open(dpath, "w")
        file.write(C)
        file.close()

    def _findJumpscaleLocationsInFile(self, path):
        """
        returns:
            {$classname:
                "location":$location
                "import":$importitems
            }
        """
        res={}
        p = Path(path)
        C=p.read_text()
        classname = None
        locfound = False
        for line in C.split("\n"):
            if line.startswith("class "):
                classname = line.replace(
                    "class ", "").split(":")[0].split(
                    "(", 1)[0].strip()
                if classname == "JSBaseClassConfig":
                    break
            if line.find("__jslocation__") != -1 and locfound == False :
                if classname is None:
                    raise RuntimeError("Could not find class in %s while loading jumpscale lib." %path)
                if line.find("=") is -1:
                    continue
                location = line.split("=",1)[1].replace("\"","").replace("'","").strip()
                if location.find("__jslocation__") == -1:
                    if classname not in res:
                        res[classname] = JSModule(self._j)
                        res[classname].path = path
                    if self._check_jlocation(location) == False:
                        raise RuntimeError("can not use location:%s in %s"%(location,path))

                    res[classname].location = location
                    locfound = True
                    self._log("%s:%s:%s" % (path, classname, location))
            if line.find("__imports__") != -1:
                if classname is None:
                    raise RuntimeError(
                        "Could not find class in %s while loading jumpscale lib." %
                        path)
                importItems = line.split("=",1)[1].replace("\"","").replace("'","").strip()
                importItems = [item.strip() for item in importItems.split(",") if item.strip() != ""]
                if classname not in res:
                    res[classname] = JSModule(self._j)
                    res[classname].path = path
                res[classname].imports = importItems

        return res

    def generate(self):
        rootDir = os.path.dirname( self._j.core.dir_jumpscale_core.rstrip("/"))

        p = Path(rootDir)
        for dpath in p.iterdir():
            if not dpath.is_dir():
                continue
            if dpath.name.startswith("."):
                continue

            #level 2 deep, is where we can find the modules
            # p = Path(rootDir)
            for dpath2 in dpath.iterdir():
                jsmodpath = os.path.join(os.fspath(dpath2), ".jumpscalemodules")
                if not os.path.exists(jsmodpath):
                    continue
                for dirName, subdirList, fileList in os.walk(os.fspath(dpath2),followlinks=True):
                    if dirName.find("egg-info") != -1:
                        self._j.shell()
                    if dirName.find("Jumpscale/core") is not -1:
                        continue
                        #skip the core files, they don't need to be read
                    for item in fnmatch.filter(fileList, "*.py"):

                        if item.startswith("_"):
                            continue
                        if item in ["JSLoader.py","SystemFSDecorators.py"]:
                            continue
                        path = os.path.join(dirName,item)
                        self._process_file(js_lib_path=os.fspath(dpath2),path=path)

        self._render()