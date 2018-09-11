
from Jumpscale import j
import os
import fnmatch
from pathlib import Path
from Jumpscale.core.generator.JSGenerator import *
from .FixerReplace import FixerReplacer

#ACTIONS
## R = Replace
## RI = Replace case insensitive

JSBASE = j.application.jsbase_get_class()
class Fixer(JSBASE):

    __jslocation__ = "j.tools.fixer"

    def __init__(self):
        JSBASE.__init__(self)
        self.generator = JSGenerator(j)
        self.replacer = FixerReplacer()
        self.logger_enable()


    def do(self):
        """
        js_shell 'j.tools.fixer.do()'
        :return:
        """

        os.environ["JSRELOAD"] = "1"
        os.environ["JSGENERATE_DEBUG"] = "1"

        def do(jsmodule,classobj,nr,line,args):
            # self=args["self"]
            changed,line2 = self.line_process(line)
            if changed:
                jsmodule.line_change_add(nr,line2)
            return args

        args = {}
        args = self.generator.generate(methods_find=True, action_method = do, action_args=args)

        self.generator.report()


    def line_process(self,line):
        # self.logger.debug("lineprocess:%s"%line)
        return self.replacer.line_process(line)




