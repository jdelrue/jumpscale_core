try:
    import ujson as json
except ImportError:
    import json

import pytoml
import pystache
import hashlib
import base64
import os


class ExecutorBase(object):

    def __init__(self, debug=False, checkok=True):
        self.debug = debug
        self.checkok = checkok
        self.type = None
        self._id = None
        self._isBuildEnv = None
        self.readonly = False
        self.state_disabled = False
        self.CURDIR = ""
        self._logger = None
        self.reset()
        self._dirpaths_init = False

    def reset(self):
        self._iscontainer = None
        self._state = None
        self._stateOnSystem = None
        self._prefab = None

    @property
    def state(self):
        if self._state is None:
            from ...core.State import State
            DState = self._jsbase("State", [State])
            self._state = DState(executor=self)
            self._state.load()
        return self._state

    @property
    def logger(self):
        if self._logger is None:
            self._logger = self.j.logging.get("executor")
        return self._logger

    @property
    def id(self):
        if self._id is None:
            raise RuntimeError("self._id cannot be None")
        return self._id

    @property
    def env(self):
        return self.stateOnSystem["env"]

    def _docheckok(self, cmd, out):
        out = out.rstrip("\n")
        lastline = out.split("\n")[-1]
        if lastline.find("**OK**") == -1:
            raise RuntimeError("Error in:\n%s\n***\n%s" % (cmd, out))
        out = "\n".join(out.split("\n")[:-1]).rstrip() + "\n"
        return out

    def commands_transform(
            self,
            cmds,
            die=True,
            checkok=False,
            env={},
            sudo=False,
            shell=False):
        # print ("TRANSF:%s"%cmds)

        if sudo or shell:
            checkok = False

        multicommand = "\n" in cmds or ";" in cmds

        if shell:
            if "\n" in cmds:
                raise RuntimeError("cannot do shell for multiline scripts")
            else:
                cmds = "bash -c '%s'" % cmds

        pre = ""

        checkok = checkok or self.checkok

        if die:
            # first make sure not already one
            if "set -e" not in cmds:
                # now only do if multicommands
                if multicommand:
                    if self.debug:
                        pre += "set -ex\n"
                    else:
                        pre += "set -e\n"

        if self.CURDIR != "":
            pre += "cd %s\n" % (self.CURDIR)

        if env != {}:
            for key, val in env.items():
                pre += "export %s=%s\n" % (key, val)

        cmds = "%s\n%s" % (pre, cmds)

        if checkok and multicommand:
            if not cmds.endswith('\n'):
                cmds += '\n'
            cmds += "echo '**OK**'"

        if "\n" in cmds:
            cmds = cmds.replace("\n", ";")
            cmds.strip() + "\n"

        cmds = cmds.replace(";;", ";").strip(";")

        if sudo:
            cmds = self.sudo_cmd(cmds)

        self.logger.debug(cmds)

        return cmds

    @property
    def prefab(self):
        if self._prefab is None:
            if not getattr(self.j.tools, "prefab", None):
                # XXX TEMPORARY INCREDIBLY BAD HACK, see issue #50
                from JumpscalePrefab.PrefabFactory \
                    import PrefabRootClassFactory \
                    as _PrefabRootClassFactory
                self.j.tools.prefab = _PrefabRootClassFactory()

            self._prefab = self.j.tools.prefab.get(self)
        return self._prefab

    def exists(self, path):
        raise NotImplemented()

    def configSave(self):
        """
        Config Save
        """
        if self.type == "local":
            self.j.core.state = self._state
        self.state.configSave()

    # interface to implement by child classes
    def execute(
            self,
            cmds,
            die=True,
            checkok=None,
            showout=True,
            timeout=0,
            env={},
            sudo=False):
        raise NotImplementedError()

    def executeRaw(self, cmd, die=True, showout=False):
        raise NotImplementedError()

    @property
    def isDebug(self):
        return self.state.configGetFromDict(
            "system", "debug") == "1" or self.state.configGetFromDict(
            "system", "debug") == 1 or self.state.configGetFromDict(
            "system", "debug") or self.state.configGetFromDict(
            "system", "debug") == "true"

    @property
    def isContainer(self):
        """
        means we don't work with ssh-agent ...
        """
        return self.stateOnSystem["iscontainer"]

    @property
    def isBuildEnv(self):
        """
        means we are building python and we are in the build-dir
        """
        if self._isBuildEnv == None:
            #env arg is set by the env.sh script in the build dir
            self._isBuildEnv = "PBASE" in os.environ
        return self._isBuildEnv


    @property
    def stateOnSystem(self):
        """
        is dict of all relevant param's on system
        """

        def do():

            self.logger.debug("stateonsystem for non local:%s" % self)
            C = """
set +ex
ls "/root/.iscontainer"  > /dev/null 2>&1 && \
            echo 'ISCONTAINER = 1' || echo 'ISCONTAINER = 0'
echo UNAME = \""$(uname -mnprs)"\"

if [ "$(uname)" == "Darwin" ]; then
    export PATH_JSCFG="$HOME/jumpscale/cfg"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    export PATH_JSCFG="$HOME/jumpscale/cfg"
else
    die "platform not supported"
fi
echo PATH_JSCFG = \"$PATH_JSCFG\"

echo "PATH_HOME = $HOME"
echo HOSTNAME = "$(hostname)"

lsmod > /dev/null 2>&1|grep vboxdrv |grep -v grep  > \
            /dev/null 2>&1 && echo 'VBOXDRV=1' || echo 'VBOXDRV=0'

#OS
apt-get -v > /dev/null 2>&1 && echo 'OS_TYPE="ubuntu"'
test -f /etc/arch-release > /dev/null 2>&1 && echo 'OS_TYPE="arch"'
test -f /etc/redhat-release > /dev/null 2>&1 && echo 'OS_TYPE="redhat"'
apk -v > /dev/null 2>&1 && echo 'OS_TYPE="alpine"'
brew -v > /dev/null 2>&1 && echo 'OS_TYPE="darwin"'
opkg -v > /dev/null 2>&1 && echo 'OS_TYPE="LEDE"'
cat /etc/os-release | grep "VERSION_ID"

echo "CFG_JUMPSCALE = --TEXT--"
cat $PATH_JSCFG/jumpscale.toml 2>/dev/null || echo ""
echo --TEXT--

echo "CFG_STATE = --TEXT--"
cat $PATH_JSCFG/state.toml 2> /dev/null || echo ""
echo --TEXT--

echo "BASHPROFILE = --TEXT--"
cat $HOME/.profile_js 2>/dev/null || echo ""
echo --TEXT--

echo "ENV = --TEXT--"
export
echo --TEXT--
            """
            C = self.j.data.text.strip(C)
            rc, out, err = self.execute(C, showout=False, sudo=False)
            res = {}
            state = ""
            for line in out.split("\n"):
                if line.find("--TEXT--") != -1 and line.find("=") != -1:
                    varname = line.split("=")[0].strip().lower()
                    state = "TEXT"
                    txt = ""
                    continue

                if state == "TEXT":
                    if line.strip() == "--TEXT--":
                        res[varname] = txt
                        state = ""
                        continue
                    else:
                        txt += line + "\n"
                        continue

                if "=" in line:
                    varname, val = line.split("=", 1)
                    varname = varname.strip().lower()
                    val = str(val).strip().strip("\"")
                    if val.lower() in ["1", "true"]:
                        val = True
                    elif val.lower() in ["0", "false"]:
                        val = False
                    else:
                        try:
                            val = int(val)
                        except BaseException:
                            pass
                    res[varname] = val

            if res["cfg_jumpscale"].strip() != "":
                try:
                    res["cfg_jumpscale"] = pytoml.loads(res["cfg_jumpscale"])
                except Exception as e:
                    raise RuntimeError(
                        "Could not load jumpscale config file "
                        "(pytoml error)\n%s\n" %
                        res["cfg_jumpscale"])
            else:
                res["cfg_jumpscale"] = {}
            if res["cfg_state"].strip() != "":
                try:
                    res["cfg_state"] = pytoml.loads(res["cfg_state"])
                except Exception as e:
                    raise RuntimeError(
                        "Could not load jumpscale config file "
                        "(pytoml error)\n%s\n" %
                        res["cfg_state"])

            else:
                res["cfg_state"] = {}

            envdict = {}
            for line in res["env"].split("\n"):
                line = line.replace("declare -x", "")
                line = line.strip()
                if line.strip() == "":
                    continue
                if "=" in line:
                    pname, pval = line.split("=", 1)
                    pval = pval.strip("'").strip("\"")
                    envdict[pname.strip()] = pval.strip()

            res["env"] = envdict
            return res


        if self._stateOnSystem is None:
            self._stateOnSystem = self.cache.get("stateOnSystem", do)
        return self._stateOnSystem

    def enableDebug(self):
        self.state.configSetInDictBool("system", "debug", True)
        self.state.configSave()
        self.cache.reset()

    def _getDirPathConfig(self):

        if self.isBuildEnv:
            T = "BASEDIR = \"%s\"\n"%os.environ["PBASE"]
            T += '''
            HOMEDIR = "{{TMPDIR}}"
            CODEDIR = "{{BASEDIR}}/code"
            HOSTDIR = "{{TMPDIR}}/host"
            HOSTCFGDIR = "{{TMPDIR}}/hostcfg"
            CFGDIR = "{{BASEDIR}}/cfg"
            VARDIR = "{{TMPDIR}}/var"
            '''
        elif self.isContainer:
            T = '''
            HOMEDIR = "~"
            BASEDIR = "/opt"
            CODEDIR = "/opt/code"
            HOSTDIR = "/host"
            HOSTCFGDIR = "/hostcfg"
            CFGDIR = "{{BASEDIR}}/cfg"
            VARDIR = "/var"
            '''

        elif self.platformtype.isMac:
            T = '''
            HOMEDIR = "~"
            BASEDIR = "{{HOMEDIR}}/opt/"
            CODEDIR = "{{HOMEDIR}}/code"
            HOSTDIR = "{{HOMEDIR}}/opt/"
            HOSTCFGDIR = "{{HOMEDIR}}/jumpscale/cfg/"
            CFGDIR = "{{HOSTCFGDIR}}"
            VARDIR = "{{BASEDIR}}/var"
            '''
        else:
            T = '''
            HOMEDIR = "~"
            BASEDIR = "/opt"
            CODEDIR = "/opt/code"
            HOSTDIR = "{{HOMEDIR}}/jumpscale/"
            HOSTCFGDIR = "{{HOMEDIR}}/jumpscale/cfg/"
            CFGDIR = "{{BASEDIR}}/cfg"
            VARDIR = "{{BASEDIR}}/var"
            '''

        BASE = '''        
        TMPDIR = "{{TMPDIRSYSTEM}}/jumpscale/"
        BASEDIRJS = "{{BASEDIR}}/jumpscale"
        JSAPPSDIR= "{{BASEDIRJS}}/apps"
        TEMPLATEDIR ="{{VARDIR}}/templates"
        DATADIR = "{{VARDIR}}/data"
        BUILDDIR = "{{VARDIR}}/build"
        LIBDIR = "{{BASEDIR}}/lib/"
        LOGDIR = "{{VARDIR}}/log"
        BINDIR="{{BASEDIR}}/bin"
        '''

        TXT = self.j.data.text.strip(BASE) + "\n" + self.j.data.text.strip(T)

        return self._replaceInToml(TXT)

    def _replaceInToml(self, T):
        T = T.replace("~", self.env["HOME"])
        # need to see if this works well on mac
        T = T.replace("{{TMPDIRSYSTEM}}", "/tmp")
        # will replace  variables in itself
        counter = 0
        while "{{" in T and counter < 10:
            TT = pytoml.loads(T)
            T = pystache.render(T, **TT)
            counter += 1
        TT = pytoml.loads(T)

        if counter > 9:
            raise RuntimeError(
                "cannot convert default configfile, "
                "template arguments still in")

        return T

    def initEnv(self):
        """
        init the environment of an executor
        """
        self.reset()
        T = self._getDirPathConfig()
        T = T.replace("//", "/")
        DIRPATHS = pytoml.loads(T)

        if not self.isBuildEnv:
            # get env dir arguments & overrule them in jumpscale config
            for key, val in self.env.items():
                if "DIR" in key and key in DIRPATHS:
                    DIRPATHS[key] = val

        TSYSTEM = '''

        [system]
        debug = false
        autopip = false
        readonly = false
        container = false

        [myconfig]
        #giturl = "ssh://git@docs.agitsystem.com:7022/myusername/myconfig.git"
        giturl = ""
        sshkeyname = "id_rsa"
        path = ""

        [logging]
        enabled = true
        filter = ["*"]
        exclude = ["sal.fs"]
        level =20

        '''

        TSYSTEM = self.j.data.text.strip(TSYSTEM)
        TT = pytoml.loads(TSYSTEM)

        TT["dirs"] = DIRPATHS

        # set up a default myconfig path.
        TT['myconfig']['path'] = TT['dirs']['CODEDIR'] + "/local/stdorg/config"

        # need to see if this works everywhere but think so
        TT["dirs"]["TMPDIR"] = "/tmp"

        TT["system"]["container"] = self.stateOnSystem["iscontainer"]

        if "plugins" not in TT.keys():
            TT["plugins"] = {}

        if not self.state_disabled:

            if self.isBuildEnv:
                for key, val in DIRPATHS.items():
                    j.sal.fs.createDir(val)
                githubpath="%s/github/threefoldtech"%DIRPATHS["CODEDIR"]

                #link code dir from host to build dir if it exists
                if not j.sal.fs.exists(githubpath):
                    sdir1 = "%s/code/github/threefoldtech"%os.environ["HOME"]
                    sdir2 = "/opt/code/github/threefoldtech"
                    if j.sal.fs.exists(sdir1):
                        sdir = sdir1
                    elif j.sal.fs.exists(sdir2):
                        sdir = sdir2
                    else:
                        sdir = None
                    if sdir is not None:
                        j.sal.fs.symlink(sdir, githubpath, overwriteTarget=True)

            else:
                out = ""
                for key, val in DIRPATHS.items():
                    out += "mkdir -p %s\n" % val
                self.execute(out, sudo=True,showout=False)

            if self.exists(
                "%s/github/threefoldtech/jumpscale_core/" %
                    DIRPATHS["CODEDIR"]):
                TT["plugins"]["Jumpscale"] = "%s/github/threefoldtech/jumpscale_core/Jumpscale/" % DIRPATHS["CODEDIR"]
                # only check if core exists
                if self.exists(
                    "%s/github/threefoldtech/jumpscale_lib/" %
                        DIRPATHS["CODEDIR"]):
                    TT["plugins"]["JumpscaleLib"] = "%s/github/threefoldtech/jumpscale_lib/JumpscaleLib/" % DIRPATHS["CODEDIR"]
                if self.exists(
                    "%s/github/threefoldtech/jumpscale_prefab/" %
                        DIRPATHS["CODEDIR"]):
                    TT["plugins"]["JumpscalePrefab"] = "%s/github/threefoldtech/jumpscale_prefab/JumpscalePrefab/" % DIRPATHS["CODEDIR"]
                if self.exists("%s/github/threefoldtech/digital_me/" % DIRPATHS["CODEDIR"]):
                    TT["plugins"]["DigitalMeLib"] = "%s/github/threefoldtech/digital_me/DigitalMeLib/" % DIRPATHS["CODEDIR"]
                if self.exists("%s/github/threefoldtech/0-robot/" % DIRPATHS["CODEDIR"]):
                    TT["plugins"]["JumpscaleZrobot"] = "%s/github/threefoldtech/0-robot/JumpscaleZrobot/" % DIRPATHS["CODEDIR"]

                if self.type == "local":
                    src = "%s/github/threefoldtech/jumpscale_core/cmds/" % DIRPATHS["CODEDIR"]
                    if self.isBuildEnv:
                        dest = DIRPATHS["BINDIR"]
                    else:
                        dest = "/usr/local/bin"
                    self.j.sal.fs.symlinkFilesInDir(src, dest,
                                                    delete=True,
                                                    includeDirs=False,
                                                    makeExecutable=True)

        if TT["system"]["container"] is True:
            self.state.configUpdate(TT, True)  # will overwrite
        else:
            self.state.configUpdate(TT, False)  # will not overwrite

        # XXX state occurs in two places, this code results in them
        # getting out-of-sync as j.core.state can be **DIFFERENT**
        # from j.tools.executorLocal.state, resulting in unpredictable
        # behaviour.  a property in j.core has been put in its place
        # which REFERENCES tools.executorLocal.state, which MAY
        # be over-ridden if desired
        #if self.type == "local":
        #    self.j.core.state = self.state

        self.cache.reset()
        #print (self.state._configJS)
        #print (self.state.configJSPath)

        self.logger.debug("initenv done on executor base")

    def env_check_init(self):
        """ check that system has been initialise, if not, do so
        """
        #print ("env_check_init", self._dirpaths_init)
        if self._dirpaths_init:
            return
        if not self.exists(self.state.configJSPath) or \
           not self.state.configExists('dirs') or \
           self.state.configGet('dirs', {}) == {}:
            self.initEnv()
        #print ("env_check_init", self.state.configJSPath)
        #print ("dirs exists", self.state.configExists('dirs'))
        self._dirpaths_init = True

    @property
    def dir_paths(self):
        self.env_check_init()
        return self.state.configGet('dirs')

    @property
    def platformtype(self):
        return self.j.core.platformtype.get(self)

    def file_read(self, path):
        self.logger.debug("file read:%s" % path)
        rc, out, err = self.execute("cat %s" % path, showout=False)
        return out

    def sudo_cmd(self, command):

        if "\n" in command:
            raise RuntimeError(
                "cannot do sudo when multiline script:%s" %
                command)

        if hasattr(self, 'sshclient'):
            login = self.sshclient.config.data['login']
            passwd = self.sshclient.config.data['passwd_']
        else:
            login = getattr(self, 'login', '')
            passwd = getattr(self, 'passwd', '')

        if "darwin" in self.platformtype.osname:
            return command
        if login == 'root':
            return command

        passwd = passwd or "\'\'"

        cmd = 'echo %s | sudo -H -SE -p \'\' bash -c "%s"' % (
            passwd, command.replace('"', '\\"'))
        return cmd

    def file_write(self, path, content, mode=None, owner=None, group=None,
                   append=False, sudo=False, showout=True):
        """
        @param append if append then will add to file

        if file bigger than 100k it will not set the attributes!

        """

        if showout:
            self.logger.debug("file write:%s" % path)

        if len(content) > 100000:
            # when contents are too big, bash will crash
            temp = self.j.sal.fs.getTempFileName()
            self.j.sal.fs.writeFile(filename=temp, contents=content,
                                    append=False)
            self.upload(temp, path,showout=showout)
            self.j.sal.fs.remove(temp)
        else:
            content2 = content.encode('utf-8')
            # sig = hashlib.md5(content2).hexdigest()
            parent = self.j.sal.fs.getParent(path)
            cmd = "set -e;mkdir -p %s\n" % parent

            content_base64 = base64.b64encode(content2).decode()
            # cmd += 'echo "%s" | openssl base64 -D '%content_base64   #DONT
            # KNOW WHERE THIS COMES FROM?
            cmd += 'echo "%s" | openssl base64 -A -d ' % content_base64

            if append:
                cmd += ">> %s\n" % path
            else:
                cmd += "> %s\n" % path

            if mode:
                cmd += 'chmod %s %s\n' % (mode, path)
            if owner:
                cmd += 'chown %s %s\n' % (owner, path)
            if group:
                cmd += 'chgrp %s %s\n' % (group, path)

            # if sig != self.file_md5(location):
            if sudo and self.type == "ssh":
                self._execute_script(cmd, sudo=sudo, die=True, showout=False)
            else:
                res = self.execute(cmd, sudo=sudo, showout=False)

        self.cache.reset()

    def test(self):

        # test that it does not do repeating thing & cache works
        for i in range(1000):
            ptype = self.platformtype

        for i in range(1000):
            env = self.env

        prev = None
        for i in range(10000):
            tmp = self.exists("/tmp")
            if prev is not None:
                assert prev == tmp
            prev = tmp

        content = ""
        for i in range(10):
            content += "abcdefg hijklmn %s\n" % i

        contentbig = ""
        for i in range(20000):
            contentbig += "abcdefg hijklmn %s\n" % i

        tmpfile = self.dir_paths["TMPDIR"] + "/testfile"

        self.file_write(tmpfile, content, append=False)
        content2 = self.file_read(tmpfile)

        assert content == content2

        self.file_write(tmpfile, contentbig, append=False)
        content2 = self.file_read(tmpfile)

        assert contentbig == content2

        self.logger.debug("TEST for executor done")
