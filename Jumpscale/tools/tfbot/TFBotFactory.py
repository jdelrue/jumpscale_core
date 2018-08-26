from jumpscale import j
import re
from io import StringIO
import os
import locale

JSBASE = j.application.jsbase_get_class()

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
            self._tfbots[name]=TFBot(zosclient=zosclient,node=node)
        return self._tfbots[name]


    def test(self):
        """
        js_shell 'j.tools.tfbot.test()'
        """
        bot = self.tfbot_get()
        print(bot.node)
        j.shell()