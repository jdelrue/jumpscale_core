
from Jumpscale import j
import os

from .ZeroTemplates import *
from .ZeroRepos import *
# from .ZeroServices import *

JSBASE = j.application.jsbase_get_class()
class ZeroRobot(JSBASE):

    def __init__(self):
        if not hasattr(self, '__jslocation__'):
            self.__jslocation__ = "j.tools.zerorobot"
        JSBASE.__init__(self)
        self._models = None
        self._tarantool = None
        self._templates = None
        self._repos = None
        # self.ZeroServiceClass =
        self.ZeroTemplateClass = ZeroTemplate

    @property
    def templates(self):
        if self._templates is None:
            self._templates = ZeroTemplates()
        return self._templates

    @property
    def repos(self):
        if self._repos is None:
            self._repos = ZeroRepos()
            self._repos.load()  # auto load the known ones
        return self._repos


    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))

    # @property
    # def tarantool(self):
    #     if self._tarantool==None:
    #         self._tarantool = j.clients.tarantool.client_get()
    #     return self._tarantool

    # @property
    # def models(self):
    #     if self._models==None:
    #         self.tarantool.addModels(self._path+"models")
    #         self._models= self.tarantool.models
    #     return self._models

    def test(self):
        self.templates.load() #will load all templates it can find

        # XXX tests need to be non-interactive.  use a different function name
        # e.g. _interactive_test
        #from IPython import embed;embed(colors='Linux')


