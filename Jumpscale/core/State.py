import pytoml
import os
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


class State(object):
    """

    """

    __jscorelocation__ = 'j.core.state'

    def __init__(self, j, executor=None,readonly=False):
        self._j = j
        self.readonly = readonly
        self.executor = executor
        if executor is not None:
            if self._j.core._db_fakeredis:
                #make sure we use real redis
                self._j.clients.redis.core_start()
                self._j.core._db = None
                if self._j.core._db_fakeredis:
                    raise RuntimeError("should have been real redis by now")
                # raise RuntimeError("make sure you run local core redis, can use ")
            data = self._j.core.db.hget("jumpscale:configs",self.executor.id)
            if data == None:
                #means there is no config yet, need to put
                with open(os.path.join(self._j.core.dir_jumpscale_core, "Jumpscale", "core", "jumpscale.toml"), 'rb') as ff:
                    conf = ff.read().decode()
                conf = conf.replace("{{HOME}}", self._dir_home)
                self._config = pytoml.loads(conf)
                self.configSave()
            else:
                self._config = pytoml.loads(data)
        else:
            self._config = self._j.core.config

        self._state={}

    @property
    def _dir_home(self):
        env = self.executor.env
        if "HOMEDIR" in env:
            return os.environ["HOMEDIR"]
        elif "HOME" in env:
            return os.environ["HOME"]
        else:
            return "/root"
        return self._dir_home

    @property
    def config(self):
        return self._config

    @property
    def cfgPath(self):
        return self._config["dirs"]["CFGDIR"]

    @property
    def versions(self):
        versions = {}
        for name, path in self.configGet('plugins', {}).items():
            repo = self._j.clients.git.get(path)
            _, versions[name] = repo.getBranchOrTag()
        return versions


    def stateSet(self, key,val={}, save=False):
        """

        Set a section in Jumpscale's

        :param key: section name
        :type key: str
        :param val: value to set
        :type val: dict
        :return: true if new value is set, false if already exists
        :rtype: bool
        """
        if not isinstance(val, dict):
            raise RuntimeError("state set input needs to be dict")
        if self.executor is None or self.executor.id == "localhost":
            val = pytoml.dumps(val)
            self._j.core.db.hset("jumpscale:state:local",key,val)
        else:
            self._state[key]= val
            if save:
                self.stateSave()

    def stateSave(self):
        if self.executor is None or self.executor.id == "localhost":
            path = "%s/opt/cfg/state.toml"%self.executor.dir_paths["HOMEDIR"]
            self.executor.file_write(path,pytoml.dumps(self.state._state))

    def stateGet(self, key, defval={}, set=False):
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
        if not isinstance(defval, dict):
            raise RuntimeError("defval needs to be dict")
        if self.executor is None or self.executor.id == "localhost":
            res = self._j.core.db.hget("jumpscale:state:local", key)
            if res==None and defval is not {}:
                res = defval
                if set:
                    self.stateSet(key,defval,True)
            elif res == None:
                res={}
            else:
                res = pytoml.loads(res)
            return res
        else:
            if not key in self._state:
                if set:
                    self._state[key] = defval
                    self.stateSave()
                else:
                    return defval
            return self._state[key]


    def stateExists(self, key):
        """ checks if a section in jumpscale.toml exists

        :param key: section name
        :type key: str
        :return: true if the section exists
        :rtype: bool
        """
        if self.executor is None or self.executor.id == "localhost":
            return not self._j.core.db.hget(self._stateHKey, key) == None
        else:
            return key in self._state


    def configExists(self, key):
        """ checks if a section in jumpscale.toml exists

        :param key: section name
        :type key: str
        :return: true if the section exists
        :rtype: bool
        """
        return key in self._config

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
            set=set)

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
            save=save)

    @property
    def mascot(self):
        return mascot

    def _get(self, key, defval=None, set=False):
        """
        """
        if key in self._config:
            return self._config[key]
        else:
            if defval is not None:
                if set:
                    self._set(key, defval)
                return defval
            else:
                raise self._j.exceptions.Input(
                    message="could not find config key:%s in executor:%s" % (key, self))

    def _set(self, key, val, save=True):
        """
        @return True if changed
        """
        if key in self._config:
            val2 = self._config[key]
        else:
            val2 = None
        if val != val2:
            self._config[key] = val
            self._config_changed = True
            if save:
                self.configSave()
            return True
        else:
            if save:
                self.configSave()
            return False

    def configSetInDict(self, key, dkey, dval):
        """Set a value to a key in a section in the self._config file
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
            dval=dval)

    def _setInDict(self, key, dkey, dval):
        """
        will check that the val is a dict, if not set it and put key & val in
        """
        if key in self._config:
            val2 = self._config[key]
        else:
            self._set(key, {}, save=True)
            val2 = {}
        if dkey in val2:
            if val2[dkey] != dval:
               self._config_changed = True
        else:
           self._config_changed = True
        val2[dkey] = dval
        self._config[key] = val2
        # print("config set dict %s:%s:%s" % (key, dkey, dval))
        self.configSave()

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
            default=default)


    def _getFromDict(self, key, dkey, default=None):
        """
        get val from subdict
        """

        if key not in self._config:
            self._set(key, val={}, save=True)

        if dkey not in self._config[key]:
            if default is not None:
                return default
            raise RuntimeError(
                "Cannot find dkey:%s in state config for dict '%s'" %
                (dkey, key))

        return self._config[key][dkey]

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
            default=default)

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
            default=default)

    def _getFromDictBool(self, key, dkey, default=None):
        if key not in self._config:
            self._set(key, val={}, save=True)

        if dkey not in self._config[key]:
            if default is not None:
                return default
            raise RuntimeError(
                "Cannot find dkey:%s in state config for dict '%s'" %
                (dkey, key))

        val = self._config[key][dkey]
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
            dval=dval)

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
            dval=dval)

    def _setInDictBool(self, key, dkey, dval):
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
        return self._setInDict(key, dkey, dval)

    def configUpdate(self, ddict, overwrite=True):
        """
        will walk over 2 levels deep of the passed dict(dict of dict) & update it with the newely sent parameters
        and overwrite the values of old parameters only if overwrite is set to True

        keyword arguments:
        ddict -- 2 level dict(dict of dict)
        overwrite -- set to true if you want to overwrite values of old keys
        """
        for key0, val0 in ddict.items():
            if not self._j.data.types.dict.check(val0):
                raise RuntimeError(
                    "Value of first level key has to be another dict.")

            if key0 not in self._config:
                self._configSet(key0, val0, save=False)
            else:
                for key1, val1 in val0.items():
                    if key1 not in self._config[key0]:
                        self._config[key0][key1] = val1
                        self._config_changed = True
                    else:
                        if overwrite:
                            self._config[key0][key1] = val1
                            self._config_changed = True
        self.configSave()



    def configSave(self):
        """
        Writes config to specified path
        """
        if self.readonly:
            raise self._j.exceptions.Input(
                message="cannot write config to '%s', because is readonly" %
                self)

        if self.executor==None:
            path = self._j.core.jsconfig_path
            dpath = os.path.dirname(path)
            if not os.path.exists(dpath):
                os.makedirs(dpath)
            file = open(path, "w")
            data = pytoml.dumps(self.config)
            file.write(data)
            file.close()
        else:
            self._j.core.db.hset("jumpscale:configs",self.executor.id,pytoml.dumps(self.config))

    @property
    def config_js(self):
        return self.config

    @property
    def config_my(self):
        return self.config["myself.config"]

    @property
    def config_system(self):
        return self.config["system"]


    def __repr__(self):
        return str(self.config)

    def __str__(self):
        return str(self.config)
