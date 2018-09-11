
from Jumpscale import j
import os
import fnmatch
from pathlib import Path
from Jumpscale.core.generator.JSGenerator import *
from .FixerReplace import FixerReplacer

#ACTIONS
## R = Replace
## RI = Replace case insensitive

JSBASE = j.application.JSBaseClass
class Fixer(JSBASE):

    __jslocation__ = "j.tools.fixer"

    def __init__(self):
        JSBASE.__init__(self)
        self.generator = JSGenerator(j)
        self.replacer = FixerReplacer()
        self.logger_enable()


    def find_changes(self):
        """
        js_shell 'j.tools.fixer.find_changes()'
        :return:
        """

        os.environ["JSRELOAD"] = "1"
        os.environ["JSGENERATE_DEBUG"] = "1"

        def do(jsmodule,classobj,nr,line,args):

            changed,line2 = self.line_process(line)
            if changed:
                jsmodule.line_change_add(nr,line,line2)
            return args

        args = {}
        args = self.generator.generate(methods_find=True, action_method = do, action_args=args)

        self.generator.report()

        print(self.generator.md.line_changes)


    def write_changes(self):
        """
        js_shell 'j.tools.fixer.write_changes()'
        BE CAREFULL THIS WILL WRITE THE CHANGES AS FOUND IN self.find_changes
        """
        self.find_changes()

        for jsmodule in self.generator.md.jsmodules.values():
            jsmodule.write_changes()


    def line_process(self,line):
        # self.logger.debug("lineprocess:%s"%line)
        return self.replacer.line_process(line)




