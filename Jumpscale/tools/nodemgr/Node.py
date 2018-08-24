from jumpscale import j

TEMPLATE = """
name = ""
clienttype = ""
sshclient = ""
active = false
selected = false
category = ""
description = ""
secretconfig_ = ""
pubconfig = ""
installed = false
zosclient = ""
"""

FormBuilderBaseClass = j.tools.formbuilder.baseclass_get()

JSBASE = j.application.jsbase_get_class()


class MyConfigUI(FormBuilderBaseClass):

    def init(self):
        # makes sure that this property is not auto populated, not needed when in form_add_items_pre
        self.auto_disable.append("clienttype")
        self.auto_disable.append("active")
        self.auto_disable.append("selected")

    def form_add_items_post(self):
        self.widget_add_boolean("active", default=False)
        self.widget_add_boolean("selected", default=True)
        self.widget_add_multichoice("clienttype", [
                                    "ovh", "packetnet", "ovc", "physical", "docker", "container"])


JSConfigBase = j.tools.configmanager.base_class_config


class Node(JSConfigBase):

    def __init__(self, instance, data={}, parent=None, interactive=False):
        JSConfigBase.__init__(self, instance=instance, data=data,
                              parent=parent, template=TEMPLATE, ui=MyConfigUI, interactive=interactive)
        self._sshclient = None
        self._ftpclient = None
        self._private = None

    @property
    def private(self):
        """
        if private in e.g. ovc space then will return True
        """

        if self._private is None:
            self._private = False
            if self.config.data["sshclient"] != "":
                if self.config.data["addr_priv"]:
                    self._private = self.sshclient.isprivate
        return self._private

    @property
    def addr(self):
        if self.config.data["sshclient"] != "":
            self.sshclient
            return self.sshclient.addr

    @property
    def port(self):
        if self.config.data["sshclient"] != "":
            return self.sshclient.port

    @property
    def active(self):
        return self.config.data["active"]

    @active.setter
    def active(self, val):
        self.config.data = {"active": val}

    @property
    def clienttype(self):
        return self.config.data["clienttype"]

    @clienttype.setter
    def clienttype(self, val):
        self.config.data = {"clienttype": val}

    @property
    def category(self):
        return self.config.data["category"]

    @category.setter
    def category(self, val):
        self.config.data = {"category": val}

    @property
    def name(self):
        return self.config.data["name"]

    @name.setter
    def name(self, val):
        self.config.data = {"name": val}

    @property
    def description(self):
        return self.config.data["description"]

    @description.setter
    def description(self, val):
        self.config.data = {"description": val}

    @property
    def selected(self):
        return self.config.data["selected"]

    @selected.setter
    def selected(self, val):
        self.config.data = {"selected": bool(val)}

    @property
    def secretconfig(self):
        data = self.config.data["secretconfig_"]
        data = j.data.serializers.json.loads(data)
        return data

    @secretconfig.setter
    def secretconfig(self, data):
        data = j.data.serializers.json.dumps(data)
        self.config.data = {"secretconfig_": data}

    @property
    def pubconfig(self):
        data = self.config.data["pubconfig"]
        data = j.data.serializers.json.loads(data)
        return data

    @pubconfig.setter
    def pubconfig(self, data):
        data = j.data.serializers.json.dumps(data)
        self.config.data = {"pubconfig": data}

    @property
    def isconnected(self):
        if self.config.data["sshclient"] != "":
            return self.sshclient.isconnected
        # if self._connected is None:
        #     # lets test tcp on 22 if not then 9022 which are our defaults
        #     test = j.sal.nettools.tcpPortConnectionTest(
        #         self.addr, self.port, 3)
        #     if test is False:
        #         self.logger.debug("could not connect to %s:%s, will try port 9022" %
        #                           (self.addr, self.port))
        #         if self.port == 22:
        #             test = j.sal.nettools.tcpPortConnectionTest(
        #                 self.addr, 9022, 1)
        #             if test:
        #                 self.port = 9022
        #     if test is False:
        #         self._connected = False
        #     else:
        #         self._connected = True
        #         self.active = True
            # self._sshclient = None
            # self._ftpclient = None
        # return self._connected

    @property
    def sftp(self):
        if self.isconnected:
            return self.executor.sshclient.sftp
        else:
            raise RuntimeError("node %s cannot be reached, cannot get ftpclient." % self.instance)

    @property
    def sshclient(self):
        if self._sshclient is None:
            self.logger.debug("sshclient get")
            self._sshclient = j.clients.ssh.get(instance=self.config.data["sshclient"])
            self.clienttype = "ssh"
        return self._sshclient

    @property
    def executor(self):
        if self.config.data["sshclient"] != "":
            return self.sshclient.prefab.executor

    @property
    def prefab(self):
        return j.tools.prefab.get(executor=self.executor, usecache=True)

    def clean(self):
        cmd = """
        rm -f ~/.profile_js
        rm -f ~/env.sh
        rm -f rm /etc/jumpscale.toml
        """
        self.executor.execute(cmd)

    def test_executor(self):
        self.executor.test()

    def getActiveCodeDirs(self):
        res = []
        done = []
        repo = j.clients.git.currentDirGitRepo()
        if repo is not None:
            res.append(j.tools.develop.codedirs.get(repo.type, repo.account, repo.name))
            done.append(repo.BASEDIR)
        ddirs = j.clients.git.getGitReposListLocal(account="threefoldtech")  # took predefined list
        for key, path in ddirs.items():
            self.logger.debug("try to find git dir for:%s" % path)
            try:
                repo = j.clients.git.get(path)
                if path not in done:
                    res.append(j.tools.develop.codedirs.get(repo.type, repo.account, repo.name))
            except Exception as e:
                self.logger.error(e)
        return res

    def sync(self, monitor=False):
        if not self.selected:
            self.selected = True
        ddirs = self.getActiveCodeDirs()
        for ddir in ddirs:
            dest = "%s/%s/%s/%s" % (
                self.executor.dir_paths["CODEDIR"], ddir.type, ddir.account, ddir.name)
            source = ddir.path
            self.executor.upload(source, dest, dest_prefix='', recursive=True, createdir=True)
        self.logger.info("SYNC DONE")
        if monitor:
            self.monitor()

    def portforward(self, remote, local):
        self.sshclient.port_forward_local_start(remoteport=remote, localport=local)

    def monitor(self):
        """
        will sync all active core dirs
        """
        if not self.selected:
            self.selected = True
        # paths = [item.path for item in self.getActiveCodeDirs()]
        paths = self.getActiveCodeDirs()
        j.tools.develop.sync_active(paths)

    def saveToHostfile(self):
        j.tools.prefab.local.system.ns.hostfile_set(self.name, self.addr)

    def save(self):
        self.config.save()

    def ssh(self):
        cmd = "ssh -A root@%s -p %s" % (self.sshclient.addr_variable, self.sshclient.port_variable)
        j.sal.process.executeInteractive(cmd)

    def __str__(self):
        if self.selected is True:
            return "%-14s %-25s:%-4s [%s] *" % (self.name, self.addr, self.port, self.category)
        else:
            return "%-14s %-25s:%-4s [%s]" % (self.name, self.addr, self.port, self.category)

    __repr__ = __str__
