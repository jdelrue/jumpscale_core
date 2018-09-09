
from Jumpscale import j
import os
import fnmatch
from pathlib import Path
from Jumpscale.core.JSGenerator import *

#ACTIONS
## R = Replace
## RI = Replace case insensitive
## RE = Replace at end of line
## RB = Replace at start of line

DO= """
RI| j.data.cache. | j.core.cache.
RI| j.data.text. | j.core.text.
# RI| j.data.text. | j.core.text.
RI| from Jumpscale import j | from Jumpscale import j 
RI| j.application.jsbase_get_class() | j.application.JSBaseClass
RE | j.application.JSBase | j.application.JSBaseClass
RI | .base_class_config | .JSBaseClassConfig
RI | .base_class_configs | .JSBaseClassConfigs
"""

ERRORS = """
configmanager._base_class_config
"""

JSBASE = j.application.JSBaseClass
class Fixer(JSBASE):

    __jslocation__ = "j.tools.fixer"

    def __init__(self):
        JSBASE.__init__(self)
        self.md = Metadata(j)


    def do(self):
        """
        js_shell 'j.tools.fixer.do()'
        :return:
        """

    def jumpscale_libs_process(self,method,args={}):

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

                    if dirName.lower().find("/template") is not -1:
                        continue
                        #skip template files

                    for item in fnmatch.filter(fileList, "*.py"):

                        if item.startswith("_"):
                            continue
                        if item in ["JSLoader.py","SystemFSDecorators.py"]:
                            continue

                        path = os.path.join(dirName,item)

                        self.logger.debug("lib process:%s"%path)
                        args = method(path,args=args)

        return args


    def lib_process(self, path):
        """
        """
        res={}
        p = Path(path)
        C=p.read_text()
        classname = None
        locfound = False
        nr=-1
        for line in C.split("\n"):
            nr+=1
            line_strip = line.strip()
            if line.startswith("class "):
                classname = line.replace("class ", "").split(":")[0].split("(", 1)[0].strip()
                if classname == "JSBaseClassConfig":
                    classname = None
                    break
            if line.find("__jslocation__") != -1 and locfound == False :
                if classname is None:
                    raise RuntimeError("Could not find class in %s while loading jumpscale lib." %path)
                if line.find("=") is -1: #not location
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

            if classname is not None:
                if "\t" in line:
                    res[classname].line_change_add(nr,line.replace("\t","    "))
                if line.startswith("    def "):
                    pre=line.split("(",1)[0]
                    method_name = pre.split("def",1)[1].strip()
                    res[classname].method_add(nr,method_name)

            if len(res.keys())>1:
                raise RuntimeError("should only have 1 module per file for j... in %s"%path)

        return res[classname]





