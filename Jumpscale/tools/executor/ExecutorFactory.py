import threading


class ExecutorFactory(object):
    _lock = threading.Lock()

    _executors = {}
    _executors_async = {}
    __jslocation__ = "j.tools.executor"

    def local_get(self):
        """
        @param executor is localhost or $hostname:$port or
                        $ipaddr:$port or $hostname or $ipaddr

        for ssh only root access is allowed !

        """
        if 'localhost' not in self._executors:
            DL = self._jsbase(("ExecutorLocal",
                    'Jumpscale.tools.executor.ExecutorLocal'))
            self._executors['localhost'] = DL()
        return self._executors['localhost']

    def ssh_get(self, sshclient):
        with self._lock:
            if self._j.data.types.string.check(sshclient):
                sshclient = self._j.clients.ssh.get(instance=sshclient)
            key = '%s:%s:%s' % (
                sshclient.config.data['addr'],
                sshclient.config.data['port'],
                sshclient.config.data['login'])
            if key not in self._executors or \
                    self._executors[key].sshclient is None:
                DS = self._jsbase(("ExecutorSSH",
                    'Jumpscale.tools.executor.ExecutorSSH'))
                self._executors[key] = DS(sshclient=sshclient)
            return self._executors[key]

    def serial_get(self, device, baudrate=9600, type="serial", parity="N",
                    stopbits=1, bytesize=8, timeout=1):
        DS = self._jsbase(("ExecutorSerial",
            'Jumpscale.tools.executor.ExecutorSerial'))
        return DS(device, baudrate=baudrate, type=type, parity=parity,
                   stopbits=stopbits, bytesize=bytesize, timeout=timeout)

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
        if self._j.data.types.string.check(sshclient):
            sshclient = self._j.clients.ssh.get(instance=sshclient)
        # @TODO: *1 needs to be fixed
        raise RuntimeError("not implemented")
        with self._lock:
            key = '%s:%s:%s' % (addr, port, login)
            if key not in self._executors_async or usecache is False:
                D = self._jsbase(("ExecutorAsyncSSH",
                        'Jumpscale.tools.executor.ExecutorAsyncSSH'))
                self._executors_async[key] = D(
                    addr=addr, port=port, login=login, passwd=passwd,
                    debug=debug, allow_agent=allow_agent,
                    look_for_keys=look_for_keys, timeout=timeout,
                    key_filename=key_filename, passphrase=passphrase)

            return self._executors_async[key]

    def getLocalDocker(self, container_id_or_name):
        D = self._jsbase(("ExecutorDocker", 
                'Jumpscale.tools.executor.ExecutorDocker'))
        return D.from_local_container(container_id_or_name)

    def reset(self, executor=None):
        """
        reset remove the executor passed in argument from the cache.
        """
        if executor is None:
            self._executors = {}
            self._executors_async = {}
            self._j.tools.prefab.prefabs_instance = {}
            return

        if self._j.data.types.string.check(executor):
            key = executor
        elif executor.type == 'ssh':
            sshclient = executor.sshclient
            key = '%s:%s:%s' % (
                sshclient.config.data['addr'],
                sshclient.config.data['port'],
                sshclient.config.data['login'])
        else:
            raise self._j.exceptions.Input(
                message='executor type not recognize.')
        with self._lock:
            if key in self._executors:
                exe = self._executors[key]
                self._j.tools.prefab.reset(exe.prefab)
                del self._executors[key]
