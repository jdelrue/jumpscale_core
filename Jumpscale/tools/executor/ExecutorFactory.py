from Jumpscale import j
JSBASE = j.application.JSBaseClass

from .ExecutorSSH import *
from .ExecutorLocal import *
from .ExecutorAsyncSSH import ExecutorAsyncSSH
from .ExecutorSerial import ExecutorSerial
import threading

JSBASE = j.application.JSBaseClass


class ExecutorFactory(JSBASE):
    # _lock = threading.Lock()

    _executors = {}
    _executors_async = {}

    def __init__(self):
        self.__jslocation__ = "j.tools.executor"
        JSBASE.__init__(self)

    def local_get(self):
        """
        @param executor is localhost or $hostname:$port or
                        $ipaddr:$port or $hostname or $ipaddr

        for ssh only root access is allowed !

        """
        if 'localhost' not in self._executors:
            self._executors['localhost'] = ExecutorLocal()
        return self._executors['localhost']

    def ssh_get(self, sshclient):
        with self._lock:
            if j.data.types.string.check(sshclient):
                sshclient = j.clients.ssh.get(instance=sshclient)
            key = '%s:%s:%s' % (sshclient.config.data['addr'],
                                sshclient.config.data['port'], sshclient.config.data['login'])
            if key not in self._executors or self._executors[key].sshclient is None:
                self._executors[key] = ExecutorSSH(sshclient=sshclient)
            return self._executors[key]

    def serial_get(self, device, baudrate=9600, type="serial", parity="N", stopbits=1, bytesize=8, timeout=1):
        return ExecutorSerial(device, baudrate=baudrate, type=type, parity=parity, stopbits=stopbits, bytesize=bytesize, timeout=timeout)

    def asyncssh_get(self, sshclient):
        """
        returns an asyncssh-based executor where:
        allow_agent: uses the ssh-agent to connect
        look_for_keys: will iterate over keys loaded on the ssh-agent and
                       try to use them to authenticate
        pushkey: authorizes itself on remote
        pubkey: uses this particular key (path) to connect
        usecache: gets cached executor if available. False to get a new one.
        """
        if j.data.types.string.check(sshclient):
            sshclient = j.clients.ssh.get(instance=sshclient)
        # @TODO: *1 needs to be fixed
        raise RuntimeError("not implemented")
        with self._lock:
            key = '%s:%s:%s' % (addr, port, login)
            if key not in self._executors_async or usecache is False:
                self._executors_async[key] = ExecutorAsyncSSH(addr=addr,
                                                              port=port,
                                                              login=login,
                                                              passwd=passwd,
                                                              debug=debug,
                                                              allow_agent=allow_agent,
                                                              look_for_keys=look_for_keys,
                                                              timeout=timeout,
                                                              key_filename=key_filename,
                                                              passphrase=passphrase)

            return self._executors_async[key]

    def getLocalDocker(self, container_id_or_name):
        from .ExecutorDocker import ExecutorDocker
        return ExecutorDocker.from_local_container(container_id_or_name)

    def reset(self, executor=None):
        """
        reset remove the executor passed in argument from the cache.
        """
        if executor is None:
            self._executors = {}
            self._executors_async = {}
            j.tools.prefab.prefabs_instance = {}
            return

        if j.data.types.string.check(executor):
            key = executor
        elif executor.type == 'ssh':
            sshclient = executor.sshclient
            key = '%s:%s:%s' % (
                sshclient.config.data['addr'],
                sshclient.config.data['port'],
                sshclient.config.data['login'])
        else:
            raise j.exceptions.Input(
                message='executor type not recognize.')
        with self._lock:
            if key in self._executors:
                exe = self._executors[key]
                j.tools.prefab.reset(exe.prefab)
                del self._executors[key]
