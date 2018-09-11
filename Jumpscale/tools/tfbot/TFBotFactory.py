from Jumpscale import j
from Jumpscale.tools.builder.ZOSContainer import ZOSContainer
import re
from io import StringIO
import os
import locale

JSBASE = j.application.JSBaseClass

from .TFBot import TFBot

class TFBotFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.tfbot"
        JSBASE.__init__(self)
        self._tfbots={}
        self.logger_enable()



    def get(self,name="tfbot",zosclient=None):
        if name not in self._tfbots:
            node = j.tools.nodemgr.set(cat="container", name=name, sshclient=name, selected=False)
            if not zosclient:
                zosclient = self.zos_client_get()
            zos_container = ZOSContainer(zosclient=zosclient, node=node)
            self._tfbots[name] = TFBot(zoscontainer=zos_container)
        return self._tfbots[name]


    def test(self):
        """
        js_shell 'j.tools.tfbot.test()'
        """
        bot = self.get()
        print(bot.node)
        j.shell()
