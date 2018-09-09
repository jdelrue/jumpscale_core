from Jumpscale import j
JSBASE = j.application.jsbase_get_class()

from Jumpscale.tools.executor.ExecutorBase import ExecutorBase

import subprocess
import os
import pytoml
import socket
import sys


class ExecutorLocal(ExecutorBase):

    def __init__(self, debug=False, checkok=False):
        self._cache_expiration = 3600
        ExecutorBase.__init__(self, debug=debug, checkok=debug)
        self.type = "local"
        self._id = 'localhost'

        self.cache = j.data.cache.get(id="executor:%s" %self.id,expiration=3600)

    def exists(self, path):
        return j.sal.fs.exists(path)

    def executeRaw(self, cmd, die=True, showout=False):
        return self.execute(cmd, die=die, showout=showout)

    def execute(
            self,
            cmds,
            die=True,
            checkok=None,
            showout=False,
            timeout=1000,
            env={},
            sudo=False):
        """
        @RETURN rc, out, err
        """
        if env:
            self.env.update(env)
        # if self.debug:
        #     print("EXECUTOR:%s" % cmds)

        if checkok is None:
            checkok = self.checkok

        cmds2 = self.commands_transform(
            cmds, die=die, checkok=checkok, env=env, sudo=sudo)

        rc, out, err = j.sal.process.execute(
            cmds2, die=die, showout=showout, timeout=timeout)

        if checkok:
            out = self._docheckok(cmds, out)

        return rc, out, err

    def executeInteractive(self, cmds, die=True, checkok=None):
        cmds = self.commands_transform(cmds, die, checkok=checkok)
        return j.sal.process.executeWithoutPipe(cmds)

    def upload(self, source, dest, dest_prefix="", recursive=True):
        if dest_prefix != "":
            dest = j.sal.fs.joinPaths(dest_prefix, dest)
        if j.sal.fs.isDir(source):
            j.sal.fs.copyDirTree(
                source,
                dest,
                keepsymlinks=True,
                deletefirst=False,
                overwriteFiles=True,
                ignoredir=[
                    ".egg-info",
                    ".dist-info"],
                ignorefiles=[".egg-info"],
                rsync=True,
                ssh=False,
                recursive=recursive)
        else:
            j.sal.fs.copyFile(source, dest, overwriteFile=True)
        self.cache.reset()

    def download(self, source, dest, source_prefix=""):
        if source_prefix != "":
            source = j.sal.fs.joinPaths(source_prefix, source)

        if j.sal.fs.isFile(source):
            j.sal.fs.copyFile(source, dest)
        else:
            j.sal.fs.copyDirTree(
                source,
                dest,
                keepsymlinks=True,
                deletefirst=False,
                overwriteFiles=True,
                ignoredir=[
                    ".egg-info",
                    ".dist-info"],
                ignorefiles=[".egg-info"],
                rsync=True,
                ssh=False)

    def file_read(self, path):
        return j.sal.fs.readFile(path)

    def file_write(self, path, content, mode=None, owner=None,
                   group=None, append=False, sudo=False,showout=True):
        j.sal.fs.createDir(j.sal.fs.getDirName(path))
        j.sal.fs.writeFile(path, content, append=append)
        if owner is not None or group is not None:
            j.sal.fs.chown(path, owner, group)
        if mode is not None:
            j.sal.fs.chmod(path, mode)
