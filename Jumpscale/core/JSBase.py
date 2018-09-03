from copy import copy
import os
import sys
import importlib.util
import inspect
import traceback
import gc    # needed for camelcase
import trace # needed for camelcase


def jwalk(instance, name, start=None, end=None, stealth=False):
    for fromname in name.split('.')[start:end]:
        #print ("patchfrom", walkfrom, fromname)
        if stealth: # use BaseGetter __getattribute__
            d = object.__getattribute__(instance, '__subgetters__')
            if fromname in d:
                instance = d[fromname]
            else:
                instance = getattr(instance, fromname)
        else:
            instance = getattr(instance, fromname)
    return instance


def _import_parent_recurse(mpathname, parent_name):
    if mpathname in sys.modules:
        return
    ppath = os.path.join(parent_name, "__init__.py")
    #print ("import recurse", mpathname, ppath, parent_name)
    spec = importlib.util._find_spec_from_path(ppath, None)
    #print ("spec", spec)
    if spec:
        module = importlib.util.module_from_spec(spec)
        # print ( "adding module", mpathname, module,
        #        mpathname not in sys.modules)
        if mpathname not in sys.modules:
            sys.modules[mpathname] = module
    mpathname = mpathname.rpartition('.')[0]
    parent_name = os.path.split(parent_name)[0]
    if mpathname:
        _import_parent_recurse(mpathname, parent_name)


def jspath_import(modulepath, fullpath):

    #print ("jspath_import fullpath %s modulepath %s" % (fullpath, modulepath))

    module = sys.modules.get(modulepath, None)
    if not module:
        parent_name = modulepath.rpartition('.')[0]

        # ok check parent not in modules, if not, track that down recursively
        # XXX however... ahh slightly unfortunate: we also need to check
        # all the plugins - not just the current parent path - to see if
        # the parent name matches there.  whoops.
        if parent_name:
            parentmodule = sys.modules.get(parent_name, None)
            if not parentmodule:
                #print ("jspath_import parent fullpath %s modath %s" % \
                #            (parent_name, modulepath))
                if False: # TODO
                    parent_fullpath, parentimport = os.path.split(fullpath)
                    if parentimport == '__init__.py':
                        parent_fullpath = os.path.dirname(parent_fullpath)
                    parent_fullpath = os.path.join(parent_fullpath,
                                                   "__init__.py")
                    print ("parent fullpath %s modulepath %s" % \
                                (parent_fullpath, parent_name))
                    jspath_import(parent_name, parent_fullpath)
                else:
                    #parent = importlib.import_module(parent_name)
                    __import__(parent_name)
                    #print ("jspath_imported parent %s %s" % \
                    #            (parent_name, repr(parent)))
        spec = importlib.util.spec_from_file_location(modulepath, fullpath)
        #print ("parentname", modulepath, parent_name)
        #print ("spec", spec, dir(spec))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    if module not in sys.modules:
        sys.modules[modulepath] = module

    module.__jsmodpath__ = modulepath
    module.__jsfullpath__ = fullpath

    return module

def resolve_klsmodule(__jsfullpath__, __jsmodulepath__, kls):
    #print ("resolve_klsmodule", __jsfullpath__, __jsmodulepath__, kls)
    # ok we assume it's a jumpscale class, FOR NOW
    # we assume it's in the same plugin as the parent
    # (don't use this for pulling in classes from other plugins!)
    # so, from the parent, get a fixed path
    #module = __import__(modulename)
    #mpathname, _, objectname = kls.rpartition('.')
    if not isinstance(kls, str): # either "classname" or "module.classname"
        return kls
    if '.' not in kls: # classname: must be relative
        return (__jsmodulepath__, kls)
    # module.classname
    mpathname, _, objectname = kls.rpartition('.')
    return (objectname, mpathname)

def mpath_to_pyfile(mp):
    if mp[-1].lower() == mp[-1]:
        mp.append('__init__.py')
        mp = mp[1:] # plugin name is duplicated: cut one of them...
    else:
        mp[-1] += ".py"
    return mp

def lookup_kls(__jsfullpath__, __jsmodulepath__, kls):
    #print ("lookup_kls", __jsfullpath__, __jsmodulepath__, kls)
    kls = resolve_klsmodule(__jsfullpath__, __jsmodulepath__, kls)
    if not isinstance(kls, tuple):
        #print ("lookup was not a tuple", kls)
        return kls # it was a class already: just return it

    #print ("lookup_kls", kls)
    (objectname, mpathname) = kls
    parent_path = os.path.split(__jsfullpath__)[0]

    # ok first we count the number of dots in the parent module
    # and walk back that number of path entries
    dotcount = len(mpathname.split(".")) - 1
    parent_path = parent_path.split('/')[:-dotcount]
    parent_path = "/".join(parent_path)

    # detect whether the full module path is an __init__.py
    # or a standard module: if the last path is all lower-case it's
    # __init__.py
    #print ("parent_path", __jsfullpath__, parent_path, mpathname)
    mp = mpathname.split('.')
    mp = mpath_to_pyfile(mp)
    fullpath = os.path.join(*mp)
    fullpath = os.path.join(parent_path, fullpath)

    # XXX TODO, check plugin directory matches...
    #plugins = basej.tools.executorLocal.state.configGet('plugins')

    #print ("mpath", mpathname, fullpath)
    module = jspath_import(mpathname, fullpath)
    # ok finally get the module (and the class)
    nkls = getattr(module, objectname)
    nkls.__jsfullpath__ = fullpath
    nkls.__jsmodulepath__ = mpathname

    return nkls

# intrusive live introspection for camel_case transition
# issue #105

camel_case_log = {}

def load_camel_case_log():
    global camel_case_log
    if len(camel_case_log) > 0:
        return # loaded already
    try:
        with open("camel_case_log.txt") as f:
            for l in f.readlines():
                l = l.strip()
                (k, v) = l.split("\t")
                camel_case_log[k] = v
    except (OSError, IOError):
        pass # ok, ignore it.  empty.  first time loading

load_camel_case_log()

def save_camel_case_log_entry(k, v):
    global camel_case_log
    with open("camel_case_log.txt", "a+") as f:
        f.write("%s\t%s\n" % (k, v))

# this is taken straight out of the trace.py module
caller_cache = {}
def file_module_function_of(frame):

    global caller_cache

    code = frame.f_code
    filename = code.co_filename
    if filename:
        modulename = trace._modname(filename)
    else:
        modulename = None

    lineno = frame.f_lineno
    funcname = code.co_name
    clsname = None
    if code in caller_cache:
        if caller_cache[code] is not None:
            clsname = caller_cache[code]
    else:
        caller_cache[code] = None
        ## use of gc.get_referrers() was suggested by Michael Hudson
        # all functions which refer to this code object
        funcs = [f for f in gc.get_referrers(code)
                     if inspect.isfunction(f)]
        # require len(func) == 1 to avoid ambiguity caused by calls to
        # new.function(): "In the face of ambiguity, refuse the
        # temptation to guess."
        if len(funcs) == 1:
            dicts = [d for d in gc.get_referrers(funcs[0])
                         if isinstance(d, dict)]
            if len(dicts) == 1:
                classes = [c for c in gc.get_referrers(dicts[0])
                               if hasattr(c, "__bases__")]
                if len(classes) == 1:
                    # ditto for new.classobj()
                    clsname = classes[0].__name__
                    # cache the result - assumption is that new.* is
                    # not called later to disturb this relationship
                    # _caller_cache could be flushed if functions in
                    # the new module get called.
                    caller_cache[code] = clsname
    if clsname is not None:
        funcname = "%s.%s" % (clsname, funcname)

    return filename, lineno, modulename, funcname


#https://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545
def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        tmp = meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0]
        cls = getattr(inspect.getmodule(meth), tmp)
        if isinstance(cls, type):
            return cls
    # handle special descriptor objects
    return getattr(meth, '__objclass__', None)

def log_camel_case_found(obj, frame, attr, attrname):
    global camel_case_log
    (fname, lineno, modulename, funcname) = file_module_function_of(frame)
    while True:
        if funcname == 'JSBase.__getattr__' or \
            funcname == 'BaseGetter.__getattribute__':
            frame = frame.f_back
            (fname, lineno, modulename, funcname) = \
                        file_module_function_of(frame)
            continue
        break
    kls = get_class_that_defined_method(attr)
    report = "%s:%d:%s" % (fname, lineno, modulename)
    # TODO: this is where the warning has to be put.
    #print ("camel case found", report)
    if report in camel_case_log:
        return
    calledmodule = kls.__module__.split('.')[-1]
    called = "%s.%s.%s" % (calledmodule, kls.__name__, attrname)
    camel_case_log[report] = called
    save_camel_case_log_entry(report, called)

def _camel(s):
    return s != s.lower() and s != s.upper()

def camel(s):
    if not _camel(s):
        return False
    # exclude some outliers
    if s.startswith("__") and s.endswith("__"):
        return False
    if "_" not in s:
        return False
    if s.startswith("_") and "_" not in s[1:] and not camel(s[1:]):
        return False
    return True

def to_snake_case(not_snake_case):
    final = ''
    while not_snake_case.startswith("_"):
        final += "_"
        not_snake_case = not_snake_case[1:]
    for i in range(len(not_snake_case)):
        item = not_snake_case[i]
        if i < len(not_snake_case) - 1:
            next_char_will_be_underscored = (not_snake_case[i+1] == "_"  \
                    or not_snake_case[i+1] == " " \
                    or not_snake_case[i+1].isupper())
        if (item == " " or item == "_") and next_char_will_be_underscored:
            continue
        elif (item == " " or item == "_"):
            final += "_"
        elif item.isupper():
            final += "_"+item.lower()
        else:
            final += item
    return final

def camelCase(st):
    output = ''.join(x for x in st.title() if x.isalnum())
    return output[0].lower() + output[1:]


class BaseGetter(object):
    """ this is a rather.. um... ugly class that has a list of module names
        added to it, where if a property is ever referred to it will either
        import a class instance in that module on-demand or return a
        previously-instantiated instance.

        example: /opt/code/github/threefold/jumpscale_core/... RedisFactory.py
        and a class named RedisFactory, and an instance name "redis",
        if ever Basegetter.redis is referred to, you get a RedisFactory()
        instantiated and returned
    """

    __dynamic_ready__ = False

    def __init__(self):
        self.__subgetters__ = {}
        self.__aliases__ = {}

    def find_jsmodule(self, modulepath, objectname):
        """ finds the absolute module path if it exists, otherwise
            does a best guess based on the plugin match.
            search here.
        """
        if modulepath in self.j.__jsmodlookup__:
            return self.j.__jsmodlookup__[modulepath]
        # ok, not in the json file, so make a best guess.
        mpath = modulepath.split('.')
        plugin = mpath[0]
        plugins = self.j.tools.jsloader.plugins
        assert plugin in plugins
        pluginpath = plugins[plugin]
        modname = [pluginpath] + mpath_to_pyfile(mpath[1:])
        modulename = os.path.join(*modname)
        fullchildname = ''
        info = (modulename, objectname, plugin, fullchildname)
        return info

    def _add_instorkls(self, subname, modulepath, objectname,
                      fullpath=None, basej=None, ask=False,
                      dynamicname=None):
        """ adds an instance (or class) to the __subgetters__ dictionary.
            When __getattribute__ is called, the instance will be created
            ON DEMAND based on the information passed in, and for the
            instance created to AUTOMATICALLY include a derivation
            from JSBase if it isn't already a base class
            (see ModuleSetup.getter)

            the "registration" process passes in the module path,
            object name, basej instance to be used, everything
            needed to DEFER the creation of a class instance
            until it's actually needed.  example:

            j._add_instance("application",
                            "Jumpscale.core.Application",
                            "Application", j)

            this REGISTERS the DESIRE to have an application instance
            be created "on demand", should it ever be referred to:

            In [3]: j.application
            Out[3]: <Jumpscale.core.JSBase.JSBasedApplication at 0x7f67ed5b8da0>

            note the inclusion of the automatic "JSBased" prefix on the
            original class named "Application".
        """
        basej = basej or self.j
        #print ("instorkls", self, subname, modulepath, objectname, basej, ask)

        if fullpath is None:
            info = self.find_jsmodule(modulepath, objectname)
            assert info
            (modulename, classname, plugin, fullchildname) = info
            fullpath = modulename
        #print ("self.fullpath1", fullpath)
        #print ("self.modpath/1", modulepath)

        ms = ModuleSetup(self, subname, modulepath, objectname,
                         fullpath, basej, ask, dynamicname)
        #print (dir(self))
        d = object.__getattribute__(self, '__subgetters__')
        d[subname] = ms
        return ms

    def _add_kls(self, subname, modulepath, objectname,
                      fullpath=None, basej=None, dynamicname=None):
        """ adds a kls to the __subgetters__ dictionary.  this is a
            quite complex lazy-loading system.
        """
        return self._add_instorkls(subname, modulepath, objectname,
                                   fullpath, basej, True, dynamicname)

    def _add_instance(self, subname, modulepath, objectname,
                      fullpath=None, basej=None, dynamicname=None):
        """ adds an instance to the __subgetters__ dictionary.
        """
        return self._add_instorkls(subname, modulepath, objectname,
                                   fullpath, basej, False, dynamicname)

    def __dir__(self):
        d = object.__getattribute__(self, '__subgetters__')
        keys = set(object.__dir__(self))
        keys.update(d.keys())
        d = object.__getattribute__(self, '__aliases__')
        keys.update(d.keys())
        try:
            jbk = object.__getattribute__(self, '__jsbasekls__')
        except AttributeError:
            jbk = None
        if jbk is not None:
            global_ready = object.__getattribute__(self.j, '__dynamic_ready__')
            dynamic_ready = object.__getattribute__(self, '__dynamic_ready__')
            if dynamic_ready and global_ready:
                keys = self._check_child_mod_cache(keys)
        keys = sorted(keys)
        return keys

    def __getattribute__(self, name):
        if name == 'JSBASE':
            return JSBase
        found = True
        try:
            object.__getattribute__(JSBase, name)
        except AttributeError:
            found = False
        if found:
            return object.__getattribute__(self, name)
        d = object.__getattribute__(self, '__aliases__')
        if name in d:
            return d[name]
        d = object.__getattribute__(self, '__subgetters__')
        if name in d:
            instance = d[name].getter()
            instance.j = self.j
            object.__setattr__(self, name, instance)
            d.pop(name)  # take the subgetter out now that it's been done
            return instance
        try:
            return object.__getattribute__(self, name)
        except AttributeError as e:
            z = e
        try:
            jbk = object.__getattribute__(self, '__jsbasekls__')
        except AttributeError:
            jbk = None
        if jbk:
            global_ready = object.__getattribute__(self.j, '__dynamic_ready__')
            dynamic_ready = object.__getattribute__(self, '__dynamic_ready__')
            if dynamic_ready and global_ready:
                d = object.__getattribute__(self, '__subgetters__')
                keys = set(d.keys())
                keys = self._check_child_mod_cache(keys, set([name]))
                instance = self._create_instance(name)
                if instance:
                    return instance
        return object.__getattribute__(self, name)

    def _create_instance(self, name):
        d = object.__getattribute__(self, '__subgetters__')
        if name not in d:
            return None
        instance = d[name].getter()
        instance.j = self.j
        object.__setattr__(self, name, instance)
        #del d[name]
        return instance

    def _check_child_mod_cache(self, keys, toadd=None):
        return keys

    def _get_lazy_instance(self, module):
        res = None
        d = object.__getattribute__(self, '__aliases__')
        if name in d:
            res = d[name]
        if res is None:
            d = object.__getattribute__(self, '__subgetters__')
            if name in d:
                res = d[name]


class ModuleSetup(object):
    def __init__(self, parentj, subname, modulepath, objectname,
                       fullpath, basej, ask, dynamicname):
        self.parentj = parentj
        self.subname = subname
        self.modulepath = modulepath # TODO or parentj.__jsmodulepath__
        self.objectname = objectname
        self.fullpath = fullpath # TODO or parentj.__jsfullpath__
        self.basej = basej
        self.dynamicname = dynamicname
        self._obj = None
        self._kls = None
        self.as_kls = ask # if True, a class will be returned.
        self._child_props = {}  # to be added after class is instantiated

    @property
    def kls(self):
        if self._kls is None:
            #print ("about to get modulepath %s object %s path %s basej %s" % \
            #   (self.modulepath, self.objectname, self.fullpath, self.basej))

            #module = jspath_import(self.modulepath, self.fullpath)
            #kls = getattr(module, self.objectname)
            #kls.__jsfullpath__ = self.fullpath
            #kls.__jsmodulepath__ = self.modulepath

            _kls = (self.objectname, self.modulepath)
            kls = lookup_kls(self.fullpath, self.modulepath, _kls)

            # check if kls has JSBase in it: if not, patch it in
            if hasattr(kls, 'mro'):
                mro = kls.mro()
            else:
                mro = []
            jsbased = False
            for m in mro:
                if m.__name__ != 'JSBase':
                    continue
                jsbased = True
                break
            if not jsbased:
                #klsname = "%s.%s" % (self.modulepath, self.objectname)
                kls = self.basej._jsbase(self.objectname, [kls],
                                         basej=self.basej,
                                         dynamicname=self.dynamicname)
            self._kls = kls
        return self._kls

    def getter(self):
        if self.as_kls:
            return self.kls
        return self.obj

    @property
    def obj(self):
        if self._obj is None:
            #print ("getter", self.kls)
            self._obj = self.kls()
            self._obj.__dynamic_ready__ = True
            # post-add child properties
            for cname, prop in self._child_props.items():
                setattr(self._obj, cname, prop)
        return self._obj


class JSBase(BaseGetter):

    def __init__(self, _logger=None):
        #print ("JSBase init", self.__class__)
        BaseGetter.__init__(self)
        self._logger = _logger
        self._cache = None
        self._cache_expiration = 3600
        self._logger_force = False
        self._late_init_called = False
        self._late_init_fns = []
        # these respectively make sure that dir / getattr are called only once
        self._child_mod_cache_checked = False # for __dir__
        self._child_toadd_cache_checked = set() # for direct getattr

    def __getattr__(self, attrname):
        """ issue #105 - okaay, so this where camelcase is to be detected,
            and if nonCamelCase is detected, a warning will be put on the
            console, the line number of the caller logged in a file, and
            the alternative (camel_case) function called instead.

            properties are *NOT* included, and are specifically detected
            and excluded by inspect.isdatadescriptor / isgetsetdescriptor

            the rules are:

            * convert CLASS METHODS ONLY (the callee).
              do NOT convert the caller... yet.
            * run a program (any program): warnings will be given,
              and also listed in a log file, along with the line numbers
              of where they were called FROM (callers).
            * run the automated tool <TBD> or just if feeling masochistic,
              edit the CALLERs by hands.

            do not do it the other way round: do NOT edit the callers
            first.  the code below is SPECIFICALLY designed to have
            CALLEEs be modified first.
        """
        # XXX not a good idea to do this.  once committed, REALLY have to
        # stick with it.
        #if not os.environ.get('CAMELCASECHECK'):
        #    return BaseGetter.__getattribute__(self, attrname)

        if not _camel(attrname): # it_was_one_of_these, it's_cool.
            return BaseGetter.__getattribute__(self, attrname)
        # so, it's a camelCaseThing. first try and get it *as* camelCase
        #print ("looking for", attrname)
        try:
            # ok try "snake" version...
            to_snake = to_snake_case(attrname)
            #to_camel = camelCase(attrname)
            #print ("looking for snake %s" % to_snake)
            attr = BaseGetter.__getattribute__(self, to_snake)
            if not inspect.ismethod(attr): # not a method
                return BaseGetter.__getattribute__(self, attrname)
            if isinstance(attr, property): # it's a property
                return BaseGetter.__getattribute__(self, attrname)
        except AttributeError:
            #print ("looking for %s failed, try %s" % (to_camel, attrname))
            return BaseGetter.__getattribute__(self, attrname)
        # ok that worked, so, hmmm, we should log finding the camel_case
        #print ("looking for %s worked" % to_camel)
        frame = inspect.currentframe().f_back # skip this __getattr__!
        log_camel_case_found(self, frame, attr, attrname)
        return attr

    def _check_child_mod_cache(self, keys, toadd=None):
        """ checks the child module.  has two modes.  toadd=None will
            do a filesystem walk (directory) at the current module
            path, and toadd=["list", "of", "modules"] will check
            directly for individual modules.  these are fired by
            dir(j.clients) and by getattr(j.clients, "fred") respectively
        """
        if toadd is None:
            if self._child_mod_cache_checked:
                return keys
            self._child_mod_cache_checked = True  # clear straight away
        else:
            tocheck = toadd.copy()
            for k in toadd:
                if k in self._child_toadd_cache_checked:
                    tocheck.remove(k)
                self._child_toadd_cache_checked.add(k)
            if not tocheck:  # nothing to check
                return keys
            toadd = tocheck
        #print ("JSBase check child cache", self, keys, toadd)
        #print ("fullpath", getattr(self, '__jsfullpath__', None))
        #print ("modpath", getattr(self, '__jsmodulepath__', None))
        module = self.__jsbasekls__.__module__
        filename = sys.modules[module].__file__
        #print ("mod,fname", module, filename)

        # obtain a list of modules listed across all plugins which match
        # the child's jslocation. XXX THIS REQUIRES that the plugin
        # directory naming hierarchy MATCH the jslocation!  it is absolutely
        # no good having j.something when the directory named "something"
        # does not match the plugin directory hierarchy!
        try:
            startchildj = object.__getattribute__(self, '__jslocation__')
        except AttributeError:
            #print ("no __jslocation__")
            return keys  # too early

        #print ("__jslocation__", startchildj)
        # really awkward but absolutely must avoid BaseGetter recursion
        try:
            loader = self.j.tools.jsloader
        except AttributeError:
            #print ("not found loader")
            return keys  # too early: skip it

        if False:
            loader = self.j
            for attr in ['tools', 'loader']:
                try:
                    #print ("searching", loader, attr)
                    loader = object.__getattribute__(loader, attr)
                    #loader = getattr(loader, attr)
                except AttributeError:
                    #print ("not found")
                    return keys  # too early: skip it

        if toadd:
            # this is specifically seeking modules by name (child name)
            # rather than walking the entire directory.  depth is set to 1
            # for this task.
            for childk in toadd:
                fullchildj = "%s.%s" % (startchildj, childk)
                mods, base = loader.gather_modules(fullchildj, depth=1,
                                                   recursive=False)
                cmods = mods.get(startchildj, {})
                for childk in cmods.keys():
                    if childk in keys:
                        continue
                    keys.add(childk)
                    loader.add_submodules(self.j, fullchildj, cmods[childk])
            return keys

        # global variant (no "toadd") - equivalent to dir-walking
        # starts at the parent, looking for everything.  it's quite
        # expensive, it basically has to do a depth=2 search.

        mods, base = loader.gather_modules(startchildj, depth=2)
        #print ("check mod cache mods", mods)
        #print ("check mod cache bas", base)

        # now check if the child modules found in the filesystem (across all
        # plugins) exist in the dir() listing, and if not, add it.
        # TODO: delay the actual adding until it's referenced?
        cmods = mods.get(startchildj, {})
        for childk in cmods.keys():
            if childk in keys:
                continue
            keys.add(childk)
            fullchildj = "%s.%s" % (startchildj, childk)
            loader.add_submodules(self.j, fullchildj, cmods[childk])

        self._child_mod_cache_checked = True
        return keys

    def _add_late_init(self, fn, *args, **kwargs):
        """ use this for when lazy-load needs to do some work
            after the constructor has been initialised.
            gets rid of potential side-effects.

            basically, if an __init__ is referencing j (or, now, self.j)
            then it should NOT be doing so (without a very good reason),
            as that creates a critical dependency.  use add_late_init
            instead.
        """
        assert self._late_init_called == False, "late init already called!"
        self._late_init_fns.append((fn, args, kwargs))

    def _call_late_inits(self):
        assert self._late_init_called == False, "late init already called!"
        self._late_init_called = True
        for (fn, args, kwargs) in self._late_init_fns:
            #print ("calling late init", self.__class__, fn, args, kwargs)
            fn(*args, *kwargs)

    def jget(self, attrname, start=None, end=None, stealth=False):
        """ gets an attribute in "j" format (dotted), walks down the
            object tree
        """
        return jwalk(self, attrname, start, end, stealth)

    @property
    def j(self):
        return global_j

    @j.setter
    def j(self, j_global_override):
        assert j_global_override is not None
        global global_j
        global_j = j_global_override

    @property
    def __name__(self):
        self.___name__ = str(self.__class__).split(".")[-1].split("'")[0]
        return self.___name__

    @property
    def logger(self):
        if self._logger is None:
            if '__jslocation__' in self.__dict__:
                name = self.__jslocation__
            else:
                name = self.__name__
            #print ("jsbase.logger get", type(self))
            self._logger = self.j.logging.get(name, force=self._logger_force)
            self._logger._parent = self
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def logger_enable(self):
        self._logger_force = True
        self._logger = None
        self.logger.level = 0

    @property
    def cache(self):
        if self._cache is None:
            id = self.__name__
            for item in [
                "instance",
                "_instance",
                "_id",
                "id",
                "name",
                    "_name"]:
                if item in self.__dict__ and self.__dict__[item]:
                    id += "_" + str(self.__dict__[item])
                    break
            self._cache = self.j.data.datacache.get(
                id, expiration=self._cache_expiration)
        return self._cache

    @cache.setter
    def cache(self, cache):
        self._cache = cache

    def _jsbase(self, jname, derived_classes=None, dynamicname=None,
                basej=None):
        """ dynamically creates a class which is derived from JSBase,
            that has the name "jname".  sets up a "super" caller
            (a dynamic __init__) that calls __init__ on the derived classes

            if the derived class list contains a string, see comments
            below: full path is created for importing of the format:
            Jumpscale.submod.submod.Module.CLASSNAME

            by default the class will be given the name "JSBased<jname>".
            to over-ride this, set dynamicname.
        """
        if basej is None:
            basej = self.j
        #print ("_jsbase", basej, jname, derived_classes)
        if derived_classes is None:
            derived_classes = []
        if self.__jsmodulepath__ and isinstance(jname, tuple):
            extrakls = resolve_klsmodule(self.__jsfullpath__,
                                      self.__jsmodulepath__, jname)
            #print ("resolved jname to", jname)
            derived_classes = [extrakls] + derived_classes
            jname = jname[0]
        for idx, kls in enumerate(derived_classes):
            nkls = lookup_kls(self.__jsfullpath__,
                             self.__jsmodulepath__, kls)
            derived_classes[idx] = nkls

        # check if the top derived class wants to have a different (extra)
        # base, and if so add it.
        firstkls = derived_classes[0]
        try:
            altbase = getattr(firstkls, '__jsbase__')
        except AttributeError:
            altbase = None
        classes = [JSBase]
        basekls = None
        if altbase:
            basekls = basej.jget(altbase)
            #print ("basekls", basekls)
            derived_classes = [firstkls, basekls] + derived_classes[1:]
        classes += copy(derived_classes)

        def initfn(self, *args, **kwargs):
            JSBase.__init__(self, _logger=basej and basej._logger or None)
            mro = inspect.getmro(self.__class__) # type(self).mro()
            #print ("baseinit", basej, self.__name__, args, kwargs)
            #print ("mro", type(self), inspect.getmro(self.__class__))
            for next_class in mro[1:]:  # slice to end
                #print ("kls", next_class.__name__)
                if hasattr(next_class, '__init__'):
                    #print ("calling", next_class.__name__)
                    if next_class.__name__ == 'BaseGetter':
                        continue
                    if next_class.__name__ == 'JSBase':
                        continue
                    else:
                        if basekls: # the extra class, call prior to next
                            basekls.__init__(self, *args, **kwargs)
                        next_class.__init__(self, *args, **kwargs)
                    break
            self._call_late_inits()
            #print ("dynamic init fn", self.__name__, self.__class__)
        inits = {'__init__': initfn}
        if derived_classes:
            # XXX have to have the first class be the Jumpscale one
            # e.g. derived_classes = [Jumpscale.core.Application.Application]
            inits['__jsbasekls__'] = firstkls

        if dynamicname is None:
            newname = "JSBased" + jname
        else:
            newname = dynamicname
        #print (newname, classes)
        memberkls = type(newname, tuple(classes), inits)
        return memberkls

    @staticmethod
    def _create_jsbase_instance(jname, basej=None, derived_classes=None):
        """ dynamically creates a class instance derived from JSBase,
        """
        if basej is None:
            basej = global_j
        assert basej is not None, "cannot create instance on empty global_j"
        memberkls = basej._jsbase(jname, derived_classes, basej=basej)
        instance = memberkls()
        return instance


# don't touch this directly - go through any instance of JSBase, assign self.j
# and it will get globally set.  generally not too good an idea to do that,
# though, as pretty much everything could break.
global_j = None
