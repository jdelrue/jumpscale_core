
from Jumpscale import j
import time
import libtmux as tmuxp
import os

JSBASE = j.application.JSBaseClass

# from .Pane import Pane
from .Session import Session
# from .Window import Window


class Tmux(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.tmux"
        JSBASE.__init__(self)
        self.__imports__ = "libtmux"
        self.sessions = {}
        # tmuxpath=j.sal.fs.joinPaths(j.dirs.TMPDIR,"tmux")
        # os.environ["TMUX_TMPDIR"]=tmuxpath
        # j.sal.fs.createDir(tmuxpath)

    def _getServer(self, name, firstWindow="ignore"):
        try:
            s = tmuxp.Server()
            s.list_sessions()
        except Exception as e:
            session1 = s.new_session(firstWindow)
        return s

    def killall(self):
        """
        js_shell 'j.tools.tmux.killall()'
        """
        for key,item in self.sessions.items():
            print("kill tmux, implement")
            from IPython import embed;embed(colors='Linux')
            s

    def session_get(self, name, reset=False, attach=False, firstWindow="ignore"):
        if reset and name in self.sessions:
            self.sessions[name].kill()

        if name in self.sessions:
            return self.sessions[name]

        self.logger.debug("create session:%s" % name)

        s = self._getServer(name, firstWindow=firstWindow)

        if reset:
            res = s.new_session(session_name=name,
                                kill_session=kill_session, attach=attach)
        else:
            res = None
            for se in s.list_sessions():
                sname = se.get("session_name")
                if name == sname:
                    res = se
            if res is None:
                res = s.new_session(session_name=name,
                                    kill_session=False, attach=attach)

        self.sessions[name] = Session(res)
        return self.sessions[name]

    def execute(self, cmd, session="main", window="main", pane="main",session_reset=False,window_reset=True):
        """
        """
        s = self.session_get(session,reset=session_reset)
        w = s.window_get(window,reset=window_reset)
        p = w.pane_get(pane)
        p.execute(cmd)

    def panes_4x4_create(self, sessionName="main", windowName="actions", reset=True):
        session = self.session_get(sessionName, firstWindow=windowName)
        window = session.window_get(windowName, reset=reset)

        if len(window.panes) == 16 and reset is False:
            return window

        a = window.pane_get(name=windowName, killothers=True)
        b = a.splitVertical("b")
        a.splitVertical("2", "1")
        b.splitVertical("4", "3")

        for paneName in window.pane_names:
            a = window.pane_get(paneName)
            try:
                count = int(a.name.decode())
            except BaseException:
                count = int(a.name)
            b = a.splitHorizontal("b")  # first split
            a.splitHorizontal("P%s2" % count, "P%s1" % count)
            b.splitHorizontal("P%s4" % count, "P%s3" % count)

        for pane in window.panes:
            pane.execute("clear;echo %s" % pane.name)

        return window
