
from Jumpscale import j

from Jumpscale.core.State import State

JSBASE = j.application.jsbase_get_class()

from Jumpscale.core.State import State

class StateFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.data.state"
        JSBASE.__init__(self)
        self._cache = {}

    def get(self, path="/host/jumpscale.toml"):
        """
        """
        st = State(j.tools.executorLocal,path=path)
        return st
