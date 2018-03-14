import os
import threading

from js9 import j

from .AsyncSSHClient import AsyncSSHClient
from .SSHClient import SSHClient


class SSHClientFactory:

    _lock = threading.Lock()
    cache = {}

    logger = j.logger.get("j.clients.ssh")

    def __init__(self):
        self.__jslocation__ = "j.clients.ssh"
        self.__imports__ = "paramiko,asyncssh"

    def reset(self):
        """
        Close and clear cached ssh clients
        """
        with self._lock:
            for _, client in self.cache.items():
                client.close()
            self.cache = {}

    def get(self, addr="localhost", port=22, login="root", passwd=None, stdout=True,
            forward_agent=True, allow_agent=True, look_for_keys=True, timeout=5,
            key_filename=None, passphrase=None, usecache=True):
        """
        gets an ssh client

        If password is passed, sshclient will try to authenticated with login/passwd.
        If key_filename is passed, it will override look_for_keys
        and allow_agent and try to connect with this key.

        :param addr: the server to connect to
        :param port: port to connect to
        :param login: the username to authenticate as
        :param passwd: leave empty if logging in with sshkey
        :param stdout: show output
        :param foward_agent: fowrward all keys to new connection
        :param allow_agent: set to False to disable connecting to the SSH agent
        :param look_for_keys: set to False to disable searching
                              for discoverable private key files in ~/.ssh/
        :param timeout: an optional timeout (in seconds) for the TCP connect
        :param key_filename: the filename to try for authentication
        :param passphrase: a password to use for unlocking a private key
        :param usecache: use cached client. False to get a new connection
        """
        with self._lock:
            key = "%s_%s_%s_%s_sync" % (addr, port, login, j.data.hash.md5_string(str(passwd)))

            if key in self.cache and usecache:
                try:
                    _ssh_transport = self.cache[key].transport
                    usecache = not (not _ssh_transport or not _ssh_transport.is_active())
                except j.exceptions.RuntimeError:
                    usecache = False

            if key not in self.cache or usecache is False:
                self.cache[key] = SSHClient(
                    addr,
                    port,
                    login,
                    passwd,
                    stdout=stdout,
                    forward_agent=forward_agent,
                    allow_agent=allow_agent,
                    look_for_keys=look_for_keys,
                    key_filename=key_filename,
                    passphrase=passphrase,
                    timeout=timeout)

            return self.cache[key]

    def get_async(self, addr="localhost", port=22, login="root", passwd=None,
                  forward_agent=True, allow_agent=True, look_for_keys=True, timeout=5,
                  key_filename=(), passphrase=None, usecache=True):
        """
        gets an async ssh client

        If password is passed, sshclient will try to authenticated with login/passwd.
        If key_filename is passed, it will override look_for_keys
        and allow_agent and try to connect with this key.

        :param addr: the server to connect to
        :param port: port to connect to
        :param login: the username to authenticate as
        :param passwd: leave empty if logging in with sshkey
        :param forward_agent: fowrward all keys to new connection
        :param allow_agent: set to False to disable connecting to the SSH agent
        :param look_for_keys: set to False to disable searching
                              for discoverable private key files in ~/.ssh/
        :param timeout: an optional timeout (in seconds) for the TCP connect
        :param key_filename: the filename to try for authentication
        :param passphrase: a password to use for unlocking a private key
        :param usecache: use cached client. False to get a new connection
        """

        key = "%s_%s_%s_%s_async" % (addr, port, login, j.data.hash.md5_string(str(passwd)))

        if key not in self.cache or usecache is False:
            self.cache[key] = AsyncSSHClient(
                addr=addr,
                port=port,
                login=login,
                passwd=passwd,
                forward_agent=forward_agent,
                allow_agent=allow_agent,
                look_for_keys=look_for_keys,
                key_filename=key_filename,
                passphrase=passphrase,
                timeout=timeout)

        return self.cache[key]

    def removeFromCache(self, client):
        with self._lock:
            key = "%s_%s_%s_%s" % (
                client.addr, client.port, client.login, j.data.hash.md5_string(str(client.passwd)))
            if key in self.cache:
                self.cache.pop(key)

    def close(self):
        with self._lock:
            for _, client in self.cache.items():
                client.close()

    def _add_ssh_agent_to_bash_profile(self):

        bashprofile_path = os.path.expanduser("~/.bash_profile")
        if not j.sal.fs.exists(bashprofile_path):
            j.sal.process.execute('touch %s' % bashprofile_path)

        content = j.sal.fs.readFile(bashprofile_path)
        out = ""
        for line in content.split("\n"):
            if line.find("#JSSSHAGENT") != -1:
                continue
            if line.find("SSH_AUTH_SOCK") != -1:
                continue

            out += "%s\n" % line

        if "SSH_AUTH_SOCK" in os.environ:
            self.logger.info("NO NEED TO ADD SSH_AUTH_SOCK to env")
            j.sal.fs.writeFile(bashprofile_path, out)
            return

        out += "export SSH_AUTH_SOCK=%s" % self._get_ssh_socket_path()
        out = out.replace("\n\n\n", "\n\n")
        out = out.replace("\n\n\n", "\n\n")
        j.sal.fs.writeFile(bashprofile_path, out)

    def _init_ssh_env(self, force=True):
        if force or "SSH_AUTH_SOCK" not in os.environ:
            os.putenv("SSH_AUTH_SOCK", self._get_ssh_socket_path())
            os.environ["SSH_AUTH_SOCK"] = self._get_ssh_socket_path()

    def _get_ssh_socket_path(self):

        if "SSH_AUTH_SOCK" in os.environ:
            return(os.environ["SSH_AUTH_SOCK"])

        socketpath = "%s/sshagent_socket" % os.environ.get("HOME", '/root')
        os.environ['SSH_AUTH_SOCK'] = socketpath
        return socketpath

    def ssh_agent_check(self):
        """
        will check that agent started if not will start it.
        """
        if "SSH_AUTH_SOCK" not in os.environ:
            self._init_ssh_env()
            self._add_ssh_agent_to_bash_profile()
        if not self.ssh_agent_available():
            self.logger.info('Will start agent')
            self.start_ssh_agent()

    def _load_ssh_key(self, path, duration=3600 * 24):
        """
        load ssh key referred in the path to the ssh-agent
        :param path: is name or full path
        """
        self.ssh_agent_check()
        if self.ssh_agent_check_key_is_loaded(path):
            return
        self.logger.info("load ssh key: %s", path)
        j.sal.fs.chmod(path, 0o600)
        cmd = "ssh-add -t %s %s " % (duration, path)
        j.sal.process.executeInteractive(cmd)

    def ssh_agent_check_key_is_loaded(self, key_name_path):
        """
        check if key is loaded in the ssh agent
        :param key_name_path: path or name of the ssh key
        """
        keys = self.ssh_keys_list_from_agent()
        if j.sal.fs.getBaseName(key_name_path) == key_name_path:
            # means this is a key name, not path
            keys = [j.sal.fs.getBaseName(item) for item in keys]

        if key_name_path in keys:
            self.logger.debug("ssh key: %s loaded", key_name_path)
            return True

        self.logger.debug("ssh key: %s is not loaded", key_name_path)
        return False

    def ssh_keys_load(self, path=None, duration=3600 * 24):
        """
        ensure ssh-agent has been started
        will adjust .profile file to make sure that env param is set to allow ssh-agent to find the keys
        :param path: will fall back to ~/.ssh if path is None,
                     enters interactive mode and ask which keys to load if dir path was provided
        :param duration: duration to retain the keys loaded in the agent
        """
        self.ssh_agent_check()

        if path is None:
            path = os.path.expanduser("~/.ssh")
        j.sal.fs.createDir(path)

        if "SSH_AUTH_SOCK" not in os.environ:
            self._init_ssh_env()

        self.start_ssh_agent()

        if j.sal.fs.isDir(path):
            keysinfs = self._list_not_loaded_keys(path)
            res = j.tools.console.askChoiceMultiple(
                keysinfs,
                "select ssh keys to load, use comma separated list e.g. 1,4,3 and press enter.")
        else:
            res = [j.sal.fs.getBaseName(path).replace(".pub", "")]
            path = j.sal.fs.getParent(path)

        for item in res:
            pathkey = "%s/%s" % (path, item)
            # timeout after 24 h
            self.logger.info("load sshkey: %s", pathkey)
            cmd = "ssh-add -t %s %s " % (duration, pathkey)
            j.sal.process.executeInteractive(cmd)

    def SSHKeyGetPathFromAgent(self, keyname, die=True):
        """
        Returns Path of public key that is loaded in the agent
        @param keyname: name of key loaded to agent to get its path
        """
        self.ssh_agent_check()
        for item in j.clients.ssh.ssh_keys_list_from_agent():
            if item.endswith(keyname):
                return item
        if die:
            raise RuntimeError(
                "Did not find key with name:%s, check its loaded in ssh-agent with ssh-add -l" %
                keyname)

    def SSHKeyGetFromAgentPub(self, keyname='', keypath='', die=True):
        """
        Returns Content of public key that is loaded in the agent
        @param keyname: name of key loaded to agent to get content from
        @param keypath: path of key loaded to agent to get content from
        """
        if not keyname and not keypath:
            raise RuntimeError("key name or key path needs to be specified")
        self.ssh_agent_check()
        for item in j.clients.ssh.ssh_keys_list_from_agent():
            self.logger.debug("items of sshagent : %s" % item)
            if keypath:
                if item == keypath.strip():
                    return j.sal.fs.readFile(item + ".pub")
            else:
                if j.sal.fs.getBaseName(item) == keyname:
                    return j.sal.fs.readFile(item + ".pub")
        if die:
            raise RuntimeError(
                "Did not find key with name: '%s' or path: '%s', check it is loaded in ssh-agent with ssh-add -l" %
                (keyname, keypath))

    def ssh_keys_list_from_agent(self, key_included=False):
        """
        list ssh keys from the agent
        :param key_included:
        :return: list of paths
        """
        if "SSH_AUTH_SOCK" not in os.environ:
            self._init_ssh_env()
        self.start_ssh_agent()
        cmd = "ssh-add -L"
        return_code, out, err = j.sal.process.execute(cmd, False, False, die=False)
        if return_code:
            if return_code == 1 and out.find("The agent has no identities") != -1:
                return []
            raise RuntimeError("error during listing of keys :%s" % err)
        keys = [line.split()
                for line in out.splitlines() if len(line.split()) == 3]
        if key_included:
            return list(map(lambda key: key[2:0:-1], keys))
        else:
            return list(map(lambda key: key[2], keys))

    # def SSHEnsureKeyname(self, keyname="", username="root"):
    #     if not j.sal.fs.exists(keyname):
    #         rootpath = "/root/.ssh/" if username == "root" else "/home/%s/.ssh/"
    #         fullpath = j.do.joinPaths(rootpath, keyname)
    #         if j.sal.fs.exists(fullpath):
    #             return fullpath
    #     return keyname

    def remove_item_from_known_hosts(self, item):
        """
        :param item: is ip addr or hostname to be removed from known_hosts
        """
        path = "%s/.ssh/known_hosts" % j.dirs.HOMEDIR
        out = ""
        for line in j.sal.fs.readFile(path).split("\n"):
            if line.find(item) is not -1:
                continue
            out += "%s\n" % line
        j.sal.fs.writeFile(path, out)

    def start_ssh_agent(self):
        """
        start ssh-agent, kills other agents if more than one are found
        """
        # check if more than 1 agent
        socketpath = self._get_ssh_socket_path()
        self._clean_ssh_agents(socketpath)

        if not j.sal.fs.exists(socketpath):
            j.sal.fs.createDir(j.sal.fs.getParent(socketpath))
            # ssh-agent not loaded
            self.logger.info("load ssh agent")
            _, out, err = j.sal.process.execute("ssh-agent -a %s" % socketpath,
                                                die=False,
                                                showout=False,
                                                outputStderr=False)
            if err:
                raise RuntimeError(
                    "Could not start ssh-agent, \nstdout:%s\nstderr:%s\n" % (out, err))
            else:
                if not j.sal.fs.exists(socketpath):
                    err_msg = "Serious bug, ssh-agent not started while there was no error, "\
                              "should never get here"
                    raise RuntimeError(err_msg)

                # get pid from out of ssh-agent being started
                piditems = [item for item in out.split("\n") if item.find("pid") != -1]

                # print(piditems)
                if len(piditems) < 1:
                    self.logger.debug("results was: %s", out)
                    raise RuntimeError("Cannot find items in ssh-add -l")

                self._init_ssh_env()

                pid = int(piditems[-1].split(" ")[-1].strip("; "))

                socket_path = j.sal.fs.joinPaths("/tmp", "ssh-agent-pid")
                j.sal.fs.writeFile(socket_path, str(pid))
                self._add_ssh_agent_to_bash_profile()
            return

        # ssh agent should be loaded because ssh-agent socket has been
        # found
        if os.environ.get("SSH_AUTH_SOCK") != socketpath:
            self._init_ssh_env()

    def load_ssh_key(self, path="", create_keys=False):
        """
        load ssh key in ssh-agent, if no ssh-agent is found, new ssh-agent will be started
        :path: path of ssh key to be loaded, it'll default to ~/.ssh/id_rsa if not provided
        :create_keys: if True, new keys will be created
        """
        path = path or j.sal.fs.joinPaths(j.dirs.HOMEDIR, ".ssh", "id_rsa")
        path_found = j.sal.fs.exists(path)
        if not path_found and not create_keys:
            raise RuntimeError("key %s is not found" % path)

        self.start_ssh_agent()

        # create new key if path not found
        if not path_found and create_keys:
            return_code, out, err = j.sal.process.execute("ssh-keygen -t rsa -f %s -N \"\"" % path,
                                                          die=False,
                                                          showout=False,
                                                          outputStderr=False)
            if return_code != 0:
                raise RuntimeError(
                    "Could not add key to the ssh-agent, \nstdout:%s\nstderr:%s\n" % (out, err))

        self._load_ssh_key(path)

    def ssh_agent_available(self):
        """
        Check if agent available
        :return: bool
        """
        if not j.sal.fs.exists(self._get_ssh_socket_path()):
            return False
        if "SSH_AUTH_SOCK" not in os.environ:
            self._init_ssh_env()
        return_code, out, _ = j.sal.process.execute("ssh-add -l",
                                                    showout=False,
                                                    outputStderr=False,
                                                    die=False)
        if 'The agent has no identities.' in out:
            return True
        if return_code != 0:
            return False
        else:
            return True

    def _clean_ssh_agents(self, socketpath):
        """
        Kill all agents if more than one is found
        :param socketpath: socketpath
        """
        _, out, _ = j.sal.process.execute("ps aux|grep ssh-agent", showout=False, outputStderr=False)
        res = [item for item in out.split("\n") if item.find("grep ssh-agent") == -1]
        res = [item for item in res if item.strip() != ""]
        res = [item for item in res if item[-2:] != "-l"]

        # delete socketpath if no ssh-agents found, aka, dangling socket
        socketpath_exists = j.sal.fs.exists(socketpath)
        if not res and socketpath_exists:
            j.sal.fs.remove(socketpath)
            return

        if len(res) > 1:
            self.logger.info("more than 1 ssh-agent, will kill all")

            cmd = "killall ssh-agent"
            # self.logger.info(cmd)
            j.sal.process.execute(cmd, showout=False, outputStderr=False, die=False)
            # remove previous socketpath
            j.sal.fs.remove(socketpath)
            j.sal.fs.remove(j.sal.fs.joinPaths('/tmp', "ssh-agent-pid"))

    def _list_not_loaded_keys(self, path):
        """
        list private keys that's not loaded in the ssh-agent
        :param path: path of the directory that holds they keys
        :return: list of key paths
        """
        loaded_keys = [j.sal.fs.getBaseName(item) for item in self.ssh_keys_list_from_agent()]

        keysinfs = []
        private_keys = j.sal.fs.listFilesInDir(path, filter="*.pub")
        for item in private_keys:
            if j.sal.fs.exists(item.replace(".pub", "")):
                keysinfs.append(j.sal.fs.getBaseName(item).replace(".pub", ""))
        return [item for item in keysinfs if item not in loaded_keys]
