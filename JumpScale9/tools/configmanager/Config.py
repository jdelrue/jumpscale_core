from js9 import j
# import os
# import copy


class Config():

    def __init__(self, instance="main", location=None, template={}, sshkey_path=None):
        """
        jsclient_object is e.g. j.clients.packet.net
        """
        self._nacl = None
        self.location = location
        self.instance = instance
        self._template = template
        self.loaded = False
        self._path = None
        self._data = {}
        if self.instance is None:
            raise RuntimeError("instance cannot be None")
        self._nacl = None
        self._sshkey_path = sshkey_path

    @property
    def path(self):
        if not self._path:
            self._path = j.sal.fs.joinPaths(j.tools.configmanager.path_configrepo, self.location, self.instance + '.toml')
            j.sal.fs.createDir(j.sal.fs.getParent(self._path))
        return self._path

    @property
    def sshkey_path(self):
        return self._sshkey_path

    @sshkey_path.setter
    def sshkey_path(self, val):
        self._sshkey_path = val

    @property
    def nacl(self):
        if not self._nacl:
            j.clients.ssh.ssh_agent_check()
            if not self._sshkey_path:
                keys = j.clients.ssh.ssh_keys_list_from_agent()
                if not keys:
                    j.clients.ssh.ssh_keys_load()
                keys = j.clients.ssh.ssh_keys_list_from_agent()
                if len(keys) >= 1:
                    key = j.tools.console.askChoice(
                        [k for k in keys], descr="Please choose which key to pass to the NACL")
                    sshkeyname = j.sal.fs.getBaseName(key)
                else:
                    raise RuntimeError(
                        "You need to configure at least one sshkey")
            else:
                j.clients.ssh.load_ssh_key(path=self._sshkey_path)
                sshkeyname = j.sal.fs.getBaseName(self._sshkey_path)
            self._nacl = j.data.nacl.get(sshkeyname=sshkeyname)
        return self._nacl

    def instance_set(self, instance):
        """
        will change instance name & delete data
        """
        self.instance = instance
        self.load(reset=True)

    def load(self, reset=False):
        """
        @RETURN if 1 means did not find the toml file so is new
        """
        if reset or self._data == {}:
            if not j.sal.fs.exists(self.path):
                j.sal.fs.touch(self.path)
                self._data, error = j.data.serializer.toml.merge(
                    tomlsource=self.template, tomlupdate={}, listunique=True)
                return 1
            else:
                content = j.sal.fs.fileGetContents(self.path)
                data = j.data.serializer.toml.loads(content)
                # merge found data into template
                self._data, error = j.data.serializer.toml.merge(
                    tomlsource=self.template, tomlupdate=data, listunique=True)
                return 0
        return 0

    # def interactive(self):
    #     print("Did not find config file:%s"%self.location)
    #     self.instance=j.tools.console.askString("specify name for instance", defaultparam=self.instance)
    #     self.configure()

    # def configure(self):
    #     if self.ui is None:
    #         raise RuntimeError("cannot call configure UI because not defined yet, is None")
    #     myconfig = self.ui(name=self.path, config=self.data, template=self.template)
    #     myconfig.run()
    #     self.data = myconfig.config
    #     self.save()

    def save(self):
        # at this point we have the config & can write (self._data has the encrypted pieces)
        j.sal.fs.writeFile(
            self.path, j.data.serializer.toml.fancydumps(self._data))

    @property
    def template(self):
        if self._template is None or self._template == '':
            raise RuntimeError("self._template has to be set")
        if j.data.types.string.check(self._template):
            self._template = j.data.serializer.toml.loads(self._template)
        return self._template

    @property
    def data(self):
        res = {}
        if self._data == {}:
            self.load()
        for key, item in self._data.items():
            ttype = j.data.types.type_detect(self.template[key])
            if key.endswith("_"):
                if ttype.BASETYPE == "string":
                    if item != '' and item != '""':
                        res[key] = self.nacl.decryptSymmetric(item, hex=True).decode()
                    else:
                        res[key] = ''
                else:
                    res[key] = item
            else:
                res[key] = item
        return res

    @data.setter
    def data(self, value):
        if j.data.types.dict.check(value) is False:
            raise TypeError("value needs to be dict")

        for key, item in value.items():
            self.data_set(key, item, save=False)

        self.save()

    def data_set(self, key, val, save=True):
        if key not in self.template:
            raise RuntimeError(
                "Cannot find key:%s in template for %s" % (key, self))

        if (key in self._data and self._data[key] != val) or key not in self._data:
            ttype = j.data.types.type_detect(self.template[key])
            if key.endswith("_"):
                if ttype.BASETYPE == "string":
                    if val != '' and val != '""':
                        val = self.nacl.encryptSymmetric(
                            val, hex=True, salt=val)
            self._data[key] = val
            if save:
                self.save()

    @property
    def yaml(self):
        return j.data.serializer.toml.fancydumps(self._data)

    def __str__(self):
        out = "config:%s:%s\n\n" % (self.location, self.instance)
        out += j.data.text.indent(self.yaml)
        return out

    __repr__ = __str__
