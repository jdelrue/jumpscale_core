from Jumpscale import j
import re
from io import StringIO
import os
import locale

JSBASE = j.application.JSBaseClass

from .ZOSContainer import ZOSContainer

class Builder(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.tools.builder"
        JSBASE.__init__(self)
        self._zos_client = None
        self._clients={}
        self._containers={}
        self.logger_enable()



    def zos_client_get(self,name="builder"):
        """
        if vb is True then it means we will create the zos virtualmachine locally using virtualbox

        js_shell 'j.tools.builder.zos_client_get(name="container")'

        """
        self.logger.info("zos client gent:%s"%name)
        if name not in self._clients:
            if name not in j.clients.zos.list():
                raise RuntimeError("zos client not found for:%s"%bame)

        # if not j.sal.nettools.tcpPortConnectionTest(cl.addr,cl.port,timeout=1) or not cl.is_running():
            self._clients[name] = j.clients.zos.get(name)
        return self._clients[name]


    def zos_iso_download(self, zerotierinstance="",overwrite=True):

        if zerotierinstance:
            ztcl = j.clients.zerotier.get(zerotierinstance)
            zerotierid = ztcl.config.data['networkid']
            download = "https://bootstrap.grid.tf/iso/development/%s/development%20debug" % zerotierid
            dest = "/tmp/zos_%s.iso" % zerotierid
        else:
            download = "https://bootstrap.grid.tf/iso/development/0/development%20debug"
            dest = "/tmp/zos.iso"
        j.tools.prefab.local.core.file_download(download, to=dest, overwrite=overwrite)
        self.logger.info("iso downloaded ok.")
        return dest

    @property
    def vb_client(self):
        """
        virtualbox client
        """
        return j.clients.virtualbox.client

    def zos_vb_create(self, name, zerotierinstance="", redis_port=4444, reset=False, memory=2000):
        """
        js_shell 'j.tools.builder.zos_vb_create(name="test",reset=True)'
        """
        vm = self.vb_client.vm_get(name)
        self.logger.debug(vm)

        if reset:
            vm.delete()

        if vm.exists:
            vm.start()
            self.logger.debug("vm %s started"%name)
        else:
            self.logger.info("will create zero-os:%s on redis port:%s" % (name, redis_port))
            #VM DOES NOT EXIST, Need to create the redis port should be free
            if j.sal.nettools.checkListenPort(redis_port):
                raise RuntimeError("cannot use port:%s is already in use" % redis_port)
            isopath = self.zos_iso_download(zerotierinstance)
            self.logger.info("zos vb create:%s (%s)" % (name, redis_port))
            vm.create(isopath=isopath, reset=reset, redis_port=redis_port,memory=memory)
            vm.start()

        from time import sleep

        if not j.sal.nettools.tcpPortConnectionTest("localhost", redis_port):
            retries = 60
            self.logger.info("wait till VM started (portforward on %s is on)." % redis_port)
            while retries:
                if j.sal.nettools.tcpPortConnectionTest("localhost", redis_port):
                    self.logger.info("VM port answers")
                    break
                else:
                    self.logger.debug("retry in 2s, redisport:%s"%redis_port)
                    sleep(2)
                retries -= 1
            else:
                raise RuntimeError("could not connect to VM port %s in 60 sec." % redis_port)

        r = j.clients.redis.get("localhost", redis_port, fromcache=False, ping=True, die=False, ssl=True)
        if r is None:
            retries = 100
            self.logger.info("wait till zero-os core redis on %s answers." % redis_port)
            while retries:
                r = j.clients.redis.get("localhost", redis_port, fromcache=False, ping=True, die=False, ssl=True)
                if r is not None:
                    self.logger.info("zero-os core redis answers")
                    break
                else:
                    self.logger.debug("retry in 2s")
                    sleep(2)
                retries -= 1
            else:
                raise RuntimeError("could not connect to VM port %s in 200 sec." % redis_port)

        self._redis = r

        zcl = j.clients.zos.get(name, data={"host": "localhost", "port": redis_port})
        retries = 200
        self.logger.info("internal files in ZOS are now downloaded for first time, this can take a while.")

        self.logger.info("check if we can reach zero-os client")
        while retries:
            if zcl.is_running():
                print("Successfully started ZOS on VirtualBox vm\n"
                      "with port forwarding {port} -> 6379 in VM\n"
                      "to get zos client run:\n"
                      "j.clients.zos.get('{instance}')\n"
                      "**DONE**".format(instance=name, port=redis_port))
                break
            else:
                self.logger.debug("couldn't connect to the created vm will retry in 2s")
                sleep(2)
            retries -= 1
        else:
            raise RuntimeError("could not connect to zeroos client in 400 sec.")

        self.logger.info("zero-os client active")
        self.logger.info("ping test start")
        pong = zcl.client.ping()
        self.logger.debug(pong)
        assert "PONG" in pong
        self.logger.info("ping test OK")

        if r.get("zos:active") != b'1':
            self.logger.info("partition first time")
            zcl.zerodbs.partition_and_mount_disks()
            r.set("zos:active",1)

        self.logger.debug("vm ready to be used")


    def zos_vb_delete_all(self):
        """
        js_shell 'j.tools.builder.zos_vb_delete_all()'

        """
        self.vb_client.reset_all()


    def get(self,name="builder",zosclient=None):
        if name not in self._containers:
            node = j.tools.nodemgr.set(cat="container", name=name, sshclient=name, selected=False)
            self.zos_vb_create(name="builder")
            if not zosclient:
                zosclient = self.zos_client_get()
            self._containers[name]=ZOSContainer(zosclient=zosclient,node=node)
        return self._containers[name]


    def test(self):
        """
        js_shell 'j.tools.builder.test()'
        """
        # self.zos_vb_delete_all()
        container = j.tools.builder.get()
        rc,out,err = container.node.executor.execute("ls /")
        assert "coreX\n" in out  #is a file on the root

        container.build_python_jumpscale()
