from jumpscale import j
from .ExecutorSSH import ExecutorSSH
import os

JSBASE = j.application.jsbase_get_class()


class ExecutorAsyncSSH(ExecutorSSH):

    def __init__(
            self,
            addr='',
            port=22,
            login="root",
            passwd=None,
            allow_agent=True,
            debug=False,
            look_for_keys=True,
            checkok=True,
            timeout=5,
            key_filename=(),
            passphrase=None):

        super().__init__(
            addr=addr,
            port=port,
            login=login,
            passwd=passwd,
            allow_agent=allow_agent,
            debug=debug,
            look_for_keys=look_for_keys,
            checkok=checkok,
            timeout=timeout,
            key_filename=(),
            passphrase=passphrase)
        self.init()

    def _getSSHClient(self, key_filename=None, passphrase=None):
        self._sshclient = j.clients.ssh.get_async(
            self.addr, self.port, login=self.login, passwd=self.passwd,
            allow_agent=self.allow_agent, look_for_keys=self.look_for_keys,
            key_filename=key_filename, passphrase=passphrase,
            timeout=self.timeout, usecache=True)

        return self._sshclient
