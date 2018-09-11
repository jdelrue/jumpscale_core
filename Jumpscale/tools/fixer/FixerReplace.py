
from Jumpscale import j
import re

#ACTIONS
## R = Regex Replace
## RI = Regex Replace case insensitive

DO= """
RI| j.application.JSBase$ | j.application.JSBaseClass
RI| j.data.cache. | j.core.cache.
RI| j.data.text. | j.core.text.
RI| from Jumpscale import j | from Jumpscale import j 
RI| j.application.jsbase_get_class() | j.application.JSBaseClass
RI| .base_class_config | .JSBaseClassConfig
RI| .base_class_configs | .JSBaseClassConfigs
RI| j.logging. | j.logger.
# RI| j.data.text. | j.core.text.
"""

ERRORS = """
configmanager._base_class_config
"""

JSBASE = j.application.JSBaseClass
class FixerReplacer(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.rules=[]

        for rule in DO.split("\n"):
            if rule.strip()=="":
                continue
            if rule.strip().startswith("#"):
                continue
            cmd,from_,to_=rule.split("|")
            if cmd.lower().strip()=="ri":
                self.rules.append(ReplaceIgnoreCase(from_,to_))
            elif cmd.lower().strip()=="r":
                self.rules.append(ReplaceNormal(from_,to_))
            else:
                raise RuntimeError("unknown rule:%s"%rule)


    def line_process(self,line):
        changed = False
        # if "\t" in line:
        #     line = line.replace("\t","    ")
        #     changed = True
        for rule in self.rules:
            line1 = rule.replace(line)
            if line1 != line:
                changed=True
            line = line1
        return changed,line


class ReplaceIgnoreCase():

    def __init__(self,from_,to_,prepend="",append=""):
        self.from_=from_.strip()
        self.to_=to_.strip()
        self.regex = re.compile(re.escape(prepend+self.from_+append), re.IGNORECASE| re.VERBOSE)

    def replace(self,txt):
        m=self.regex.match(txt)

        if m:
            found = m.string[m.start():m.end()]
            txt2=txt.replace(found,self.to_)
            return txt2
        else:
            return txt


class ReplaceNormal(ReplaceIgnoreCase):

    def __init__(self,from_,to_,prepend="",append=""):
        ReplaceIgnoreCase.__init__(self,from_,to_,re.VERBOSE)
        self.regex = re.compile(re.escape(prepend+self.from_+append))



