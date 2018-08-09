from Jumpscale import j

import sys
import os
import platform
# import re


# def _useELFtrick(file):
#     fd = os.open(file, os.O_RDONLY)
#     out = os.read(fd, 5)
#     if out[0:4] != "\x7fELF":
#         result = 0  # ELF trick fails...
#     elif out[4] == '\x01':
#         result = 32
#     elif out[4] == '\x02':
#         result = 64
#     else:
#         result = 0
#     os.close(fd)
#     return result
JSBASE = j.application.jsbase_get_class()


class PlatformTypes(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.core.platformtype"
        JSBASE.__init__(self)
        self._myplatform = None
        self._platformParents = {}
        self._platformParents["unix"] = ["generic"]
        self._platformParents["linux"] = ["unix"]
        self._platformParents["linux32"] = ["linux", "unix32"]
        self._platformParents["linux64"] = ["linux", "unix64"]
        self._platformParents["unix32"] = ["unix"]
        self._platformParents["unix64"] = ["unix"]
        self._platformParents["alpine"] = ["linux"]
        self._platformParents["alpine64"] = ["alpine", "linux64"]
        self._platformParents["alpine32"] = ["alpine", "linux32"]
        self._platformParents["ubuntu"] = ["linux"]
        self._platformParents["ubuntu64"] = ["ubuntu", "linux64"]
        self._platformParents["ubuntu32"] = ["ubuntu", "linux32"]
        self._platformParents["mint64"] = ["mint", "ubuntu64"]
        self._platformParents["mint32"] = ["mint", "ubuntu32"]
        self._platformParents["win"] = ["generic"]
        self._platformParents["win32"] = ["win"]
        self._platformParents["win64"] = ["win"]
        self._platformParents["win7"] = ["win"]
        self._platformParents["win8"] = ["win"]
        self._platformParents["vista"] = ["win"]
        self._platformParents["cygwin32"] = ["cygwin"]
        self._platformParents["cygwin64"] = ["cygwin"]
        self._platformParents["win2008_64"] = ["win64"]
        self._platformParents["win2012_64"] = ["win64"]
        self._platformParents["cygwin_nt-10.064"] = ["win64", "cygwin64"]
        self._platformParents["cygwin_nt-10.032"] = ["win32", "cygwin32"]
        self._platformParents["arch"] = ["linux"]
        self._platformParents["arch32"] = ["arch", "linux32"]
        self._platformParents["arch64"] = ["arch", "linux64"]
        self._platformParents["redhat"] = ["linux"]
        self._platformParents["redhat32"] = ["redhat", "linux32"]
        self._platformParents["redhat64"] = ["redhat", "linux64"]
        # is not really linux but better to say I is I guess (kds)
        self._platformParents["darwin32"] = ["darwin"]
        self._platformParents["darwin64"] = ["darwin"]
        self._platformParents["osx64"] = ["darwin64", "osx"]
        self._platformParents["debian"] = ["ubuntu"]
        self._platformParents["debian32"] = ["debian", "linux32"]
        self._platformParents["debian64"] = ["debian", "linux64"]
        self._cache = {}

    @property
    def myplatform(self):
        if self._myplatform is None:
            self._myplatform = PlatformType()
        return self._myplatform

    def getParents(self, name):
        res = [name]
        res = self._getParents(name, res)
        return res

    def _getParents(self, name, res=[]):
        if name in self._platformParents:
            for item in self._platformParents[name]:
                if item not in res:
                    res.append(item)
                res = self._getParents(item, res)
        return res

    def get(self, executor):
        """
        @param executor is an executor object, None or $hostname:$port or $ipaddr:$port or $hostname or $ipaddr
        """
        key = executor.id
        if key not in self._cache:
            self._cache[key] = PlatformType(executor=executor)
        return self._cache[key]


class PlatformType(JSBASE):

    def __init__(self, name="", executor=None):
        # print("INIT PLATFORMTYPE:%s" % executor)
        JSBASE.__init__(self)
        self.myplatform = name
        self._platformtypes = None
        self._is64bit = None
        self._osversion = None
        self._hostname = None
        self._uname = None
        if executor is None:
            self.executor = j.tools.executorLocal
        else:
            self.executor = executor

        # print("PLATFORMTYPE:%s"%self.executor)

        if name == "":
            self._getPlatform()

    @property
    def platformtypes(self):
        if self._platformtypes is None:
            platformtypes = j.core.platformtype.getParents(self.myplatform)
            self._platformtypes = [
                item for item in platformtypes if item != ""]
        return self._platformtypes

    @property
    def uname(self):
        if self._uname is None:
            if self.executor.type == "local":
                unn = os.uname()
                self._hostname = unn.nodename
                distro_info = platform.linux_distribution()
                if 'Ubuntu' in distro_info:
                    self._osversion = distro_info[1]
                elif 'ubuntu' in j.tools.executorLocal.stateOnSystem['os_type'].lower():
                    version = self.executor.execute('lsb_release -r')[1]
                    # version should be something like: 'Release:\t16.04\n
                    self._osversion = version.split(':')[-1].strip()
                else:
                    self._osversion = unn.release
                self._cpu = unn.machine
                self._platform = unn.sysname

            else:
                _uname = self.executor.stateOnSystem["uname"]
                if _uname.find("warning: setlocale") != -1:
                    raise RuntimeError(
                        "run js_shell 'j.tools.bash.local.locale_check()'")
                _uname = _uname.split("\n")[0]
                _tmp, self._hostname, _osversion, self._cpu, self._platform = _uname.split(
                    " ")
                if self.osname == "darwin":
                    self._osversion = _osversion
                else:
                    # is for ubuntu
                    if "version_id" in self.executor.stateOnSystem:
                        self._osversion = self.executor.stateOnSystem["version_id"]
                self._uname = _uname
        return self._uname

    @property
    def hostname(self):
        self.uname
        return self._hostname.split(".")[0]

    @property
    def is64bit(self):
        self.uname
        self._is64bit = "64" in self._cpu
        return self._is64bit

    @property
    def is32bit(self):
        self.uname
        self._is64bit = "32" in self._cpu
        return self._is64bit

    @property
    def osversion(self):
        self.uname
        if self._osversion is None:
            raise RuntimeError("need to fix, osversion should not be none")
            # print("####OSVERSION")
            # TELL KRISTOF YOU GOT HERE
            rc, lsbcontent, err = self.executor.execute(
                "cat /etc/*-release", replaceArgs=False, showout=False, die=False)
            if rc == 0:
                import re
                try:
                    expr = re.findall(r"DISTRIB_ID=(\w+)", lsbcontent)
                    self._osname = expr[0].lower()
                    expr = re.findall(r"DISTRIB_RELEASE=([\w.]+)", lsbcontent)
                    self._osversion = expr[0].lower()
                except IndexError as e:
                    self._osversion = self.uname
            else:
                self._osversion = self.uname
        return self._osversion

    @property
    def osname(self):
        if "os_type" not in self.executor.stateOnSystem:
            return "unknown"
        return self.executor.stateOnSystem["os_type"]

    def checkMatch(self, match):
        """
        match is in form of linux64,darwin
        if any of the items e.g. darwin is in getMyRelevantPlatforms then return True
        """
        tocheck = self.platformtypes
        matches = [item.strip().lower()
                   for item in match.split(",") if item.strip() != ""]
        for match in matches:
            if match in tocheck:
                return True
        return False

    def _getPlatform(self):

        if self.is32bit:
            name = "%s32" % (self.osname)
        else:
            name = "%s64" % (self.osname)

        self.myplatform = name

    def has_parent(self, name):
        return name in self.platformtypes

    def dieIfNotPlatform(self, platform):
        if not self.has_parent(platform):
            raise j.exceptions.RuntimeError(
                "Can not continue, supported platform is %s, this platform is %s" %
                (platform, self.myplatform))

    @property
    def isUbuntu(self):
        return self.has_parent("ubuntu")

    @property
    def isMac(self):
        return self.has_parent("darwin")

    @property
    def isAlpine(self):
        return self.has_parent("alpine")

    @property
    def isUnix(self):
        '''Checks whether the platform is Unix-based'''
        return self.has_parent("unix")

    @property
    def isWindows(self):
        '''Checks whether the platform is Windows-based'''
        return self.has_parent("win")

    @property
    def isLinux(self):
        '''Checks whether the platform is Linux-based'''
        return self.has_parent("linux")

    @property
    def isXen(self):
        '''Checks whether Xen support is enabled'''
        return j.sal.process.checkProcessRunning('xen') == 0

    @property
    def isVirtualBox(self):
        '''Check whether the system supports VirtualBox'''
        return self.executor.stateOnSystem.get('vboxdrv', False)

    # @property
    # def isHyperV(self):
    #     '''Check whether the system supports HyperV'''
    #     # TODO: should be moved to _getPlatform & proper parent definition
    #     if self.isWindows:
    #         import winreg as wr
    #         try:
    #             virt = wr.OpenKey(
    #                 wr.HKEY_LOCAL_MACHINE,
    #                 'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization',
    #                 0,
    #                 wr.KEY_READ | wr.KEY_WOW64_64KEY)
    #             wr.QueryValueEx(virt, 'Version')
    #         except WindowsError:
    #             return False
    #         return True
    #     return False

    def __str__(self):
        return str(self.myplatform)

    __repr__ = __str__
