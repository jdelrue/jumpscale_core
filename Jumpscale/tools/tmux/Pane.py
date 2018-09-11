
from Jumpscale import j
import time
import libtmux as tmuxp
import os

JSBASE = j.application.JSBaseClass

class Pane(JSBASE):

    def __init__(self, window, pane):
        JSBASE.__init__(self)
        self.mgmt = pane
        self.id = pane.get("pane_id")
        self.window = window

    # @property
    # def name(self):
    #     res = j.core.db.hget("tmux:%s:name" % self.window.name, str(self.id))
    #     if res is None:
    #         return ""
    #     else:
    #         res = res.decode()
    #         return res

    # @name.setter
    # def name(self, name):
    #     j.core.db.hset("tmux:%s:name" % self.window.name, str(self.id), name)

    def select(self):
        self.mgmt.select_pane()

    def _split(self, name, ext="-v"):
        self.select()
        j.tools.tmux.execute("split-window %s" % ext)
        # look for pane who is not found yet
        panefound = None
        for pane2 in self.window.mgmt.panes:
            if not self.window.pane_exists(id=pane2.get("pane_id")):
                if panefound is not None:
                    raise j.exceptions.RuntimeError(
                        "can only find 1 pane, bug")
                panefound = pane2
        pane = Pane(self.window, panefound)
        pane.name = name
        self.window.panes.append(pane)
        return pane

    def splitVertical(self, name2, name1="", clear=False):
        res = self._split(name2, "-v")
        if name1 != "":
            self.name = name1
        if clear:
            res.mgmt.send_keys("clear")
        return res

    def splitHorizontal(self, name2, name1="", clear=False):
        res = self._split(name2, "-h")
        if name1 != "":
            self.name = name1
        if clear:
            res.mgmt.send_keys("clear")
        return res

    def execute(self, cmd, wait=False):
        # j.core.db.hset("tmux:%s:exec" % self.window.name,
        #                self.name, "%s" % j.data.time.getTimeEpoch())
        # set exit code and date in front
        # cmd2 = "echo HSET tmux:%s:exec %s %s:$? | redis-cli -s /tmp/redis.sock -x > /dev/null 2>&1" %\
        #     (self.window.name, self.name, j.data.time.getTimeEpoch())
        # cmdall = cmd + ";" + cmd2
        # self.logger.debug (cmd)
        self.mgmt.send_keys(cmd)
        if wait:
            return self.wait()

    # def resetState(self):
    #     """
    #     make sure that previous exit code is removed and all is clean for next run
    #     """
    #     j.core.db.hset("tmux:%s:exec" % self.window.name, self.name, "")

    def check(self):
        # res = j.core.db.hget("tmux:%s:exec" % self.window.name, self.name)
        if res == "":
            return ""
        res = res.decode()
        if ":" in res:
            epoch, rc = res.split(":")
            state = "OK"
        else:
            state = "INIT"
            rc = 0
            epoch = res

        epoch = int(epoch)
        rc = int(rc)
        if rc > 0:
            state = "ERROR"

        # duration=j.data.time.getTimeEpoch()-epoch
        return state, epoch, rc

    def wait(self):
        while True:
            state, epoch, rc = self.check()
            if state != "INIT":
                return state, epoch, rc
            time.sleep(0.1)

    def __repr__(self):
        return ("panel:%s:%s" % (self.id, self.name))

    __str__ = __repr__
