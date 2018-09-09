from Jumpscale import j
import os

class JSBase:

    def __init__(self):
        self._logger = None
        self._cache = None
        self._classname = None
        self._cache_expiration = 3600
        self._logger_force = False

        if "_location" not in self.__dict__:
            self._location=None

    @property
    def __name__(self):
        if self._classname is None:
            self._classname = j.core.text.strip_to_ascii_dense(str(self.__class__))
        return self._classname

    @property
    def __location__(self):
        if self._location is None:
            if '__jslocation__' in self.__dict__:
                self._location = self.__jslocation__
            elif '__jscorelocation__' in self.__dict__:
                self._location = self.__jslocation__
            else:
                self._location = self.__name__
        return self._location



    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get(self.__location__, force=self._logger_force)
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
            id = self.__location__
            for item in ["instance", "_instance", "_id", "id", "name", "_name"]:
                if item in self.__dict__ and self.__dict__[item]:
                    id += "_" + str(self.__dict__[item])
                    break
            self._cache = j.core.cache.get(id, expiration=self._cache_expiration)
        return self._cache
