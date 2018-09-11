from Jumpscale import j
JSBASE = j.application.JSBaseClass

from Jumpscale.tools.executor.ExecutorBase import ExecutorBase

import subprocess
import os
import pytoml
import socket
import sys


class ExecutorLocal(ExecutorBase):

    def __init__(self, debug=False, checkok=False):

        self.__jslocation__ = "j.tools.executorLocal"
        self._cache_expiration = 3600
        ExecutorBase.__init__(self, debug=debug, checkok=debug)
        self.type = "local"
        self._id = 'localhost'

        self.cache = j.core.cache.get(id="executor:%s" %self.id,expiration=3600)

    def exists(self, path):
        return j.sal.fs.exists(path)

    @property
    def stateOnSystem(self):
        """
        is dict of all relevant param's on system
        """

        def getenv():
            res = {}
            for key, val in os.environ.items():
                res[key] = val
            return res

        def do():
            # print ("INFO: stateonsystem for local")

            if self.isBuildEnv:
                homedir = os.environ["PBASE"]
                cfgdir = "%s/cfg" % homedir
            else:
                if "HOMEDIR" in os.environ.keys():
                    homedir = os.environ["HOMEDIR"]
                else:
                    # if os.path.exists("/root/.iscontainer"):
                    #     homedir = "/host"
                    # else:
                    homedir = os.environ["HOME"]
                cfgdir = "%s/jumpscale/cfg" % homedir
            res = {}

            def load(name):
                path = "%s/%s.toml" % (cfgdir, name)
                if os.path.exists(path):
                    return pytoml.loads(j.sal.fs.fileGetContents(path))
                else:
                    return {}

            res["cfg_jumpscale"] = load("jumpscale")
            res["cfg_state"] = load("state")
            res["cfg_me"] = load("me")
            res["env"] = getenv()

            # res["uname"] = subprocess.Popen("uname -mnprs", stdout=subprocess.PIPE,
            #                                 shell=True).stdout.read().decode().strip()
            # res["hostname"] = subprocess.Popen("hostname", stdout=subprocess.PIPE,
            #                                    shell=True).stdout.read().decode().strip()
            res["uname"] = None
            res["hostname"] = socket.gethostname()

            if "darwin" in sys.platform.lower():
                res["os_type"] = "darwin"
            elif "linux" in sys.platform.lower():
                res["os_type"] = "ubuntu"  # dirty hack, will need to do something better, but keep fast
            else:
                print("need to fix for other types (check executorlocal")
                sys.exit(1)

            path = "%s/.profile_js" % (homedir)
            if os.path.exists(path):
                res["bashprofile"] = j.sal.fs.fileGetContents(path)
            else:
                res["bashprofile"] = ""

            res["path_jscfg"] = cfgdir

            if os.path.exists("/root/.iscontainer"):
                res["iscontainer"] = True
            else:
                res["iscontainer"] = False

            return res

        if self._stateOnSystem == None:
            self._stateOnSystem = do()  # don't use cache

        return self._stateOnSystem

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
