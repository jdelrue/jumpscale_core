
from Jumpscale import j
import sys
import inspect

JSBASE = j.application.JSBaseClass
class ZeroService(JSBASE):

    def __init__(self,zrepo,template):
        JSBASE.__init__(self)
        self.guid=""




    



class ZeroServices(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.services = {}

