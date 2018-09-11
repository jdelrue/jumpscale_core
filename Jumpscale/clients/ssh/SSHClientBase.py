from Jumpscale import j

TEMPLATE = """
addr = ""
port = 22
addr_priv = ""
port_priv = 22
login = ""
passwd_ = ""
sshkey = ""
clienttype = ""
proxy = ""
timeout = 5
forward_agent = true
allow_agent = true
stdout = true
"""


JSConfigBase = j.tools.configmanager.JSBaseClassConfig


class SSHClientBase(JSConfigBase):

    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigBase.__init__(self, instance=instance, data=data,
                              parent=parent, template=TEMPLATE, interactive=interactive)
        self.async_ = False
        self._private = None
        self._connected = None

    @property
    def isprivate(self):
        if self._private is None:
            self._private = self.config.data["addr_priv"] and not j.sal.nettools.tcpPortConnectionTest(
                self.config.data["addr"], self.config.data["port"], 1)
        return self._private

    # SETTERS & GETTERS
    @property
    def addr(self):
        if self._private == True:
            return self.addr_variable
        return self.config.data["addr"]

    @property
    def addr_variable(self):
        if self.isprivate:
            return self.config.data["addr_priv"]
        else:
            return self.config.data["addr"]

    @addr.setter
    def addr(self, val):
        self.config.data = {"addr": val}

    @property
    def port(self):
        if self._private is True:
            return self.port_variable
        return self.config.data["port"]

    @property
    def port_variable(self):
        if self.isprivate:
            return self.config.data["port_priv"]
        else:
            return self.config.data["port"]

    @port.setter
    def port(self, val):
        self.config.data = {"port": int(val)}

    @property
    def forward_agent(self):
        return self.config.data["forward_agent"]

    @forward_agent.setter
    def forward_agent(self, val):
        self.config.data = {"forward_agent": bool(val)}

    @property
    def timeout(self):
        return self.config.data["timeout"]

    @timeout.setter
    def timeout(self, val):
        self.config.data = {"timeout": int(val)}

    @property
    def proxy(self):
        """
        ssh client to server which acts as proxy
        """
        name = self.config.data["proxy"]
        return j.clients.ssh.get(name)

    @proxy.setter
    def proxy(self, val):
        self.config.data = {"proxy": bool(val)}

    @property
    def stdout(self):
        return self.config.data["stdout"]

    @stdout.setter
    def stdout(self, val):
        self.config.data = {"stdout": bool(val)}

    @property
    def allow_agent(self):
        return self.config.data["allow_agent"]

    @allow_agent.setter
    def allow_agent(self, val):
        self.config.data = {"allow_agent": bool(val)}

    @property
    def login(self):
        return self.config.data["login"]

    @login.setter
    def login(self, val):
        self.config.data = {"login": str(val)}

    @property
    def passwd(self):
        return self.config.data["passwd_"]

    @passwd.setter
    def passwd(self, val):
        self.config.data = {"passwd_": str(val)}

    @property
    def sshkey(self):
        """
        return right sshkey
        """
        if not self.config.data["sshkey"]:
            return None
        return j.clients.sshkey.get(self.config.data["sshkey"])

    @sshkey.setter
    def sshkey(self, val):
        self.config.data = {"sshkey": str(val)}

    @property
    def isconnected(self):
        if self._connected is None:
            self._connected = j.sal.nettools.tcpPortConnectionTest(
                self.addr_variable, self.port_variable, 1)
            self.active = True
            self._sshclient = None
            self._ftpclient = None
        return self._connected

    def ssh_authorize(self, user, key=None, pubkey=None):
        """add key to authorized users, if key is specified will get public key from sshkey client,
        or can directly specify the public key. If both are specified key name instance will override public key.

        :param user: user to authorize
        :type user: str
        :param key: name of sshkey instance to use, defaults to None
        :param key: str, optional
        :param pubkey: public key to authorize, defaults to None
        :param pubkey: str, optional
        """
        if key:
            sshkey = j.clients.sshkey.get(key)
            pubkey = sshkey.pubkey
        if pubkey in [None,""]:
            raise RuntimeError("pubkey not given")
        self.prefab.system.ssh.authorize(user=user, key=pubkey)
