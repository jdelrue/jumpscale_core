import os
import copy
from .JSBaseClassConfig import JSBaseClassConfig
from .JSBaseClassConfigs import JSBaseClassConfigs
import sys


installmessage = """

**ERROR**: there is no config directory created

create a git repository on github or any other git system.
checkout this repository by doing

'js_code get --url='...your ssh git url ...'

the go to this directory (to to that path & do)

js_config init


"""


class ConfigFactory(object):

    __jslocation__ = "j.tools.configmanager"

    def __init__(self):
        self._path = ""
        self.interactive = True  # std needs to be on True
        self.sandbox = False
        self._keyname = ""  # if set will overrule from the main js config file
        self._init = False

        self.Config = self._jsbase("Config",
            ['Jumpscale.tools.configmanager.Config.Config'])

    def reset(self, location=None, instance=None, force=False):
        """
        Reset configurations

        @param force: If no location is given and force is set
                to true then all locations will be reset
        """
        path = self._path
        if location:
            path = self.j.sal.fs.joinPaths(path, location)
        if instance:
            path = self.j.sal.fs.joinPaths(path, '%s.toml' % instance)
        if not location:
            if force or self.j.tools.console.askYesNo(
                "No location specified, Are you sure you want to " + \
                        "delete all configs?",
                    default=True):
                configs = self.j.sal.fs.listDirsInDir(path) if path else []
                for config in configs:
                    if not self.j.sal.fs.getBaseName(config).startswith('.'):
                        self.j.sal.fs.removeDirTree(config)
        else:
            self.j.sal.fs.remove(path)

    @property
    def path(self):
        if not self._path:
            self._path = self.j.core.state.configGetFromDict("myconfig", "path")
            if not self._path:
                self.init()
        return self._path

    @property
    def keyname(self):
        if not self._keyname:
            self._keyname = self.j.core.state.configGetFromDict(
                "myconfig", "sshkeyname")
        return self._keyname

    def sandbox_check(self, path="", die=False):
        if self._init and path == "" and die == False:
            return self.sandbox
        if not path:
            path = self.j.sal.fs.getcwd()

        cpath = self.j.sal.fs.pathNormalize(path + "/secureconfig")
        kpath = self.j.sal.fs.pathNormalize(path + "/keys")

        if self.j.sal.fs.exists(cpath):
            self.logger.debug("found sandbox config:%s" % cpath)
            self.j.tools.configmanager._path = cpath
            self.sandbox = True
        if self.j.sal.fs.exists(kpath):
            self.logger.debug("found sandbox sshkeys:%s" % kpath)
            items = self.j.sal.fs.listFilesInDir(kpath, filter="*.pub")
            if len(items) != 1:
                raise RuntimeError("should only find 1 key, found:%s" % items)
            sshkeyname = self.j.sal.fs.getBaseName(items[0][:-4])
            kpath_full = self.j.sal.fs.pathNormalize(path + "/keys/%s" % sshkeyname)
            self.j.tools.configmanager._keyname = sshkeyname
            self._init = True
            self.sandbox = True
            return self.j.clients.sshkey.key_load(path=kpath_full)

        if die:
            raise RuntimeError("did not find sandbox on this path:%s" % path)
        self._init = True
        return self.sandbox

    def sandbox_init(
            self,
            path="",
            systemssh=False,
            passphrase="",
            reset=False,
            sshkeyname=""):
        """
        Will use specified dir as sandbox for config management 
        (will not use system config dir)

        looks for $path/secureconfig & $path/sshkeys (if systemssh == False)
        if not found will create

        Keyword Arguments:
            systemssh {Bool} -- if True will use the configured sshkey 
                                on system (default: {False})
            reset {Bool} -- will replace current config (default: {False})
            sshkeyname -- if empty will be dirname of current path

        Returns:
            SSHKey
        """

        if path:
            self.j.sal.fs.changeDir(path)

        # just to make sure all stays relative (we don't want to store full
        # paths)
        path = ""
        if not sshkeyname:
            sshkeyname = self.j.sal.fs.getBaseName(j.sal.fs.getcwd())

        cpath = "secureconfig"
        self.j.sal.fs.createDir(cpath)

        if not systemssh:
            kpath_full = "keys/%s" % sshkeyname
            kpath_full0 = self.j.sal.fs.pathNormalize(kpath_full)
            if not self.j.sal.fs.exists("keys"):
                self.j.sal.fs.createDir("keys")
                self.j.clients.sshkey.key_generate(
                    path=kpath_full0,
                    passphrase=passphrase,
                    load=True,
                    returnObj=False)
            self.j.tools.configmanager._keyname = sshkeyname

        self.j.tools.configmanager._path = self.j.sal.fs.pathNormalize(cpath)

        data = {}
        data["path"] = kpath_full
        data["passphrase_"] = passphrase

        sshkeyobj = self.j.clients.sshkey.get(
            instance=sshkeyname, data=data, interactive=False)

        self.sandbox = True

        # SHOULD NOT CONFIGURE THE HOST CONFIGMMANAGER, SHOULD BE ALREADY DONE
        #j.tools.configmanager.init(configpath=cpath, keypath=kpath_full,
        #               silent=False)

        return sshkeyobj

    def _findConfigRepo(self, die=False):
        """
        if path is not set, it will look under CODEDIRS for 
        any pre-configured js_config repo
        if there are more than one, will try to use one in 
        root of cwd. If not in one, will raise a RuntimeError

        return configpath,remoteGitUrl
        """
        # self.sandbox_check()
        path = self.j.sal.fs.getParentWithDirname(dirname=".jsconfig", die=die)
        if path is not None:
            return path, None
        paths = []
        for key, path in self.j.clients.git.getGitReposListLocal().items():
            if self.j.sal.fs.exists(self.j.sal.fs.joinPaths(path, ".jsconfig")):
                paths.append(path)
        if len(paths) == 0:
            if die:
                raise RuntimeError("could not find config paths")
            else:
                return None, None
        if len(paths) > 1:
            if die:
                raise RuntimeError(
                    "multipule configuration repos were found in {} " + \
                            "but not currently in root of one".format(paths))
            else:
                return None, None
        cpath = paths[0]
        g = self.j.clients.git.get(cpath)
        self.logger.info("found jsconfig dir in: %s" % cpath)
        self.logger.info("remote url: %s" % g.remoteUrl)

        return cpath, g.remoteUrl


    @property
    def base_class_config(self):
        return JSBaseClassConfig

    @property
    def base_class_configs(self):
        return JSBaseClassConfigs

    def configure(
            self,
            location="",
            instance="main",
            data={},
            interactive=True):
        """
        Will display a npyscreen form to edit the configuration
        @param location: jslocation of module to configure for 
                         (eg: self.j.clients.openvcloud)
        @param: instance: configuration instance
        """
        self.sandbox_check()
        if not data:
            interactive = True
        jumpscaleobj = self.js_obj_get(
            location=location, instance=instance, data=data)
        if interactive:
            jumpscaleobj.configure()
        jumpscaleobj.config.save()
        return jumpscaleobj

    def update(self, location, instance="main", updatedict={}):
        """
        update the configuration by giving a dictionnary. 
        The configuration will be updated with the value of updatedict
        """
        self.sandbox_check()
        jumpscaleobj = self.js_obj_get(location=location, instance=instance)
        sc = jumpscaleobj.config
        sc.data = updatedict
        sc.save()
        return sc

    def _get_for_obj(self, jsobj, template, ui=None, instance="main", data={}):
        """
        return a secret config
        """
        self.sandbox_check()
        if not hasattr(jsobj, '__jslocation__') or \
                jsobj.__jslocation__ is None or jsobj.__jslocation__ is "":
            raise RuntimeError(
                "__jslocation__ has not been set on class %s" %
                jsobj.__class__)
        location = jsobj.__jslocation__
        key = "%s_%s" % (location, instance)

        if ui is not None:
            jsobj.ui = ui
        sc = self.Config( instance=instance,
            location=location,
            template=template,
            data=data)

        return sc

    def js_obj_get(self, location="", instance="main", data={}):
        """
        will look for jumpscale module on defined location & return this object
        and generate the object which has a .config on the object
        """
        self.sandbox_check()
        if not location:
            if self.j.sal.fs.getcwd().startswith(self.path):
                # means we are in subdir of current config  repo, so we can be
                # in location
                location = self.j.sal.fs.getBaseName(j.sal.fs.getcwd())
                if not location.startswith("j."):
                    raise RuntimeError(
                        "Cannot find location, are you in right " + \
                                "directory? now in:%s" %
                        self.j.sal.fs.getcwd())
            else:
                raise RuntimeError(
                    "location has not been specified, looks " + \
                            "like we are not in config directory:'%s'" %
                    self.path)

        obj = self.jget(location)
        # If the client is a single item one (i.e itsyouonline), we will always
        # use the default `main` instance
        if obj._single_item:
            instance = "main"
        if not hasattr(obj, 'get'):
            return obj
        obj = obj.get(instance=instance, data=data)
        return obj

    def get(self, location, instance="main"):
        """
        return a secret config, it needs to exist, otherwise it will die
        """
        self.sandbox_check()
        if location == "":
            raise RuntimeError("location cannot be empty")
        if instance == "" or instance is None:
            raise RuntimeError("instance cannot be empty")
        key = "%s_%s" % (location, instance)
        sc = self.Config(instance=instance, location=location)
        return sc

    # should use config_update
    # def set(self, location, instance, config=None):
    #     """
    #     create a new config

    #     @param location: location of the client
    #     @param instance: instance name
    #     @param config: optional configuration to set.
    #     @type config: dict
    #     """
    #     # create the config directory and file, so we don't trigger the form
    #     # when creating a SercretConfig object
    #     path = self.j.sal.fs.joinPaths(j.tools.configmanager.path, 
    #                               location, instance + '.toml')
    #     self.j.sal.fs.createDir(j.sal.fs.getParent(path))
    #     self.j.sal.fs.writeFile(path, "")

    #     jsclient_object = eval(location)

    #     sc = Config(instance=instance, jsclient_object=jsclient_object)
    #     if config is not None:
    #         sc.data = config
    #     sc.save()
    #     return sc

    def list(self, location="j.tools.myconfig"):
        """
        list all the existing instance name for a location

        if empty then will list (($location,$name),)

        @return: list of instance name
        """
        self.sandbox_check()
        instances = []

        if not location:
            res = []
            for location in self.j.sal.fs.listDirsInDir(
                    self.path, recursive=False, dirNameOnly=True):
                if ".git" in location:
                    continue
                for instance in self.list(location):
                    res.append((location, instance))
            return res

        root = self.j.sal.fs.joinPaths(self.path, location)
        if not self.j.sal.fs.exists(root):
            return instances

        # jsclient_object = eval(location)

        for cfg_path in self.j.sal.fs.listFilesInDir(root):
            cfg_name = self.j.sal.fs.getBaseName(cfg_path)
            if cfg_name in ('.git', '.jsconfig'):
                continue
            # trim the extension
            instance_name, _ = os.path.splitext(cfg_name)
            instances.append(instance_name)
        return instances

    def delete(self, location, instance="*"):
        self.sandbox_check()
        if instance != "*":
            path = self.j.sal.fs.joinPaths(
                self.j.tools.configmanager.path,
                location,
                instance + '.toml')
            if self.j.sal.fs.exists(path):
                self.j.sal.fs.remove(path)
        else:
            path = self.j.sal.fs.joinPaths(j.tools.configmanager.path, location)
            if self.j.sal.fs.exists(path):
                for item in self.j.sal.fs.listFilesInDir(path):
                    self.j.sal.fs.remove(item)

    def init(self, data={}, silent=False, configpath="", keypath=""):
        """
        @param data is data for myconfig
        @param configpath is the path towards the config directory can be
                git based or local
        @param keypath is the path towards the ssh key which will be used 
                to use the config manager

        """
        def msg(msg):
            self.logger.info("Jumpscale init: %s" % msg)

        def die(msg):
            self.logger.error("ERROR: CANNOT INIT jumpscale")
            self.logger.error("ERROR: %s" % msg)
            self.logger.error(
                "make sure you did the upgrade procedure: " + \
                "'cd  ~/code/github/threefoldtech/jumpscale_core/;python3 " + \
                "upgrade.py'")
            sys.exit(1)

        def ssh_init(ssh_silent=False):
            self.logger.debug("ssh init (no keypath specified)")

            keys = self.j.clients.sshkey.list()  # LOADS FROM AGENT NOT FROM CONFIG
            keys0 = [self.j.sal.fs.getBaseName(item) for item in keys]

            if not keys:
                # if no keys try to load a key from home directory/.ssh and
                # re-run the method again
                self.logger.info("found 0 keys from ssh-agent")
                keys = self.j.sal.fs.listFilesInDir(
                    "%s/.ssh" %
                    self.j.dirs.HOMEDIR,
                    exclude=[
                        "*.pub",
                        "*authorized_keys*",
                        "*known_hosts*"])
                if not keys:
                    raise RuntimeError(
                        "Cannot find keys, please load right ssh " + \
                                "keys in agent, now 0")
                elif len(keys) > 1:
                    if silent:
                        raise RuntimeError(
                            "cannot run silent if more than 1 sshkey " + \
                                    "exists in your ~/.ssh directory, "
                            "please either load your key into your " + \
                                    "ssh-agent or "
                            "make sure you have only one key in ~/.ssh")
                    msg("found ssh keys in your ~/.ssh directory, " + \
                            "do you want to load one is ssh-agent?")
                    key_chosen = self.j.tools.console.askChoice(keys)
                    self.j.clients.sshkey.key_load(path=key_chosen)
                else:
                    self.j.clients.sshkey.key_load(path=keys[0])
                return ssh_init()

            elif len(keys) > 1:
                # if loaded keys are more than one, ask user to select one or
                # raise error if in silent mode
                if ssh_silent:
                    raise RuntimeError(
                        "cannot run silent if more than 1 sshkey loaded")
                # more than 1 key
                msg("Found more than 1 ssh key loaded in ssh-agent, "
                    "please specify which one you want to use to store " + \
                            "your secure config.")
                key_chosen = self.j.tools.console.askChoice(keys0)
                self.j.core.state.configSetInDict(
                    "myconfig", "sshkeyname", key_chosen)

            else:
                # 1 key found
                msg("ssh key found in agent is:'%s'" % keys[0])
                if not silent:
                    msg("Is it ok to use this one:'%s'?" % keys[0])
                    if not self.j.tools.console.askYesNo():
                        die("cannot continue, please load other sshkey " + \
                                "in your agent you want to use")
                self.j.core.state.configSetInDict(
                    "myconfig", "sshkeyname", keys0[0])

        if self.sandbox_check():
            return

        if data != {}:
            self.logger.debug(
                "init: silent:%s path:%s withdata:\n" %
                (silent, configpath))
        else:
            self.logger.debug(
                "init: silent:%s path:%s nodata\n" %
                (silent, configpath))

        if silent:
            self.interactive = False

        if configpath and not self.sandbox:
            self._path = configpath
            self.j.sal.fs.createDir(configpath)
            self.j.sal.fs.touch("%s/.jsconfig" % configpath)
            self.j.core.state.configSetInDict("myconfig", "path", configpath)

        cpath = configpath

        if keypath:
            self._keyname = self.j.sal.fs.getBaseName(keypath)
            self.j.core.state.configSetInDict(
                "myconfig", "sshkeyname", self.keyname)
            self.j.clients.sshkey.key_get(keypath, load=True)
        else:
            ssh_init(ssh_silent=silent)

        cfg = self.j.core.state.config_js
        if "myconfig" not in cfg:
            die("could not find myconfig in the main configuration " + \
                    "file, prob need to upgrade")

        if not cpath and not cfg["myconfig"].get("path", None):
            # means config directory not configured
            cpath, giturl = self._findConfigRepo(die=False)

            if silent:
                if not cpath:
                    msg("did not find config dir in code dirs, " + \
                            "will create one in js_shell cfg dir")
                    cpath = '%s/myconfig/' % self.j.dirs.CFGDIR
                    self.j.sal.fs.createDir(cpath)
                    msg("Config dir in: '%s'" % cpath)
                self.j.core.state.configSetInDict("myconfig", "path", cpath)
                if not giturl:
                    self.j.core.state.configSetInDict("myconfig", "giturl", giturl)
            else:

                if cpath:
                    msg("Found a config repo on: '%s', do you want "
                            "to use this one?" % cpath)
                    if not self.j.tools.console.askYesNo():
                        giturl = None
                        cpath = ""
                    else:
                        if giturl:
                            self.j.clients.git.pullGitRepo(
                                url=giturl, interactive=True, ssh=True)

                if not cpath:
                    msg("Do you want to use a git based CONFIG dir, y/n?")
                    if self.j.tools.console.askYesNo():
                        msg("Specify a url like: " + \
                "'ssh://git@docs.grid.tf:7022/despiegk/config_despiegk.git'")
                        giturl = self.j.tools.console.askString("url")
                        cpath = self.j.clients.git.pullGitRepo(
                            url=giturl, interactive=True, ssh=True)

                if not cpath:
                    msg(
                        "will create config dir in '%s/myconfig/', "
                                "your config will not be centralised! "
                                "Is this ok?" % self.j.dirs.CFGDIR)
                    if self.j.tools.console.askYesNo():
                        cpath = '%s/myconfig/' % self.j.dirs.CFGDIR
                        self.j.sal.fs.createDir(cpath)

                if cpath:
                    self.j.core.state.configSetInDict("myconfig", "path", cpath)
                else:
                    die("ERROR: please restart config procedure, " + \
                            "use git based config or need to store locally.")
                if giturl:
                    self.j.core.state.configSetInDict("myconfig", "giturl", giturl)

                self.j.core.state.configSave()

        data = data or {}
        if data:
            from Jumpscale.tools.myconfig.MyConfig import MyConfig as MyConfig
            self.j.tools._myconfig = MyConfig(data=data)

        if self.j.tools.myconfig.config.data["email"] == "":
            if not silent:
                self.j.tools.myconfig.configure()
                self.j.tools.myconfig.config.save()

    def __str__(self):
        self.sandbox_check()
        sshagent = self.j.clients.sshkey.sshagent_available()
        keyloaded = self.keyname in self.j.clients.sshkey.listnames()
        C = """

        configmanager:

        - path: {path}
        - keyname: {keyname}
        - is sandbox: {sandbox}
        - sshagent loaded: {sshagent}
        - key in sshagent: {keyloaded}

        """.format(**{"path": self.path,
                      "sshagent": sshagent,
                      "keyloaded": keyloaded,
                      "keyname": self.keyname,
                      "sandbox": self.sandbox_check()})
        C = self.j.data.text.strip(C)

        return C

    __repr__ = __str__

    def check(self):
        """
        js_shell 'j.tools.configmanager.check()'
        """
        # print(self)
        self.j.data.nacl.default.agent
        print(self)

    def test(self):
        """
        js_shell 'j.tools.configmanager.test()'
        """

        def testinit():

            tdir = "/tmp/tests/secretconfig"
            # self.j.sal.process.execute("cd %s && git init" % tdir)

            MYCONFIG = """
            fullname = "kristof@something"
            email = "kkk@kk.com"
            login_name = "dddd"
            """
            data = self.j.data.serializers.toml.loads(MYCONFIG)

            self.init(configpath=tdir, data=data, silent=True)

            assert self.j.tools.myconfig.config.data == data

            return data

        data = testinit()
        self._test_myconfig_singleitem(data)
        testinit()
        self._test_myconfig_multiitem()

        # self.j.sal.fs.remove(tdir)

    def _test_myconfig_singleitem(self, data):

        tdir = "/tmp/tests/secretconfig/j.tools.myconfig"
        # there should be 1 file
        assert len(j.sal.fs.listFilesInDir(tdir)) == 1

        # check that the saved data is ok
        assert self.j.data.serializers.toml.fancydumps(
            self.j.tools.myconfig.config.data) == \
                    self.j.data.serializers.toml.fancydumps(data)

        self.delete("j.tools.myconfig")  # should remove all
        assert len(j.sal.fs.listFilesInDir(tdir)) == 0

        # self.j.tools.configmanager.reset()
        self.j.tools.myconfig.reset()  # will remove data from mem
        assert self.j.tools.myconfig.config._data == {
            'email': '', 'fullname': '', 'login_name': ''}
        assert self.j.tools.myconfig.config.data == {
            'email': '', 'fullname': '', 'login_name': ''}

        self.j.tools.myconfig.config.load()
        assert self.j.tools.myconfig.config.data == {
            'email': '', 'fullname': '', 'login_name': ''}
        self.j.tools.myconfig.config.data = data
        self.j.tools.myconfig.config.save()
        assert len(j.sal.fs.listFilesInDir(tdir)) == 1

        # clean the env
        # self.j.tools.configmanager.reset()
        self.j.tools.myconfig.reset()
        self.j.tools.myconfig.config._data = {}
        assert self.j.data.serializers.toml.fancydumps(
            self.j.tools.myconfig.config.data) ==  \
                    self.j.data.serializers.toml.fancydumps(data)

        # clean the env
        # self.j.tools.configmanager.reset()
        self.j.tools.myconfig.config.load()
        self.j.tools.myconfig.config.data = {"email": "someting@ree.com"}
        self.j.tools.myconfig.config.save()
        # self.j.tools.configmanager.reset()

        assert self.j.tools.myconfig.config.data["email"] == "someting@ree.com"

        # delete
        self.delete("j.tools.myconfig", "main")
        assert len(j.sal.fs.listFilesInDir(tdir)) == 0

    def _test_myconfig_multiitem(self):

        MYCONFIG = """
        name = ""
        addr = "192.168.1.1"
        port = 22
        clienttype = "ovh"
        active = true
        selected = true
        category = "me"
        description = "some descr"
        secretconfig_ = "my secret config"
        """
        data = self.j.data.serializers.toml.loads(MYCONFIG)

        for i in range(10):
            data["addr"] = "192.168.1.%s" % i
            data["name"] = "test%s" % i
            obj = self.j.tools.nodemgr.get("test%s" % i, data=data)

        # empty mem
        # self.j.tools.configmanager.reset()
        self.j.tools.nodemgr.items = {}

        obj = self.j.tools.nodemgr.get("test5")
        assert obj.config._data["addr"] == "192.168.1.5"
        assert obj.config.data["addr"] == "192.168.1.5"
        # needs to be encrypted
        assert obj.config._data["secretconfig_"] != "my secret config"
        assert obj.config.data["secretconfig_"] == "my secret config"

        tdir = "/tmp/tests/secretconfig/j.tools.nodemgr"
        assert len(j.sal.fs.listFilesInDir(tdir)) == 10

        obj.config.data = {"secretconfig_": "test1"}
        assert obj.config.data["secretconfig_"] == "test1"

        i = self.j.tools.nodemgr.get("test1")
        assert i.name == "test1"

        # self.j.tools.nodemgr.reset()
        # assert len(j.sal.fs.listFilesInDir(tdir)) == 0
