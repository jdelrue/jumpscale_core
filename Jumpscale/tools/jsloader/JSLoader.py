import os
import sys
import json
import fcntl
import pystache
from subprocess import Popen, PIPE
from ...core.JSBase import JSBase, jwalk

import functools
import types

# for monkey-patching the j instance to add namespace... "things"
patchers = [
    {'from': 'application', 'to': 'core.application'},
    {'from': 'dirs', 'to': 'core.dirs'},
    {'from': 'errorhandler', 'to': 'core.errorhandler'},
    {'from': 'exceptions', 'to': 'core.errorhandler.exceptions'},
    {'from': 'events', 'to': 'core.events'},
    {'from': 'data.datacache', 'to': 'data.cache'},
    {'from': 'logging', 'to': 'core.logging'},
    {'from': 'core.state', 'to': 'tools.executorLocal.state'},
]

bootstrap = [
        ('', 'core', 'core', 'Core'),
        ('', 'tools', 'tools', 'Tools'),
        ('', 'sal', 'sal', 'Sal'),
        ('', 'data', 'data', 'Data'),
        ('', 'clients', 'clients', 'Clients'),
        ('', 'servers', 'servers', 'Servers'),
        #('', 'errorhandling', 'errorhandling', 'Exceptions'),
        ('data', 'types', 'data.types.Types', 'Types'),
        ('data', 'text', 'data.text.Text', 'Text'),
        # idgen not strictly needed for bootstrap but for error reporting
        ('data', 'idgenerator', 'data.idgenerator.IDGenerator', 'IDGenerator'),
        ('sal', 'fs', 'fs.SystemFS', 'SystemFS'),
        ('core', 'application', 'core.Application', 'Application'),
        ('core', 'errorhandler', 'errorhandler.ErrorHandler', 'ErrorHandler'),
        ('data', 'datacache', 'data.cache.Cache', 'Cache'),
        ('tools', 'jsloader', 'tools.jsloader.JSLoader', 'JSLoader'),
        ('tools', 'executorLocal', 'tools.executor.ExecutorLocal',
                                    'ExecutorLocal'),
        #('', 'errorhandling', 'errorhandling.JSExceptions',
        #                        'ExceptionsFactory'),
        ('', 'dirs', 'core.Dirs', 'Dirs'),
        ('core', 'platformtype', 'core.PlatformTypes', 'PlatformTypes'),
        ('sal', 'process', 'sal.process.SystemProcess', 'SystemProcess'),
        ('', 'application', 'core.application', None),
        ('', 'cache', 'data.cache', None),
        #('core', 'state', 'tools.executorLocal.state', None),
        ('core', 'dirs', 'dirs', None),
        ('', 'errorhandler', 'core.errorhandler', None),
        ('', 'exceptions', 'core.errorhandler.exceptions', None),
    ]

def find_jslocation(line):
    """ finds self.__jslocation__ for class-instance declaration version
        OR __jslocation__ with whitespace in front of it, indicating
        static version:

        class Foo:
            def __init__(...)
                self.__jslocation__ = 'j.foo'

        OR:

        class Foo:
            __jslocation__ = 'j.foo'
    """
    if line.find("self.__jslocation__") != -1:
        return True
    idx = line.find("__jslocation__")
    if idx == -1:
        return False
    # ok found something like '<space><space>__jsinstance__ = ......' ?
    prefix = line[:idx]
    return prefix.isspace()

# gets down to the Jumpscale core9 subdirectory from here
# (.../Jumpscale/tools/loader/JSLoader.py)
plugin_path = os.path.dirname(os.path.abspath(__file__))
plugin_path = os.path.dirname(plugin_path)
top_level_path = os.path.dirname(plugin_path)

def add_dynamic_instance(j, parent, child, module, kls):
    """ very similar to dynamic_generate, needs work
        to morph into using same code
    """
    #print ("adding", parent, child, module, kls)
    if not parent:
        parent = j
    else:
        parent = getattr(j, parent)
    if kls:
        # assume here that modules are imported from Jumpscale *only*
        # (*we're in boostrap mode so it's ok), and hand-create
        # a full module path.
        #print (top_level_path)
        if "." in module:
            mname = "%s.py" % module.replace(".", "/")
            fullpath = os.path.join(top_level_path, mname)
        else:
            mname = "%s/__init__.py" % module.replace(".", "/")
            fullpath = os.path.join(top_level_path, mname)
        #print ("fullpath", fullpath)
        parent._add_instance(child, "Jumpscale." + module, kls,
                             fullpath, basej=j)
        #print ("added", parent, child)
    else:
        walkfrom = j
        for subname in module.split('.'):
            walkfrom = getattr(walkfrom, subname)
        parent.__aliases__[child] = walkfrom

def bootstrap_j(j, logging_enabled=False, filter=None, config_dir=None):

    # LoggerFactory isn't instantiated from JSBase so there has to
    # be a little bit of a dance to get it established and pointing
    # to the right global j.  JSBase now contains a property "j"
    # which is actually a singleton (global)

    if config_dir:
        os.environ['HOSTCFGDIR'] = config_dir

    j.j = j # sets up the global singleton
    j.__jsfullpath__ = os.path.join(plugin_path, "Jumpscale.py")
    j.__jsmodulepath__ = 'Jumpscale'
    j.j.__dynamic_ready__ = False # set global dynamic loading OFF

    DLoggerFactory = j._jsbase('LoggerFactory',
                        ['Jumpscale.logging.LoggerFactory.LoggerFactory'],
                        basej=j)
    l = DLoggerFactory()
    l.enabled = logging_enabled
    l.filter = filter or []  # default filter which captures all is *
    j.logging = l

    rootnames = []
    for (parent, child, module, kls) in bootstrap:
        add_dynamic_instance(j, parent, child, module, kls)
        if parent == '':
            rootnames.append(child)

    if False:
        DJSLoader = j._jsbase('JSLoader', [JSLoader], basej=j)
        dl = DJSLoader()
        #j = dl._dynamic_generate(j, modules, bases, aliases)
        j = dl.dynamic_generate(basej=j)

    # initialise
    j.tools.executorLocal.env_check_init() # OUCH! doubles file-accesses!
    j.dirs.reload()
    j.logging.init()  # will reconfigure the logging to use the config file
    #j.core.db_reset() # used fake redis up to now: move to real if it exists
    j.__dynamic_ready__ = True # set global dynamic loading ON

    #for jname in rootnames:
    #    getattr(j, jname)._child_mod_cache_checked = False

    return j

def lazyprop(fn):
    attr_name = '_lazy_' + fn.__name__

    @property
    @functools.wraps(fn)
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazyprop

def remove_dir_part(path):
    "only keep part after jumpscale or digitalme"
    state = 0
    res = []
    for item in path.split("/"):
        if state == 0:
            if item.find("Jumpscale") != - \
                    1 or item.find("DigitalMe") != -1:
                state = 1
        if state == 1:
            res.append(item)
    if len(res) < 2:
        raise RuntimeError("could not split path in jsloader")
    if res[0] == res[1]:
        if res[0].casefold().find("jumpscale") != - \
                1 or res[0].casefold().find("digitalme") != -1:
            res.pop(0)
    return "/".join(res)


class JSLoader():

    __jslocation__ = "j.tools.jsloader"

    def __init__(self):
        self.tryimport = False
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = self.j.logging.get("jsloader")
        return self._logger

    @property
    def autopip(self):
        return self.j.core.state.config["system"]["autopip"] in [
            True, "true", "1", 1]

    def _installDevelopmentEnv(self):
        cmd = "apt-get install python3-dev libssl-dev -y"
        self.j.sal.process.execute(cmd)
        self.j.sal.process.execute("pip3 install pudb")

    def _findSitePath(self):
        res = ""
        for item in sys.path:
            if "/site-packages" in item:
                if res == "" or len(item) < len(res):
                    res = item
        if res != "":
            return res
        for item in sys.path:
            if "/dist-packages" in item:
                if res == "" or len(item) < len(res):
                    res = item
        if res == "":
            raise RuntimeError("Could not find sitepath")
        return res

    @property
    def initPath(self):
        path = self._findSitePath() + "/jumpscale.py"
        # print("initpath:%s" % path)
        self.j.sal.fs.remove(path)

        return path

    def _pip(self, item):
        rc, out, err = self.j.sal.process.execute(
            "pip3 install %s" %
            item, die=False)
        if rc > 0:
            if "gcc' failed" in out:
                self._installDevelopmentEnv()
                rc, out, err = self.j.sal.process.execute(
                    "pip3 install %s" % item, die=False)
        if rc > 0:
            print("WARNING: COULD NOT PIP INSTALL:%s\n\n" % item)
        return rc

    def processLocationSub(self, jlocationSubName, jlocationSubList):
        # import a specific location sub (e.g. j.clients.git)

        classfile, classname, importItems = jlocationSubList

        generationParamsSub = {}
        generationParamsSub["classname"] = classname
        generationParamsSub["name"] = jlocationSubName
        importlocation = remove_dir_part(
            classfile)[:-3].replace("//", "/").replace("/", ".")
        generationParamsSub["importlocation"] = importlocation
        prefix = importlocation.split('.')[:-1]
        prefix = map(lambda x: x[0].upper()+x[1:], prefix)
        prefix = ''.join(prefix)
        generationParamsSub["classprefix"] = prefix

        rc = 0

        return rc, generationParamsSub

    def gather_modules(self, startpath=None, depth=0, recursive=True):
        """ identifies and gathers information about (only) jumpscale modules
        """
        # outCC = outpath for code completion
        # out = path for core of jumpscale

        # make sure the jumpscale toml file is set / will also link cmd files
        # to system
        self.j.tools.executorLocal.env_check_init()

        moduleList = {}
        baseList = {}
        if startpath is None:
            startpath = "j"
        if startpath == 'j':
            logfn = self.logger.info
        else:
            logfn = self.logger.debug

        # split the startpath (j format) to create subdirectory
        # search locations to be appended to plugin path
        startpath = startpath.split('.')[1:]

        # ok, set up a default based on the current location of THIS
        # file.  it's a hack however it will at least get started.
        # this will get the plugins recognised from Jumpscale
        # when there is absolutely no config file set up.
        #
        # related to issue #71
        #
        defaultplugins = {'Jumpscale': top_level_path}

        plugins = self.j.tools.executorLocal.state.configGet('plugins',
                        defaultplugins)
        if 'Jumpscale' not in plugins:
            plugins['Jumpscale'] = defaultplugins['Jumpscale']
        #print ("plugins", plugins)
        for name, _path in plugins.items():
            path = [_path] + startpath
            path = os.path.join(*path)
            logfn("find modules in jumpscale for : '%s'" % path)
            #print ("startpath: %s depth: %d" % (startpath, depth))
            if not self.j.sal.fs.exists(_path, followlinks=True):
                raise RuntimeError("Could not find plugin dir:%s" % _path)
            if not self.j.sal.fs.exists(path, followlinks=True):
                continue
            if False: # XXX hmmm.... nasty hack... disable....
                pth = path
                if pth[-1] == '/':
                    pth = pth[:-1]
                pth = os.path.split(pth)[0]
                sys.path = [pth] + sys.path
            moduleList, baseList = self.findModules(path=path,
                                    moduleList=moduleList,
                                    baseList=baseList,
                                    depth=depth,
                                    recursive=recursive)

        for jlocationRoot, jlocationRootDict in moduleList.items():
            # is per item under j e.g. self.j.clients

            #print ("jlocationRoot", jlocationRoot)
            #if jlocationRoot == 'j':
            #    print (jlocationRootDict)
            if not jlocationRoot.startswith("j.") and jlocationRoot != 'j':
                raise RuntimeError(
                    "jlocation should start with j, found: '%s', in %s" %
                    (jlocationRoot, jlocationRootDict))

            for subname, sublist in jlocationRootDict.items():
                rc, _ = self.processLocationSub(subname, sublist)
                if rc != 0:
                    # remove unneeded items
                    del jlocationRootDict[subname]

        return moduleList, baseList

    def add_submodules(self, basej, subname, sublist):
        #print (subname, sublist)
        parent = jwalk(basej, subname, end=-1)
        jname = subname.split(".")[-1]
        #print ("add_submodule", basej, jname, parent)
        #print ("dynamic generate root", jname, jlocationRoot)
        modulename, classname, imports = sublist
        #print ("subs", jname, sublist)
        importlocation = remove_dir_part(
            modulename)[:-3].replace("//", "/").replace("/", ".")
        #print ("importlocation", importlocation)
        parent._add_instance(jname, importlocation, classname,
                             fullpath=modulename,
                             basej=basej)

    def _old_dynamic_generate(self, basej, moduleList=None, baseList=None,
                                       aliases=None, basepath=None, depth=0):
        """ dynamically generates a jumpscale instance.

            uses gather_modules (which strips out non-Jumpscale modules for us)
            to get a list of root (base) modules that are in __init__.py
            files (and have a __jslocation__), and submodules that need
            to be added to them.

            base (root) instance constructors are **REQUIRED** to not
            have side-effects: they get instantiated straight away
            (see use of m.getter() below).

            anything else gets created as a lazy-property
            (see BaseGetter __getattribute__ override, they
             end up in BaseGetter.__subgetters__)
        """

        # gather list of modules (also initialises environment)
        if moduleList is None and baseList is None:
            moduleList, baseList = self.gather_modules(depth=depth)

        if isinstance(moduleList, dict):
            moduleList = moduleList.items()
        if aliases is None:
            aliases = map(lambda x: (x['from'], x['to']), patchers)

        _j = basej._create_jsbase_instance('Jumpscale')
        _j.__jslocation__ = 'j'
        _j.__jsdeps__ = {}
        rootmembers = {}

        #print ("baselist", baseList)
        for jlocationRoot in baseList:
            jname = jlocationRoot.split(".")[1].strip()
            kls = baseList[jlocationRoot]
            #print ("baselisted", jname, kls)
            m = _j._add_instance(jname, "Jumpscale."+jname, kls, basej=_j)
            member = m.getter()
            setattr(_j, jname, member)
            #print ("baselisted", jname, member)
            rootmembers[jname] = member

        for jlocationRoot, jlocationRootDict in moduleList:
            #self.add_submodules( _j, jlocationRoot, jlocationRootDict)
            #print ("jlocattion", jlocationRoot, jlocationRootDict)
            jname = jlocationRoot.split(".")[1].strip()
            #print ("dynamic generate root", jname, jlocationRoot)
            if jlocationRoot in baseList:
                continue
            member = JSBase._create_jsbase_instance(jname)
            setattr(_j, jname, member)
            #print ("created", jname, member)
            rootmembers[jname] = member

        #print ("rootmembers", rootmembers)

        for jlocationRoot, jlocationRootDict in moduleList:
            #print (jlocationRoot, jlocationRootDict)
            jname = jlocationRoot.split(".")[1].strip()
            member = rootmembers[jname]
            #print ("dynamic generate root", jname, jlocationRoot)
            for subname, sublist in jlocationRootDict.items():
                modulename, classname, imports = sublist
                #print ("subs", jlocationRoot, subname, sublist)
                importlocation = remove_dir_part(
                    modulename)[:-3].replace("//", "/").replace("/", ".")
                #print (importlocation)
                member._add_instance(subname, importlocation, classname,
                                     fullpath=modulename,
                                     basej=basej)

        for frommodule, tomodule in aliases:
            #print ("alias", frommodule, tomodule)
            #print ("patching", p)
            walkfrom = jwalk(_j, frommodule, end=-1)
            frommodule = frommodule.split('.')
            for fromname in frommodule[:-1]:
                #print ("patchfrom", walkfrom, fromname)
                walkfrom = getattr(walkfrom, fromname)
            child = frommodule[-1]
            walkto = _j
            for subname in tomodule.split('.'):
                #print ("patchto", walkto, subname)
                walkto = getattr(walkto, subname)
            setattr(walkfrom, child, walkto)

        _j.j = _j

        return _j

    def _dynamic_generate(self, basej, moduleList=None, baseList=None,
                                       aliases=None, basepath=None):
        """ dynamically generates a jumpscale instance.

            uses gather_modules (which strips out non-Jumpscale modules for us)
            to get a list of root (base) modules that are in __init__.py
            files (and have a __jslocation__), and submodules that need
            to be added to them.

            base (root) instance constructors are **REQUIRED** to not
            have side-effects: they get instantiated straight away
            (see use of m.getter() below).

            anything else gets created as a lazy-property
            (see BaseGetter __getattribute__ override, they
             end up in BaseGetter.__subgetters__)
        """

        # gather list of modules (also initialises environment)
        if moduleList is None and baseList is None:
            moduleList, baseList = self.gather_modules(depth=2)

        if isinstance(moduleList, dict):
            moduleList = moduleList.items()
        if aliases is None:
            aliases = list(map(lambda x: (x['from'], x['to']), patchers))

        #print ("aliases", aliases)
        _j = basej._create_jsbase_instance('Jumpscale')
        _j.__jslocation__ = 'j'
        _j.__fullpath__ = None # TODO
        _j.__modulepath__ = 'Jumpscale'
        _j.__jsdeps__ = {}
        rootmembers = {}

        #print ("baselist", baseList)
        for jlocationRoot in baseList:
            #print ("jlocationRoot", jlocationRoot)
            jname = jlocationRoot.split(".")[1].strip()
            kls = baseList[jlocationRoot]
            #print ("baselisted", jname, kls)
            m = _j._add_instance(jname, "Jumpscale."+jname, kls, basej=_j)
            member = m.getter()
            if hasattr(m.kls, '__jsdeps__'):
                #print ("jlocation __jsdeps__", jname, m.kls.__jsdeps__,
                #       member.__class__.__name__, member.__module__,
                #       m.kls.__jsbasekls__.__module__)
                for cjname, childspec in m.kls.__jsdeps__.items():
                    if isinstance(childspec, str):
                        childspec = childspec, childspec
                    childmodule, childkls = childspec
                    if not childmodule.startswith('Jumpscale'): # plugins
                        cmn = "Jumpscale.%s.%s" % (jname, childmodule)
                    else:
                        cmn = childmodule
                    if not cjname.startswith("j."):
                        cm = member._add_instance(cjname, cmn, childkls,
                                                  basej=_j)
                        #print ("adding child", cmn, member, cjname,
                        #            cm.subname, cm.modulepath, cm.objectname)
                    else:
                        walkfrom = jwalk(_j, cjname, start=1, end=-1)
                        setattr(walkfrom, cjname, cm.kls)

            setattr(_j, jname, member)
            #print ("baselisted", jname, member)
            rootmembers[jname] = member

        for jlocationRoot, jlocationRootDict in moduleList:
            #print ("jlocattion", jlocationRoot, jlocationRootDict)
            jname = jlocationRoot.split(".")[1].strip()
            #print ("dynamic generate root", jname, jlocationRoot)
            if jlocationRoot in baseList:
                continue
            member = JSBase._create_jsbase_instance(jname)
            setattr(_j, jname, member)
            #print ("created", jname, member)
            rootmembers[jname] = member

        #print ("rootmembers", rootmembers)

        for frommodule, tomodule in aliases:
            #print ("alias", frommodule, tomodule)
            #print ("patching", p)
            walkfrom = jwalk(_j, frommodule, end=-1)
            walkto = jwalk(_j, tomodule)
            child = frommodule.split('.')[-1]
            setattr(walkfrom, child, walkto)

        _j.j = _j
        _j.core.db_reset()
        #_j.data.cache.reset()
        _j.cache = _j.data.cache
        _j.tools.executorLocal.initEnv()

        for jname in rootmembers:
            rootmembers[jname]._child_mod_cache_checked = False

        return _j

    def _old_generate(self):
        """ generates the jumpscale init file: jumpscale
            as well as the one required for code generation

            to call:
            ipython -c 'from Jumpscale import j;j.tools.jsloader.generate()'
        """

        # gather list of modules (also initialises environment)
        moduleList, baseList = self.gather_modules()

        # outCC = outpath for code completion
        # out = path for core of jumpscale

        outJSON = os.path.join(
            self.j.dirs.HOSTDIR,
            "autocomplete",
            "jumpscale.json")
        self.j.sal.fs.createDir(os.path.join(self.j.dirs.HOSTDIR,
                                "autocomplete"))

        out = self.initPath
        self.logger.info("* jumpscale path:%s" % out)
        self.logger.info("* jumpscale codecompletion path:%s" % outCC)
        self.initPath  # to make sure empty one is created

        modlistout_json = json.dumps(moduleList, sort_keys=True, indent=4)
        self.j.sal.fs.writeFile(outJSON, modlistout_json)

    def _pip_installed(self):
        """return the list of all installed pip packages
        """
        _, out, _ = self.j.sal.process.execute(
            'pip3 list --format json', die=False, showout=False)
        pip_list = json.loads(out)
        return [p['name'] for p in pip_list]

    def findJumpscaleLocationsInFile(self, path):
        """
        returns:
            [$classname]["location"] =$location
            [$classname]["import"] = $importitems
        """
        res = {}
        C = self.j.sal.fs.readFile(path)
        classname = None
        locfound = False
        for line in C.split("\n"):
            if line.startswith("class "):
                classname = line.replace(
                    "class ", "").split(":")[0].split(
                    "(", 1)[0].strip()
                if classname == "JSBaseClassConfig":
                    break
            if find_jslocation(line) and locfound == False:
                if classname is None:
                    fname = os.path.split(path)[1]
                    if fname == 'JSLoader.py':
                        # XXX sigh doing manual parsing of python files
                        # like this is never a good idea, it is much
                        # better to do an AST syntax tree walk, that's
                        # what it's for.  JSLoader.py has some occurrences
                        # of __jslocation__ that are being detected,
                        # so we skip them here.
                        continue
                    raise RuntimeError(
                        "Could not find class in %s "
                        "while loading jumpscale lib." %
                        path)
                # XXX not a good way to get value after equals (remove " and ')
                #print ("line ------->", line)
                location = line.split("=", 1)[1]
                location = location.replace('"', "")
                location = location.replace("'", "").strip()
                if location.find("__jslocation__") == -1:
                    if classname not in res:
                        res[classname] = {}
                    res[classname]["location"] = location
                    locfound = True
                    self.logger.debug("%s:%s:%s" % (path, classname, location))
            if line.find("self.__imports__") != -1:
                if classname is None:
                    raise RuntimeError(
                        "Could not find class in %s " +
                        "while loading jumpscale lib." %
                        path)
                importItems = line.split(
                    "=",
                    1)[1].replace(
                    "\"",
                    "").replace(
                    "'",
                    "").strip()
                importItems = [
                    item.strip() for item in importItems.split(",")
                    if item.strip() != ""]
                if classname not in res:
                    res[classname] = {}
                res[classname]["import"] = importItems

        return res

    def findModules(self, path, moduleList=None, baseList=None, depth=None,
                          recursive=True):
        """ walk over code files & find locations for jumpscale modules
            return as two dicts.

            format of moduleList:
            [$rootlocationname][$locsubname]=(classfile,classname,importItems)

            format of baseList:
            [$rootlocationname]=(classname,jlocation)
        """
        # self.logger.debug("modulelist:%s"%moduleList)
        if moduleList is None:
            moduleList = {}
        if baseList is None:
            baseList = {}

        self.logger.info("findmodules in %s, depth %s" % (path, repr(depth)))

        # ok search for files up to the requested depth, BUT, __init__ files
        # are treated differently: they are depth+1 because searching e.g.
        # "j.core" we want to look for Jumpscale/core/__init__.py
        initfiles = self.j.sal.fs.listFilesInDir(path, recursive, "__init__.py",
                                               depth=depth+1)
        pyfiles = self.j.sal.fs.listFilesInDir(path, recursive, "*.py",
                                               depth=depth)
        pyfiles = initfiles + pyfiles
        for classfile in pyfiles:
            #print("found", classfile)
            basename = self.j.sal.fs.getBaseName(classfile)
            if basename.startswith('__init__'):
                for classname, item in self.findJumpscaleLocationsInFile(
                        classfile).items():
                    #print ("found __init__", classfile, classname, item)
                    # hmm probably can use moduleList but not sure...
                    if "location" not in item:
                        continue
                    location = item["location"]
                    baseList[location] = classname

            if basename.startswith("_"):
                continue
            if "actioncontroller" in basename.lower():
                continue
            # look for files starting with Capital
            if str(basename[0]) != str(basename[0].upper()):
                continue

            for classname, item in self.findJumpscaleLocationsInFile(
                    classfile).items():
                # item has "import" & "location" as key in the dict
                if "location" not in item:
                    continue
                location = item["location"]
                if "import" in item:
                    importItems = item["import"]
                else:
                    importItems = []

                locRoot = ".".join(location.split(".")[:-1])
                locSubName = location.split(".")[-1]
                if locRoot not in moduleList:
                    moduleList[locRoot] = {}
                moduleList[locRoot][locSubName] = (
                    classfile, classname, importItems)
        return moduleList, baseList

    def removeEggs(self):
        for key, path in self.j.clients.git.getGitReposListLocal(
                account="jumpscale").items():
            for item in [item for item in self.j.sal.fs.listDirsInDir(
                    path) if item.find("egg-info") != -1]:
                self.j.sal.fs.removeDirTree(item)

    def prepare_config(self, autocompletepath=None):
        """ prepares the plugin configuration
        """

        if self.j.dirs.HOSTDIR == "":
            raise RuntimeError(
                "dirs in your jumpscale.toml not ok, hostdir cannot be empty")

        if autocompletepath is None:
            autocompletepath = os.path.join(self.j.dirs.HOSTDIR, "autocomplete")
            self.j.sal.fs.createDir(autocompletepath)

        for name, path in self.j.core.state.configGet('plugins', {}).items():
            if self.j.sal.fs.exists(path, followlinks=True):
                # link libs to location for hostos
                self.j.sal.fs.copyDirTree(path,
                                     os.path.join(autocompletepath, name),
                                     overwriteFiles=True,
                                     ignoredir=['*.egg-info',
                                                '*.dist-info',
                                                "*Jumpscale*",
                                                "*Tests*",
                                                "*tests*"],

                                     ignorefiles=['*.egg-info',
                                                  "*.pyc",
                                                  "*.so",
                                                  ],
                                     rsync=True,
                                     recursive=True,
                                     rsyncdelete=True,
                                     createdir=True)

        self.j.sal.fs.touch(os.path.join(self.j.dirs.HOSTDIR, 'autocomplete',
                "__init__.py"))

        # DO NOT AUTOPIP the deps are now installed while installing the libs
        self.j.core.state.configSetInDictBool("system", "autopip", False)
        # j.application.config["system"]["debug"] = True

    def generate(self, autocompletepath=None):
        """
        """

        print ("GENERATE NOW DEPRECATED. DO NOT USE. IT IS CRITICAL TO")
        print ("DELETE /usr/lib/python3/dist-packages/jumpscale.py")
        return
        self.prepare_config(autocompletepath)
        self._generate()

    def dynamic_generate(self, autocompletepath=None, basej=None,
                               moduleList=None, baseList=None,
                                       aliases=None):
        """
        """
        assert basej is not None
        self.prepare_config(autocompletepath)
        return self._dynamic_generate(basej, moduleList,
                                      baseList, aliases)