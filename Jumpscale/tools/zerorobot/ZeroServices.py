
from jumpscale import j
import sys
import inspect

JSBASE = j.application.jsbase_get_class()
class ZeroService(JSBASE):

    def __init__(self,zrepo,template):
        JSBASE.__init__(self)
        self.guid=""




    



class ZeroServices(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.services = {}

