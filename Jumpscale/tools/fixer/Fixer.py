
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

        os.environ["JSRELOAD"] = "1"
        os.environ["JSGENERATE_DEBUG"] = "1"

        def do(jsmodule,classobj,line,args):
            j.shell()
            # self=args["self"]
            self.lib_process(path)
            return args

        args = {}
        # args["self"]=self
        args = j.core.jsgenerator.generate(methods_find=True, action_method = do, action_args=args)
        args=self.jumpscale_libs_process(do,args=args)



    def line_process(self,line):
        # self.logger.debug("lineprocess:%s"%line)
        return self.replacer.line_process(line)


    def lib_process(self, path):
        """
        """


            if "\t" in line:
                classobj.line_change_add(nr,line.replace("\t","    "))



            changed,line = self.line_process(line)
            if changed:
                classobj.line_change_add(nr,line)







