from Jumpscale import j
import os


class JSBase(object):

    def __init__(self):
        self._logger = None
        self._cache = None
        self._cache_expiration = 3600
        self._logger_force = False

    @property
    def j(self):
        return global_j

    @j.setter
    def j(self, j_global_override):
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

# don't touch this directly - go through any instance of JSBase, assign self.j
# and it will get globally set.
global_j = JSBase()
