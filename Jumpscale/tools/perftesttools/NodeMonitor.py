from Jumpscale import j
JSBASE = j.application.JSBaseClass

from .NodeBase import NodeBase



class NodeMonitor(NodeBase):

    def __init__(self, ipaddr, sshport, name=""):
        NodeBase.__init__(self, ipaddr=ipaddr, sshport=sshport, role="monitor", name=name)
        if self.name == "":
            self.name = "monitor"

    def start(self):
        self.startInfluxPump()

    def startInfluxPump(self):
        env = {}

        if j.tools.perftesttools.monitorNodeIp is None:
            raise j.exceptions.RuntimeError("please do j.tools.perftesttools.init() before calling this")

        if self.influx_host is None:
            env["redishost"] = j.tools.perftesttools.monitorNodeIp
        else:
            env["redishost"] = self.redis_host
        env["redisport"] = 9999

        if self.influx_host is None:
            env["idbhost"] = j.tools.perftesttools.monitorNodeIp
        else:
            env["idbhost"] = self.influx_host

        env["idbport"] = self.influx_port
        env["idblogin"] = self.influx_login
        env["idbpasswd"] = self.influx_password
        env["testname"] = j.tools.perftesttools.testname
        # this remotely let the influx pump work: brings data from redis to influx

        self.prepareTmux("mgmt", ["influxpump", "mgmt"])
        self.executeInScreen("influxpump", "js 'j.tools.perftesttools.influxpump()'", env=env, session="mgmt")

    def getTotalIOPS(self):
        return (self.getStatObject(key="iops")["val"], self.getStatObject(
            key="iops_r")["val"], self.getStatObject(key="iops_w")["val"])

    def getTotalThroughput(self):
        return (self.getStatObject(key="kbsec")["val"], self.getStatObject(
            key="kbsec_r")["val"], self.getStatObject(key="kbsec_w")["val"])

    def getStatObject(self, node="total", key="writeiops"):
        data = self.redis.hget("stats:%s" % node, key)
        if data is None:
            return {"val": None}
        data = j.data.serializers.json.loads(data)
        return data

    def loopPrintStatus(self):
        while True:
            self.logger.debug("total iops:%s (%s/%s)" % self.getTotalIOPS())
            self.logger.debug("total throughput:%s (%s/%s)" % self.getTotalThroughput())
            time.sleep(1)
