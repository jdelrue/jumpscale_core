from Jumpscale import j
JSBASE = j.application.jsbase_get_class()

# import sys
# import time
#
# import os
# import psutil
from .NodeBase import NodeBase

class NodeHost(NodeBase):

    def __init__(self, ipaddr, sshport=22, name=""):
        """
        is host running the hypervisor
        """
        NodeBase.__init__(self, ipaddr=ipaddr, sshport=sshport, role="host", name=name)

        self.startMonitor()

    def authorizeKey(self, keypath="/home/despiegk/.ssh/perftest.pub"):
        from IPython import embed
        self.logger.debug("DEBUG NOW authorizeKey")
        embed()
