from jumpscale import j
import re
from io import StringIO
import os
import locale

JSBASE = j.application.jsbase_get_class()

class TFBot(JSBASE):

    def __init__(self, zoscontainer):
        self.__jslocation__ = "j.tools.tfbot"
        JSBASE.__init__(self)
        self.zoscontainer = zoscontainer
        self.logger_enable()

    @property
    def name(self):
        return self.zoscontainer.name


    @property
    def info(self):
        return self.zoscontainer.container.info


    def __repr__(self):
        return "tfbot:%s" % self.name

    __str__ = __repr__
