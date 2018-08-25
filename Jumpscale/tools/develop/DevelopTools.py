from jumpscale import j

from .CodeDirs import CodeDirs
from .MyFileSystemEventHandler import MyFileSystemEventHandler
from watchdog.observers import Observer

import time
import pytoml

JSBASE = j.application.jsbase_get_class()


class DevelopToolsFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.develop"
        JSBASE.__init__(self)
        self.__imports__ = "watchdog"
        self.nodes = j.tools.nodemgr
        self._codedirs = None

    def run(self):
        from .DevelopConfig import ConfigUI
        # self.dockerconfig()
        app = ConfigUI()
        app.run()

    @property
    def iscontainer(self):
        return j.sal.fs.exists("%s/.iscontainer" % j.dirs.HOMEDIR)

    @property
    def codedirs(self):
        if self._codedirs is None:
            self._codedirs = CodeDirs()
        return self._codedirs

    def help(self):

        H = """
        j.tools.develop.run()
        """
        self.logger.debug(H)

    # def resetState(self):
    #     j.actions.setRunId("developtools")
    #     j.actions.reset()
    #     self.init()

    def sync(self):
        """
        sync all code to the remote destinations, uses config as set in jumpscale.toml


        """
        if self.nodes.getall() == []:
            self.logger.debug(
                "NOTHING TO DO, THERE ARE NO NODES DEFINED PLEASE USE  j.tools.develop.run()")
            return
        did = False
        for node in self.nodes.getall():
            if node.selected:
                node.sync()
                did = True
        if did == False:
            self.logger.debug("nodes are defined but not selected, please use j.tools.develop.run()")

    def monitor(self):
        """
        look for changes in directories which are being pushed & if found push to remote nodes
        """

        self.sync()
        nodes = self.nodes.getall()
        paths = j.tools.develop.codedirs.getActiveCodeDirs()
        self.sync_active(paths, nodes)

    def sync_active(self, paths):
        """

        sync changes to destination nodes
        Arguments:
            paths list of paths -- existing folders on system

        """
        event_handler = MyFileSystemEventHandler()
        observer = Observer()
        for source in paths:
            self.logger.debug("monitor:%s" % source)
            observer.schedule(event_handler, source.path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

    def test_executor(self):
        for node in self.nodes.getall():
            if node.selected:
                node.test_executor()

    def clean(self):
        for node in self.nodes.getall():
            if node.selected:
                node.clean()

    def test_js_quick(self):
        j.data.kvs.test()
        j.data.datacache.test()
        j.tools.nodemgr.test()
