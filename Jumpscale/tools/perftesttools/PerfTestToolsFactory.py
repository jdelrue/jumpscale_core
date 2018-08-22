from jumpscale import j

from .NodeNas import NodeNas
from .NodeHost import NodeHost
from .NodeMonitor import NodeMonitor
from .MonitorTools import *
from .InfluxDumper import *

import os

class PerfTestToolsFactory:
    """ j.tools.perftesttools.getNodeMonitor("localhost",22)
        make sure there is influxdb running on monitor node (root/root)
        make sure there is redis running on monitor node with passwd as
        specified

        for example script
        call self.getScript()
    """

    __jslocation__ = "j.tools.perftesttools"

    def __init__(self):
        self.__imports__ = "psutil"
        self.monitorNodeIp = None
        self.monitorNodeSSHPort = None
        self.redispasswd = ""
        self.nodes = []
        self.sshkey = None

    def init(self, testname, monitorNodeIp, sshPort,
                redispasswd="", sshkey=None):
        """ sshkey can be path to key or the private key itself
            the goal is you use ssh-agent & your keys pre-loaded,
            best not to manually work with keys !!!
        """
        self.testname = testname
        self.monitorNodeIp = monitorNodeIp
        self.monitorNodeSSHPort = sshPort
        self.redispasswd = redispasswd
        if sshkey is not None and self.j.sal.fs.exists(path=sshkey):
            sshkey = self.j.sal.fs.fileGetContents(sshkey)
            self.sshkey = sshkey

            path = "%s/.ssh/testevn" % os.environ["HOME"]
            self.j.sal.fs.writeFile(path, self.sshkey)
            self.j.sal.fs.chmod(path, 0o600)

        self.j.sal.ssh.sshkeys_load()

    def getNodeNAS(self, ipaddr, sshport=22, nrdisks=0, fstype="xfs",
                role='', debugdisk="", name=""):
        """
        @param debug when True it means we will use this for
                development purposes & not init & mount local disks
        """
        n = NodeNas(ipaddr=ipaddr, sshport=sshport, fstype=fstype,
                debugdisk=debugdisk, name=name)
        self.nodes.append(n)
        return n

    def getNodeHost(self, ipaddr, sshport=22, name=""):
        n = NodeHost(ipaddr, sshport, name=name)
        self.nodes.append(n)
        return n

    def getNodeBase(self, ipaddr, sshport=22, name=""):
        n = NodeHost(ipaddr, sshport, name=name)
        self.nodes.append(n)
        return n

    def getNodeMonitor(self, name=""):
        n = NodeMonitor(self.monitorNodeIp, self.monitorNodeSSHPort, name=name)
        self.nodes.append(n)
        return n

    def getExampleScript(self, path=None):
        dirpath = self.j.sal.fs.getDirName(os.path.realpath(__file__))
        path2 = "%s/exampleScriptexampleScript" % dirpath
        C = self.j.sal.fs.fileGetContents(path2)
        if path is not None:
            self.j.sal.fs.writeFile(filename=path, contents=C)
        return C

    def monitor(self):
        """ will do monitoring & send results to redis, env is used to
            get config parameters from
        """
        nodename = os.environ["nodename"]
        if nodename == "":
            nodename = self.j.sal.process.execute("hostname")[1].strip()

        net = os.environ["net"] == '1'
        disks = [item.strip() for item in os.environ["disks"].split(",") \
                    if item.strip() != ""]

        cpu = os.environ["cpu"] == '1'
        redis = self.j.clients.redis.get(os.environ["redishost"],
                    os.environ["redisport"])

        m = MonitorTools(redis, nodename)
        m.startMonitorLocal(disks, cpu, net)

    def influxpump(self):
        """ will dump redis stats into influxdb & env is used to
            get config parameters from
            influxdb is always on localhost & std login/passwd
        """
        redis = self.j.clients.redis.get(os.environ["redishost"],
                                    os.environ["redisport"])
        d = InfluxDumper(os.environ["testname"], redis,
                                    server=os.environ['idbhost'],
                         port=os.environ['idbport'],
                                    login=os.environ['idblogin'],
                                    passwd=os.environ['idbpasswd'])
        d.start()
