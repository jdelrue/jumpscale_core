class Config(object):

    def __init__(self, instance="main", location=None, template=None,
                       data=None):
        """
        jsclient_object is e.g. j.clients.packet.net
        """
        self.new = False
        if data is None:
            data = {}
        self.location = self._j.data.text.toStr(location)
        self.instance = self._j.data.text.toStr(instance)
        self.error = False  # if this is true then need to call the configure part
        self._template = template
        if not self._j.data.types.string.check(template):
            if template is not None:
                raise RuntimeError(
                    "template needs to be None or string:%s" %
                    template)
        if self.instance is None:
            raise RuntimeError("instance cannot be None")

        self.reset()
        if not self._j.sal.fs.exists(self.path):
            self._j.sal.fs.createDir(self._j.sal.fs.getDirName(self.path))
            self.new = True
            dataOnFS = {}
        else:
            self.load()
            # this is data on disk, because exists, should already apply to template
            # without decryption so needs to go to self._data
            dataOnFS = self.data  # now decrypt

        # make sure template has been applied !
        data2, error = self._j.data.serializers.toml.merge(
            tomlsource=self.template, tomlupdate=dataOnFS, listunique=True)

        if data != {}:
            # update with data given
            data, error = self._j.data.serializers.toml.merge(
                tomlsource=data2, tomlupdate=data, listunique=True)
            self.data = data
        else:
            # now put the data into the object (encryption)
            self.data = data2

        # do the fancydump to make sure we really look at differences
        if self._j.data.serializers.toml.fancydumps(
                self.data) != self._j.data.serializers.toml.fancydumps(dataOnFS):
            self.logger.debug("change of data in config, need to save")
            self.save()

    def reset(self):
        self._data = {}
        self.loaded = False
        self._path = None
        self._nacl = None
        self.new = False

    @property
    def path(self):
        self.logger.debug("init getpath:%s" % self._path)
        if not self._path:
            self._path = self._j.sal.fs.joinPaths(
                self._j.data.text.toStr(self._j.tools.configmanager.path),
                self.location, self.instance + '.toml')
            self.logger.debug("getpath:%s" % self._path)
        return self._path

    @property
    def nacl(self):
        if not self._nacl:
            if self._j.tools.configmanager.keyname:
                self._nacl = self._j.data.nacl.get(
                    sshkeyname=self._j.tools.configmanager.keyname)
            else:
                self._nacl = self._j.data.nacl.get()
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
            if not self._j.sal.fs.exists(self.path):
                raise RuntimeError("should exist at this point")
            else:
                content = self._j.sal.fs.fileGetContents(self.path)
                try:
                    self._data = self._j.data.serializers.toml.loads(content)
                except Exception as e:
                    if "deserialization failed" in str(e):
                        raise RuntimeError(
                            "config file:%s is not valid toml.\n%s" %
                            (self.path, content))
                    raise e
            for key, val in self.template.items():
                ttype = self._j.data.types.type_detect(self.template[key])
                if ttype.BASETYPE == "string":
                    if key in self._data:
                        self._data[key] = self._data[key].strip()

    def save(self):
        # at this point we have the config & can write (self._data has the
        # encrypted pieces)
        self._j.sal.fs.writeFile(
            self.path, self._j.data.serializers.toml.fancydumps(self._data))

    def delete(self):
        self._j.sal.fs.remove(self.path)

    @property
    def template(self):
        if self._template is None or self._template == '':
            obj = self.jget(self.location)
            if hasattr(obj, "_child_class"):
                obj._child_class
                myvars = {}
                try:
                    exec(
                        "from %s import TEMPLATE;template=TEMPLATE" %
                        obj._child_class.__module__, myvars)
                except Exception as e:
                    if "cannot import name" in str(e):
                        raise RuntimeError(
                            "cannot find TEMPLATE in %s, please call the template: TEMPLATE" %
                            obj._child_class.__module__)
                    raise e
            else:
                myvars = {}
                try:
                    exec(
                        "from %s import TEMPLATE;template=TEMPLATE" %
                        obj.__module__, myvars)
                except Exception as e:
                    if "cannot import name" in str(e):
                        raise RuntimeError(
                            "cannot find TEMPLATE in %s, please call the template: TEMPLATE" %
                            obj._child_class.__module__)
                    raise e
            self._template = myvars["template"]
        if self._j.data.types.string.check(self._template):
            try:
                self._template = self._j.data.serializers.toml.loads(self._template)
            except Exception as e:
                if "deserialization failed" in str(e):
                    raise RuntimeError(
                        "config file:%s is not valid toml.\n%s" %
                        (self.path, self._template))
                raise e

        return self._template

    @property
    def data(self):
        res = {}
        if self._data == {}:
            self.load()
        for key, item in self._data.items():
            if key not in self.template:
                self.logger.warning(
                    "could not find key:%s in template, while it was in instance:%s" %
                    (key, self.path))
                self.logger.debug("template was:%s\n" % self.template)
                self.error = True
            else:
                ttype = self._j.data.types.type_detect(self.template[key])
                if key.endswith("_"):
                    if ttype.BASETYPE == "string":
                        if item != '' and item != '""':
                            res[key] = self.nacl.decryptSymmetric(
                                item, hex=True).decode()
                        else:
                            res[key] = ''
                    else:
                        res[key] = item
                else:
                    res[key] = item
        return res

    @data.setter
    def data(self, value):
        if self._j.data.types.dict.check(value) is False:
            raise TypeError("value needs to be dict")

        changed = False
        for key, item in value.items():
            ch1 = self.data_set(key, item, save=False)
            changed = changed or ch1

        if changed:
            # raise RuntimeError()
            self.logger.debug("changed:\n%s" % self)
            self.save()

    def data_set(self, key, val, save=True):
        if key not in self.template:
            raise RuntimeError(
                "Cannot find key:%s in template for %s" % (key, self))

        if key not in self._data or self._data[key] != val:
            ttype = self._j.data.types.type_detect(self.template[key])
            if key.endswith("_"):
                if ttype.BASETYPE == "string":
                    if val != '' and val != '""':
                        val = self.nacl.encryptSymmetric(
                            val, hex=True, salt=val)
                        if key in self._data and val == self._data[key]:
                            return False
            self._data[key] = val
            if save:
                self.save()
            return True
        else:
            return False

    @property
    def yaml(self):
        return self._j.data.serializers.toml.fancydumps(self._data)

    def __str__(self):
        out = "config:%s:%s\n\n" % (self.location, self.instance)
        out += self._j.data.text.indent(self.yaml)
        return out

    __repr__ = __str__
