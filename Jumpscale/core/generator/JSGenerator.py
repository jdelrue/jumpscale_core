import os
import fnmatch
from pathlib import Path
from jinja2 import Template

from .Metadata import Metadata

class JSGenerator():

    __jscorelocation__ = "j.core.jsgenerator"

    def __init__(self, j):
        """
        """
        self._j = j
        self._generated = False
        self.errors = []

    def error(self,cat,obj,error):
        print("ERROR: %s:%s"%(cat,obj))
        print (error)
        self.errors.append((cat,obj,error))
        return "%s:%s:%s"%(cat,obj,error)

    def _check_process_file(self,path):
        bname=os.path.basename(path)
        if bname.startswith("_"):
            return False
        IGNORE = ["/template","JSLoader.py","SystemFSDecorators.py"]
        for item in IGNORE:
            if path.find(item) != -1:
                return False
        return True

    def generate(self,reset=False,methods_find=False):
        """
        walk over all found jumpscale libraries
        look for the classes where there is a __jslocation__ inside these are classes which need to be loaded
        :param reset:
        :return:
        """
        self.md = Metadata(self._j)

        #find the directory in which we have all repo's of threefoldtech
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

                js_lib_path = os.path.join(os.fspath(dpath2))

                #NOW WE HAVE FOUND A SET OF JUMPSCALE MODULES
                jumpscale_repo_name = os.path.basename(dpath2)


                for dirName, subdirList, fileList in os.walk(os.fspath(dpath2),followlinks=True):
                    if dirName.find("egg-info") != -1:
                        self._j.shell()
                    if dirName.find("Jumpscale/core") is not -1:
                        continue
                        #skip the core files, they don't need to be read
                    for item in fnmatch.filter(fileList, "*.py"):
                        path = os.path.join(dirName, item)
                        self._log("process",path)
                        if self._check_process_file(path):
                            # self._log("process_ok")
                            jsmodule = self.md.jsmodule_get(path=path,jumpscale_repo_name=jumpscale_repo_name,
                                                                                    js_lib_path=js_lib_path)
                            jsmodule.process(methods_find=methods_find)

        self.md.groups_load() #make sure we find all groups

        self._render()
        self.report()



    def _log(self,cat,msg=""):
        print("- %-15s %s"%(cat,msg))

    def _render(self):

        #create the jumpscale dir if it does not exist yet
        dpath = "%s/jumpscale/"%self._j.dirs.TMPDIR
        if not os.path.exists(dpath):
            os.makedirs(dpath)

        #write the __init__ file otherwise cannot include
        dpath = "%s/jumpscale/__init__.py"%self._j.dirs.TMPDIR
        file = open(dpath, "w")
        file.write("")
        file.close()

        template_path = os.path.join(os.path.dirname(__file__),"templates","template_jumpscale_debug.py")
        template = Path(template_path).read_text()
        t=Template(template)
        C = t.render(md=self.md)
        dpath = "%s/jumpscale/jumpscale_generated.py"%self._j.dirs.TMPDIR
        file = open(dpath, "w")
        file.write(C)
        file.close()

        self._generated = True




    def report(self):
        """
        js_shell "j.core.jsgenerator.report()"
        write reports to /tmp/jumpscale/code_report.md
        :return:
        """
        if self._generated == False:
            self.generate()
        for name,jsgroup in self.md.jsgroups.items():
            path = "%s/jumpscale/code_report_%s.md"%(self._j.dirs.TMPDIR,jsgroup.name)
            file = open(path, "w")
            file.write(jsgroup.markdown)
            file.close()

    def report_errors(self):
        out=""
        for cat,obj,error in self.errors:
            out+="## %s:%s\n\n"%(cat,obj)
            out+="%s\n\n"%error
        path = "%s/jumpscale/ERRORS_report.md" % (self._j.dirs.TMPDIR)
        file = open(path, "w")
        file.write(out)
        file.close()
        return len(self.errors)
