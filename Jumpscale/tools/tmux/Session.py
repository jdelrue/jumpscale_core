
from Jumpscale import j
import time
import libtmux as tmuxp
import os

JSBASE = j.application.JSBaseClass

# from .Pane import Pane
from .Window import Window

class Session(JSBASE):

    def __init__(self, session):
        # if j.core.db is None:
        #     j.clients.redis.core_start()
        #     j.core.db = j.clients.redis.get()
        JSBASE.__init__(self)
        self.id = session.get("session_id")
        self.name = session.get("session_name")
        self.mgmt = session
        self.reload()

    def reload(self):
        self.windows = []
        for w in self.mgmt.list_windows():
            self.windows.append(Window(self, w))

    def window_remove(self, name):
        windows = self.mgmt.list_windows()
        if len(windows) < 2:
            self.window_get(name="ignore", removeIgnore=False)
        for w in self.mgmt.windows:
            wname = w.get("window_name")
            if name == wname:
                w.kill_window()
        # j.core.db.delete("tmux:pane:%s" % self.name)
        self.reload()

    def window_exists(self, name):
        for window in self.windows:
            if window.name == name:
                return True
        return False

    def window_get(self, name, start_directory=None, attach=False, reset=False, removeIgnore=True):

        # from pudb import set_trace; set_trace()
        if reset:
            self.window_remove(name)

        for window in self.windows:
            if window.name == name:
                # is right construct, means we found a window, now we can safely remove ignore
                if self.window_exists("ignore") and removeIgnore:
                    self.window_remove("ignore")
                return window

        self.logger.debug("create window:%s" % name)
        # j.core.db.delete("tmux:pane:%s" % name)
        res = self.mgmt.new_window(
            name, start_directory=start_directory, attach=attach)

        window = Window(self, res)
        self.windows.append(window)
        window.select()

        # when only 1 pane then ignore had to be created again
        if self.window_exists("ignore") and removeIgnore:
            self.window_remove("ignore")

        return window

    def kill(self):
        raise j.exceptions.RuntimeError("kill")

    def __repr__(self):
        return ("session:%s:%s" % (self.id, self.name))

    __str__ = __repr__

