
from Jumpscale import j
import time
import libtmux as tmuxp
import os

JSBASE = j.application.JSBaseClass

from .Pane import Pane

class Window(JSBASE):

    def __init__(self, session, window):
        JSBASE.__init__(self)
        self.name = window.get("window_name")
        self.session = session
        self.mgmt = window
        self.panes = []
        self.id = window.get("window_id")
        self._reload()

    @property
    def pane_names(self):
        names = [pane.name for pane in self.panes]
        return names

    def _reload(self):
        if len(self.mgmt.panes) == 1:
            self.panes = [Pane(self, self.mgmt.panes[0])]
        else:
            self.panes = []
            for pane in self.mgmt.panes:
                self.panes.append(Pane(self, pane))

    def pane_exists(self, name="", id=0):
        """
       if there is only 1 and name is not same then name will be set
        """
        for pane in self.panes:
            if pane.name == name:
                return True
            if pane.id == id:
                return True
        return False

    def pane_get(self, name, killothers=False, clear=False):
        """
       if there is only 1 and name is not same then name will be set
        """
        if len(self.panes) == 1:
            self.panes[0].name = name
            if clear:
                self.panes[0].mgmt.send_keys("clear")
            return self.panes[0]
        for pane in self.panes:
            if pane.name == name:
                if killothers:
                    for pane2 in self.panes:
                        if pane2.name != name:
                            pane2.kill()
                if clear:
                    pane.mgmt.send_keys("clear")
                return pane
        raise j.exceptions.RuntimeError(
            "Could not find pane:%s.%s" % (self.name, name))

    def select(self):
        self.mgmt.select_window()

    def kill(self):
        if len(self.session.windows.keys()) < 2:
            self.session.window_get(name="ignore")
        self.logger.debug("KILL %s" % self.name)
        self.mgmt.kill_window()

    def __repr__(self):
        return ("window:%s:%s" % (self.id, self.name))

    __str__ = __repr__

