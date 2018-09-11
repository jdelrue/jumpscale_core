
import os
import threading

from Jumpscale import j

from .SSHClient import SSHClient
from .SSHClientParamiko import SSHClientParamiko

JSConfigBase = j.tools.configmanager.JSBaseClassConfigs


class SSHClientFactory(JSConfigBase):

    _lock = threading.Lock()
    cache = {}

    def __init__(self):
        self.__jslocation__ = "j.clients.ssh"
        self.__imports__ = "paramiko"
        JSConfigBase.__init__(self, SSHClient)

    def new(self, addr, port=22, instance="", keyname="", timeout=5, die=True, login="root", passwd="",
            stdout=True, allow_agent=False, addr_priv="", port_priv=22, use_paramiko=False):
        """
        @param instance is the name used for the sshclient instance name
        e.g. j.clients.ssh.new("192.168.8.8",instance="mytest",login="root",passwd="rooter")


        """
        if not instance:
            instance = addr.replace(".", "-") + "-%s" % port
        data = {}
        data["port"] = port
        data["addr"] = addr
        data["sshkey"] = keyname
        data["timeout"] = timeout
        data["stdout"] = stdout
        data["login"] = login
        data["passwd_"] = passwd
        data["allow_agent"] = allow_agent
        data["addr_priv"] = addr_priv
        data["port_priv"] = port_priv

        # if key in self.cache and usecache:
        #     try:
        #         usecache = not (self.cache[key]._client is None)
        #     except j.exceptions.RuntimeError:
        #         usecache = False

        cl = self.get(instance=instance, data=data, die=die, use_paramiko=use_paramiko)
        return cl

    def get(self, instance="main", data=None, create=True, die=True, interactive=False, use_paramiko=False):
        """
        Get an instance of the SSHClient

        @param instance: instance name to get. If an instance is already loaded in memory, return it
        @param data: dictionary of data use to configure the instance
        @param use_paramiko boolean: used to use paramiko library for ssh.


        Example: IPython session
        In [1]: sshkey =  j.clients.sshkey.get(instance='dmdmconf', data=dict(path='/root/.ssh/id_rsa'))

        In [2]: sshcl = j.clients.ssh.get(instance="dmdmssh", data=dict(addr="127.0.0.1", login="root", sshkey='dmdmconf', forward_agent=False, allow_agent=True, stdout=True,
        ...:  timeout=10), use_paramiko=True)

        In [3]: sshcl.execute("ssh-add -L")
        * connect to:127.0.0.1
        * connection ok
        Could not open a connection to your authentication agent.
        ((type:runtime.error)

        In [4]: sshcl = j.clients.ssh.get(instance="dmdmssh", data=dict(addr="127.0.0.1", login="root", sshkey='dmdmconf', forward_agent=True, allow_agent=True, stdout=True, 
        ...: timeout=10), use_paramiko=True)

        In [5]: sshcl.execute("ssh-add -L")
        * connect to:127.0.0.1
        * connection ok
        Out[5]: 
        (0,
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCeq1MFCQOv3OCLO1HxdQl8V0CxAwt5AzdsNOL91wmHiG9ocgnq2yipv7qz+uCS0AdyOSzB9umyLcOZl2apnuyzSOd+2k6Cj9ipkgVx4nx4q5W1xt4MWIwKPfbfBA9gDMVpaGYpT6ZEv2ykFPnjG0obXzIjAaOsRthawuEF8bPZku1yi83SDtpU7I0pLOl3oifuwPpXTAVkK6GabSfbCJQWBDSYXXM20eRcAhIMmt79zo78FNItHmWpfPxPTWlYW02f7vVxTN/LUeRFoaNXXY+cuPxmcmXp912kW0vhK9IvWXqGAEuSycUOwync/yj+8f7dRU7upFGqd6bXUh67iMl7 /root/.ssh/id_rsa\nssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDM+No+Va36MX+f/ljwaN89w4j0Dy6Z0tSHVdx/kJhXq8QhZewc+BB7fISDPgqoPr5OoK7B5zy5tFMwf464NeRBwhAdq9LvOslJaHX9OzSavJISxpxLbK7o67dzV+BbzD3g9FL0jyd80+R39u00WzqfVr6aA2zE4kygeCak3Yj229/Y5BU64yHk1saCRxtBMa5o0vHw9gSSfJqjdw/TlhLiDe4YUn2DeC/AX9Jyh3udvl8fDHfiJeIg/TdfeMOj2iHolCzT7GV0+TMAw1tAapAALLRXpb9WCVAF8BEWFWr10dOdwc/VarPTmP4CcMxgivwqfQicSU4uPuwP0HYAOJiH /opt/code/git/despiegk/itenv_test/keys/itenv_test\n',
        '')

        """
        if data is None:
            data = {}
        instance = instance.replace(".", "-")  # allows address to be used
        if not create and instance not in self.list():
            if die:
                raise RuntimeError("could not find instance:%s" % (instance))
            else:
                return None

        if j.core.platformtype.myplatform.isMac:
            use_paramiko = True
            return SSHClientParamiko(instance=instance, data=data, interactive=interactive, parent=self)
        elif use_paramiko is True:
            return SSHClientParamiko(instance=instance, data=data, interactive=interactive, parent=self)
        else:
            return SSHClient(instance=instance, data=data, parent=self, interactive=interactive)

    def reset(self):
        """
        Close and clear cached ssh clients
        """
        with self._lock:
            for _, client in self.cache.items():
                client.close()
            self.cache = {}
        j.tools.executor.reset()

    def close(self):
        with self._lock:
            for _, client in self.cache.items():
                client.close()

    def test_packetnet(self, reset=False):
        '''
        js_shell 'j.clients.ssh.test_packetnet()'
        '''

        # will get your main connection to packet.net make sure has been configured
        packetnetcl = j.clients.packetnet.get("test")

        loginname = j.tools.myconfig.config.data["login_name"]
        if loginname == "":
            raise RuntimeError("please configure your login name, do:\n'js_config configure -l j.tools.myconfig'")
        hostname = '%s-test' % loginname

        # make sure we have an sshkey, will be without passphrase like this
        skey = j.clients.sshkey.get(instance="test10")
        skey.generate()
        skey.load()
        assert skey.is_loaded()  # check is loaded

        node = packetnetcl.startDevice(hostname=hostname, plan='baremetal_1', facility='ams1',
                                       os='ubuntu_17_10', ipxeUrl=None, wait=True, remove=reset, sshkey="test10")

        node.prefab.core.run('which curl')
        packetnetcl.removeDevice(hostname)
        self.logger.info("test successful and device removed")
