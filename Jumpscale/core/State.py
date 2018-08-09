import pytoml
from Jumpscale import j

mascot = '''
                                                        .,,'
                                                   'c.cool,..',,,,,,,.
                                                  'dxocol:l:;,'......';:,.
                                              .lodoclcccc,...............;:.
                                                ':lc:;;;;;.................:;
            JUMPSCALE                         :oc;'..................,'.....,;
            ---------                        olc'.......'...........,. .,:'..:.
                                            ,oc'......;,',..........od.   'c..'
                                            ;o:......l,   ':........dWkkN. ,;..
                                            .d;.....:K. ;   l'......:KMMM: ''.';'
                                             :,.....cNWNMx  .o.......;OWNc,.....,c
                                              c.....'kMMMX   l.........,,......;'c.
                                             l........xNNx...,. 'coxk;',;;'....;xd.
                                            .l..,...........';;;:dkkc::;;,.....'l'
                                             o'x............lldo,.'o,cl:;'...;,;;
                                           ..;dd'...........':'.,lkkk,.....,.l;l
                                       .',,....'l'.co..;'..........'.....;d,;:
                                    ';;..........;;o:c;,dl;oc,'......';;locc;
                                 ,:;...................;;:',:'',,,,,'.      .,.
                              .::.................................            'c
                            .:,...................................           . .l
                          .:,......................................          'l':
                        .;,.......................................            .l.
                     ';c:.........................................          ;:.';
              ',;::::'...........................................            :d;l;.
           'lolclll,,'..............................','..........            .dccco;
          loooool:,'..............................'l'..........     '.       cocclll..
        .lol:;'...................................::.,,'........    .o     .ldcccccccco:
       ,lcc'.........,;...,;.    ................',c:,''........,.  .o   .;;xccccccccld:
        .';ccc:;;,,'.  ...  ..''..             ;;'...............';.c'.''.  ;loolloooo;
                                ..',,,,,,,''...:o,.................c           ....
                                               .;l.................c.
                                                 ;;;;,'..........,;,
                                                    .':ldddoooddl
'''

JSBASE = j.application.jsbase_get_class()


class State(JSBASE):
    """

    """

    def __init__(self, executor):
        JSBASE.__init__(self)
        self.readonly = False
        self.executor = executor
        self.load()

    def load(self, reset=False):
        if reset:
            self.executor.reset()

        if self.executor.stateOnSystem is None:
            raise RuntimeError(
                "cannot load state because state on system in executor == None")

        self.configJSPath = self.executor.stateOnSystem["path_jscfg"] + "/jumpscale.toml"
        self.configStatePath = self.executor.stateOnSystem["path_jscfg"] + "/state.toml"
        self._configState = self.executor.stateOnSystem["cfg_state"]
        self._configJS = self.executor.stateOnSystem["cfg_jumpscale"]

    @property
    def cfgPath(self):
        return self.executor.stateOnSystem["path_jscfg"]

    @property
    def versions(self):
        versions = {}
        for name, path in self.configGet('plugins', {}).items():
            repo = j.clients.git.get(path)
            _, versions[name] = repo.getBranchOrTag()
        return versions

    def stateSet(self, key, val, save=True):
        """Set a section in Jumpscale's state.toml

        :param key: section name
        :type key: str
        :param val: value to set
        :type val: dict
        :param save: writes to the file if true
        :param save: bool, optional
        :return: true if new value is set, false if already exists
        :rtype: bool
        """

        return self._set(
            key=key,
            val=val,
            save=save,
            config=self._configState,
            path=self.configStatePath)

    def stateGet(self, key, defval=None, set=False):
        """gets a section from state.toml

        :param key: section name
        :type key: str
        :param defval: value to return if not found if set is true will add it to state, defaults to None
        :param defval: dict, optional
        :param set: if true will set the specified defval, defaults to False
        :param set: bool, optional
        :return: the section data
        :rtype: dict
        """

        return self._get(
            key=key,
            defval=defval,
            set=set,
            config=self._configState,
            path=self.configStatePath)

    def configGet(self, key, defval=None, set=False):
        """gets a section from jumpscale.toml

        :param key: section name
        :type key: str
        :param defval: value to return if not found if set is true will add it to config, defaults to None
        :param defval: dict, optional
        :param set: if true will set the specified defval, defaults to False
        :param set: bool, optional
        :return: the section data
        :rtype: dict
        """
        return self._get(
            key=key,
            defval=defval,
            set=set,
            config=self._configJS,
            path=self.configJSPath)

    def configSet(self, key, val, save=True):
        """Set a section in Jumpscale's jumpscale.toml

        :param key: section name
        :type key: str
        :param val: value to set
        :type val: dict
        :param save: writes to the file if true
        :param save: bool, optional
        :return: true if new value is set, false if already exists
        :rtype: bool
        """
        return self._set(
            key=key,
            val=val,
            save=save,
            config=self._configJS,
            path=self.configJSPath)

    @property
    def mascot(self):
        return mascot

    def _get(self, key, defval=None, set=False, config=None, path=""):
        """
        """
        if key in config:
            return config[key]
        else:
            if defval is not None:
                if set:
                    self._set(key, defval, config=config, path=path)
                return defval
            else:
                raise j.exceptions.Input(
                    message="could not find config key:%s in executor:%s" %
                    (key, self), level=1, source="", tags="", msgpub="")

    def _set(self, key, val, save=True, config=None, path=""):
        """
        @return True if changed
        """
        if key in config:
            val2 = config[key]
        else:
            val2 = None
        if val != val2:
            config[key] = val
            self._config_changed = True
            if save:
                self.configSave(config, path)
            return True
        else:
            if save:
                self.configSave(config, path)
            return False

    def configSetInDict(self, key, dkey, dval):
        """Set a value to a key in a section in the config file
        For example:
        [section]
        key = "value"

        :param key: section name
        :type key: str
        :param dkey: key to set its value
        :type dkey: str
        :param dval: value to set
        :type dval: str
        """

        self._setInDict(
            key=key,
            dkey=dkey,
            dval=dval,
            config=self._configJS,
            path=self.configJSPath)

    def stateSetInDict(self, key, dkey, dval):
        """Set a value to a key in a section in the state file
        For example:
        [section]
        key = "value"

        :param key: section name
        :type key: str
        :param dkey: key to set its value
        :type dkey: str
        :param dval: value to set
        :type dval: str
        """
        self._setInDict(
            key=key,
            dkey=dkey,
            dval=dval,
            config=self._configState,
            path=self.configStatePath)

    def _setInDict(self, key, dkey, dval, config, path=""):
        """
        will check that the val is a dict, if not set it and put key & val in
        """
        if key in config:
            val2 = config[key]
        else:
            self._set(key, {}, save=True, config=config, path=path)
            val2 = {}
        if dkey in val2:
            if val2[dkey] != dval:
                self._config_changed = True
        else:
            self._config_changed = True

        val2[dkey] = dval

        config[key] = val2
        # print("config set dict %s:%s:%s" % (key, dkey, dval))
        self.configSave(path)

    def configGetFromDict(self, key, dkey, default=None):
        """Get value of key in a section in the config file
        For example:
        [section]
        key = "value"

        :param key: section name
        :type key: str
        :param dkey: key to get its value
        :type dkey: str
        :param default: default value to return if not found, defaults to None
        :param default: str, optional
        :return: key value
        :rtype: str
        """

        return self._getFromDict(
            key=key,
            dkey=dkey,
            default=default,
            config=self._configJS,
            path=self.configJSPath)

    def stateGetFromDict(self, key, dkey, default=None):
        """Get value of key in a section in the state file
        For example:
        [section]
        key = "value"

        :param key: section name
        :type key: str
        :param dkey: key to get its value
        :type dkey: str
        :param default: default value to return if not found, defaults to None
        :param default: str, optional
        :return: key value
        :rtype: str
        """
        return self._getFromDict(
            key=key,
            dkey=dkey,
            default=default,
            config=self._configState,
            path=self.configStatePath)

    def _getFromDict(self, key, dkey, default=None, config=None, path=""):
        """
        get val from subdict
        """
        if key not in config:
            self._set(key, val={}, save=True, config=config, path=path)

        if dkey not in config[key]:
            if default is not None:
                return default
            raise RuntimeError(
                "Cannot find dkey:%s in state config for dict '%s'" %
                (dkey, key))

        return config[key][dkey]

    def configGetFromDictBool(self, key, dkey, default=None):
        """Get boolean value of key if value is in [1, 0, 'yes', 'no', 'y', 'n']
        For example:
        [section]
        key = "yes"

        :param key: section name
        :type key: str
        :param dkey: key to get its value
        :type dkey: str
        :param default: default value to return if not found, defaults to None
        :param default: str, optional
        :return: key value
        :rtype: str
        """
        return self._getFromDictBool(
            key=key,
            dkey=dkey,
            default=default,
            config=self._configJS)

    def stateGetFromDictBool(self, key, dkey, default=None):
        """Get boolean value of key if value is in [1, 0, 'yes', 'no', 'y', 'n']
        For example:
        [section]
        key = "yes"

        :param key: section name
        :type key: str
        :param dkey: key to get its value
        :type dkey: str
        :param default: default value to return if not found, defaults to None
        :param default: str, optional
        :return: key value
        :rtype: str
        """
        self._getFromDictBool(
            key=key,
            dkey=dkey,
            default=default,
            config=self._configState)

    def _getFromDictBool(self, key, dkey, default=None, config=None, path=""):
        if key not in config:
            self._set(key, val={}, save=True, config=config, path=path)

        if dkey not in config[key]:
            if default is not None:
                return default
            raise RuntimeError(
                "Cannot find dkey:%s in state config for dict '%s'" %
                (dkey, key))

        val = config[key][dkey]
        if val in [
                1,
                True] or (
                isinstance(
                val,
                str) and val.strip().lower() in [
                    "true",
                    "1",
                    "yes",
                "y"]):
            return True
        else:
            return False

    def configSetInDictBool(self, key, dkey, dval):
        """Set a value to a key in a section in the config file, value in [1, 0, 'yes', 'no', 'y', 'n']
        For example:
        [section]
        key = "value"

        :param key: section name
        :type key: str
        :param dkey: key to set its value
        :type dkey: str
        :param dval: value to set
        :type dval: str
        """
        self._setInDictBool(
            key=key,
            dkey=dkey,
            dval=dval,
            config=self._configJS,
            path=self.configJSPath)

    def stateSetInDictBool(self, key, dkey, dval):
        """Set a value to a key in a section in the state file, value in [1, 0, 'yes', 'no', 'y', 'n']
        For example:
        [section]
        key = "value"

        :param key: section name
        :type key: str
        :param dkey: key to set its value
        :type dkey: str
        :param dval: value to set
        :type dval: str
        """
        self._setInDictBool(
            key=key,
            dkey=dkey,
            dval=dval,
            config=self._configState,
            path=self.configStatePath)

    def _setInDictBool(self, key, dkey, dval, config, path):
        """
        will check that the val is a dict, if not set it and put key & val in
        """
        if dval in [
                1,
                True] or str(dval).strip().lower() in [
                "true",
                "1",
                "yes",
                "y"]:
            dval = "1"
        else:
            dval = "0"
        return self._setInDict(key, dkey, dval, config, path)

    def configUpdate(self, ddict, overwrite=True):
        """
        will walk over 2 levels deep of the passed dict(dict of dict) & update it with the newely sent parameters
        and overwrite the values of old parameters only if overwrite is set to True

        keyword arguments:
        ddict -- 2 level dict(dict of dict)
        overwrite -- set to true if you want to overwrite values of old keys
        """
        for key0, val0 in ddict.items():
            if not j.data.types.dict.check(val0):
                raise RuntimeError(
                    "Value of first level key has to be another dict.")

            if key0 not in self._configJS:
                self.configSet(key0, val0, save=False)
            else:
                for key1, val1 in val0.items():
                    if key1 not in self._configJS[key0]:
                        self._configJS[key0][key1] = val1
                        self._config_changed = True
                    else:
                        if overwrite:
                            self._configJS[key0][key1] = val1
                            self._config_changed = True
        self.configSave()

    def configSave(self, config=None, path=""):
        """
        Writes config to specified path
        """
        if self.executor.state_disabled:
            return
        if self.readonly:
            raise j.exceptions.Input(
                message="cannot write config to '%s', because is readonly" %
                self, level=1, source="", tags="", msgpub="")
        if config and path:
            data = pytoml.dumps(config)
            self.executor.file_write(path, data)
            return
        data = pytoml.dumps(self._configJS)
        self.executor.file_write(self.configJSPath, data, sudo=True)
        data = pytoml.dumps(self._configState)
        self.executor.file_write(self.configStatePath, data, sudo=True)
        self.executor.reset()  # make sure all caching is reset

    @property
    def config_js(self):
        return self._configJS

    @property
    def config_my(self):
        return self._configJS["myconfig"]

    @property
    def config_system(self):
        return self._configJS["system"]

    def reset(self):
        self._configJS = {}
        self._configState = {}
        self.configSave()

    def __repr__(self):
        return str(self._configJS)

    def __str__(self):
        return str(self._configJS)
