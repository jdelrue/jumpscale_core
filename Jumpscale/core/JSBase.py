from Jumpscale import j
import os
import importlib


class BaseGetter(object):
    """ this is a rather.. um... ugly class that has a list of module names
        added to it, where if a property is ever referred to it will either
        import a class instance in that module on-demand or return a
        previously-instantiated instance.

        example: /opt/code/github/threefold/jumpscale_core/... RedisFactory.py
        and a class named RedisFactory, and an instance name "redis",
        if ever Basegetter.redis is referred to, you get a RedisFactory()
        instantiated and returned

        at the moment the import is done using importlib.import_module()
        however see 32.5.7.5 https://docs.python.org/3/library/importlib.html
        really we should be *explicitly* importing from the exact location
        required / requested, using a modified variant of the code shown
        there.

        the problem at the moment is that the code below (found on
        stackoverflow) doesn't deal with relative imports: parent
        has to be set (and loaded prior to the child... and all the
        way down), so it gets... compplicated.

        import_module, although it will go searching in /usr/local/
        etc. etc. will do the job for now
        """

    def __init__(self):
        self.__subgetters__ = {}

    def _add_instance(self, subname, modulepath, objectname):
        """ adds an instance to the dictionary, for when
            __getattribute__ is called, the instance will be loaded
        """
        #print ("add instance", self, subname, modulepath, objectname)
        ms = ModuleSetup(subname, modulepath, objectname)
        #print (dir(self))
        d = object.__getattribute__(self, '__subgetters__')
        d[subname] = ms

    def __getattribute__(self, name):
        if name == 'JSBASE':
            return JSBase
        if name in dir(JSBase):
            return object.__getattribute__(self, name)
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        d = object.__getattribute__(self, '__subgetters__')
        if name in d:
            return d[name].getter()
        return object.__getattribute__(self, name)
        raise AttributeError(name)


class ModuleSetup(object):
    def __init__(self, subname, modulepath, objectname):
        self.subname = subname
        self.modulepath = modulepath
        self.objectname = objectname
        self._obj = None

    def getter(self):
        if self._obj is None:
            #print ("about to get modulepath %s object %s" % \
            #        (self.modulepath, self.objectname))

            imp = importlib.import_module(self.modulepath)

            #spec = importlib.util.spec_from_file_location(self.objectname,
            #                                        self.modulepath)
            #imp = importlib.util.module_from_spec(spec)
            #spec.loader.exec_module(imp)
            #print ("about to get modulepath %s object %s" % \
            #        (self.modulepath, self.objectname))
            self._obj = getattr(imp, self.objectname)()
        return self._obj


class JSBase(BaseGetter):

    def __init__(self):
        BaseGetter.__init__(self)
        self._logger = None
        self._cache = None
        self._cache_expiration = 3600
        self._logger_force = False

    @property
    def j(self):
        return global_j

    @j.setter
    def j(self, j_global_override):
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
            self._logger = j.logger.get(name, force=self._logger_force)
            self._logger._parent = self
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def logger_enable(self):
        self._logger_force = True
        self._logger = None
        self.logger.level = 20

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
            self._cache = j.data.cache.get(
                id, expiration=self._cache_expiration)
        return self._cache

    @staticmethod
    def _create_jsbase_instance(jname):
        """ dynamically creates a class which is derived from JSBase,
            that has the name "jname"
        """
        memberkls = type(jname, (JSBase, ), {})
        return memberkls()

# don't touch this directly - go through any instance of JSBase, assign self.j
# and it will get globally set.
global_j = JSBase()
