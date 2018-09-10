
from Jumpscale import j
import os
import fnmatch
from pathlib import Path
from Jumpscale.core.JSGenerator import *
from .FixerReplace import FixerReplacer

#ACTIONS
## R = Replace
## RI = Replace case insensitive

JSBASE = j.application.jsbase_get_class()
class Fixer(JSBASE):

    __jslocation__ = "j.tools.fixer"

    def __init__(self):
        JSBASE.__init__(self)
        self.md = Metadata(j)
        self.replacer = FixerReplacer()
        self.logger_enable()


    def do(self):
        """
        js_shell 'j.tools.fixer.do()'
        :return:
        """

        def do(path,args):
            # self=args["self"]
            self.lib_process(path)
            return args

        args = {}
        args["self"]=self
        args=self.jumpscale_libs_process(do,args=args)



    def jumpscale_libs_process(self,method,args={}):

        rootDir = os.path.dirname( j.core.dir_jumpscale_core.rstrip("/"))

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
                        j.shell()
                    if dirName.find("Jumpscale/core") is not -1:
                        continue
                        #skip the core files, they don't need to be read

                    if dirName.lower().find("/template") is not -1:
                        continue
                        #skip template files

                    for item in fnmatch.filter(fileList, "*.py"):
                        self.logger.debug("do:%s" % item)

                        if item.startswith("_"):
                            continue
                        if item in ["JSLoader.py","SystemFSDecorators.py","Fixer.py"]:
                            continue

                        path = os.path.join(dirName,item)

                        self.logger.debug("lib process:%s"%path)
                        args = method(path=path,args=args)

        return args


    def line_process(self,line):
        # self.logger.debug("lineprocess:%s"%line)
        return self.replacer.line_process(line)


    def lib_process(self, path):
        """
        """
        classobj=None
        p = Path(path)
        C=p.read_text()
        classobj = JSModule(j)
        locfound = False
        nr=-1
        for line in C.split("\n"):
            nr+=1

            if line.startswith("class "):
                classname = line.replace("class ", "").split(":")[0].split("(", 1)[0].strip()
                if classname == "JSBaseClassConfig":
                    classname = None
                    break
                classobj.name = classname
                classobj.path = path
            if line.find("__jslocation__") != -1 and locfound == False :
                if classobj.name is None:
                    raise RuntimeError("Could not find class in %s while loading jumpscale lib." %path)
                if line.find("=") is -1: #not location
                    continue
                location = line.split("=",1)[1].replace("\"","").replace("'","").strip()
                if location.find("__jslocation__") == -1:
                    if j.core.jsgenerator._check_jlocation(location) == False:
                        raise RuntimeError("can not use location:%s in %s"%(location,path))
                        classobj.location = location
                    self.logger.debug("%s:%s:%s" % (path, classobj.name, location))
            if line.find("__imports__") != -1:
                if classname is None:
                    raise RuntimeError("Could not find class in %s while loading jumpscale lib." %path)
                importItems = line.split("=",1)[1].replace("\"","").replace("'","").strip()
                importItems = [item.strip() for item in importItems.split(",") if item.strip() != ""]
                classobj.imports = importItems

            if "\t" in line:
                classobj.line_change_add(nr,line.replace("\t","    "))



            changed,line = self.line_process(line)
            if changed:
                classobj.line_change_add(nr,line)







