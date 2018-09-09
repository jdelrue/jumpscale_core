from Jumpscale import j
JSBASE = j.application.jsbase_get_class()

from .ExecutorBase import *
import os


class ExecutorSSH(ExecutorBase):

    def __init__(self, sshclient, debug=False, checkok=False):
        ExecutorBase.__init__(self, debug=debug, checkok=checkok)

        self.sshclient = sshclient
        self.type = "ssh"

        self._id = None

        self._logger = self.logger

    def exists(self, path):
        if path == "/env.sh":
            raise RuntimeError("SS")

        rc, _, _ = self.execute('test -e %s' % path, die=False, showout=False)
        if rc > 0:
            return False
        else:
            return True

    @property
    def id(self):
        if self._id is None:
            self._id = '%s-%s' % (self.sshclient.addr, self.sshclient.port)
        return self._id

    def executeRaw(self, cmd, die=True, showout=False):
        return self.sshclient.execute(cmd, die=die, showout=showout)

    def execute(
            self,
            cmds,
            die=True,
            checkok=False,
            showout=True,
            timeout=None,
            env={},
            asScript=True,
            sudo=False,
            shell=False):
        """
        return (rc,out,err)
        """
        # if cmds.find("cat /root/.bash_profile") != -1:
        #     raise RuntimeError("JJ")
        # if cmds.find("test -e /root/.bash_profile") != -1:
        #     raise RuntimeError("JJ")
        cmds2 = self.commands_transform(
            cmds, die, checkok=checkok, env=env, sudo=sudo)
        if cmds.find("\n") != -1 and asScript:
            if showout:
                self.logger.info(
                    "EXECUTESCRIPT} %s:%s:\n%s" %
                    (self.sshclient.addr, self.sshclient.port, cmds))
            # sshkey = self.sshclient.key_filename or ""
            return self._execute_script(
                content=cmds,
                showout=showout,
                die=die,
                checkok=checkok,
                sudo=sudo)

        if cmds.strip() == "":
            raise RuntimeError("cmds cannot be empty")

        # online command, we use prefab
        if showout:
            self.logger.info("EXECUTE %s:%s: %s" %
                             (self.sshclient.addr, self.sshclient.port, cmds))

        if sudo:
            cmds2 = self.sudo_cmd(cmds2)
        rc, out, err = self.sshclient.execute(
            cmds2, die=die, showout=showout, timeout=timeout)

        if showout:
            self.logger.debug("EXECUTE OK")

        if checkok and die:
            out = self._docheckok(cmds, out)

        return rc, out, err

    def _execute_script(
            self,
            content="",
            die=True,
            showout=True,
            checkok=None,
            sudo=False):
        """
        @param remote can be ip addr or hostname of remote,
                    if given will execute cmds there
        """

        if "sudo -H -SE" in content:
            raise RuntimeError(content)

        if showout:
            self.logger.info(
                "EXECUTESCRIPT {}:{}:\n'''\n{}\n'''\n".format(
                    self.sshclient.addr,
                    self.sshclient.port,
                    content))

        if content[-1] != "\n":
            content += "\n"

        if die:
            content = "set -ex\n{}".format(content)

        if sudo:
            login = self.sshclient.config.data['login']
            path = "/tmp/tmp_prefab_removeme_{}.sh".format(login)
        else:
            path = "/tmp/prefab_{}.sh".format(
                j.data.idgenerator.generateRandomInt(1, 100000))

        j.sal.fs.writeFile(path, content)

        # just in case of the same machine.
        path2 = "/tmp/prefab_{}.sh".format(
            j.data.idgenerator.generateRandomInt(1, 100000))
        self.sshclient.copy_file(path, path2)  # is now always on tmp
        if sudo and "LEDE" not in j.core.platformtype.get(self).osname:
            passwd = self.sshclient.config.data['passwd_']
            cmd = 'echo \'{}\' | sudo -H -SE -p \'\' bash "{}"'.format(
                passwd, path2)
        else:
            cmd = "bash {}".format(path2)
        rc, out, err = self.sshclient.execute(cmd, die=die, showout=showout)

        if checkok and die:
            out = self._docheckok(content, out)

        j.sal.fs.remove(path)
        self.sshclient.sftp.unlink(path2)
        return rc, out, err

    def upload(self, source, dest, dest_prefix="", recursive=True,
               createdir=True,
               rsyncdelete=True,
               ignoredir=['.egg-info', '.dist-info', '__pycache__', ".git"], 
               keepsymlinks=False,showout=False):

        if dest_prefix != "":
            dest = j.sal.fs.joinPaths(dest_prefix, dest)
        if dest[0] != "/":
            raise j.exceptions.RuntimeError("need / in beginning of dest path")
        if source[-1] != "/":
            source += ("/")
        if dest[-1] != "/":
            dest += ("/")
        dest = "root@%s:%s" % (self.sshclient.addr, dest)
        j.sal.fs.copyDirTree(
            source,
            dest,
            keepsymlinks=keepsymlinks,
            deletefirst=False,
            overwriteFiles=True,
            ignoredir=ignoredir,
            ignorefiles=[".egg-info"],
            rsync=True,
            ssh=True,
            sshport=self.sshclient.port,
            recursive=recursive,
            createdir=createdir,
            rsyncdelete=rsyncdelete)
        self.cache.reset()

    def download(self, source, dest, source_prefix="", recursive=True):
        if source_prefix != "":
            source = j.sal.fs.joinPaths(source_prefix, source)
        if source[0] != "/":
            raise j.exceptions.RuntimeError(
                "need / in beginning of source path")
        source = "root@%s:%s" % (self.sshclient.addr, source)
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
            ssh=True,
            sshport=self.sshclient.port,
            recursive=recursive)

    def __repr__(self):
        return ("Executor ssh: %s (%s)" %
                (self.sshclient.addr, self.sshclient.port))

    __str__ = __repr__
