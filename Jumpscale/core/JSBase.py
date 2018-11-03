from Jumpscale import j
import os
import inspect
import os

class JSBase:

    __dirpath = ""
    _logger = None
    _location = None
    _cache_expiration = 3600
    _classname = None

    def __init__(self):
        self._cache = None


    @property
    def _dirpath(self):
        if self.__class__.__dirpath =="":
            self.__class__.__dirpath = os.path.dirname(inspect.getfile(self.__class__))
        return self.__class__.__dirpath

    @property
    def __name__(self):
        if self.__class__._classname is None:
            self.__class__._classname = j.core.text.strip_to_ascii_dense(str(self.__class__))
        return self.__class__._classname

    @property
    def __location__(self):
        if self.__class__._location is None:
            if '__jslocation__' in self.__dict__:
                self.__class__._location = self.__jslocation__
            elif '__jscorelocation__' in self.__dict__:
                self.__class__._location = self.__jslocation__
            else:
                self.__class__._location = self.__name__
        return self.__class__._location


    def _example_run(self,filepath="example",obj_key="main",**kwargs):
        """
        the example file will be copied to $VARDIR/CODEGEN/$uniquekey and executed there
        template engine jinja is used to apply kwargs onto this file

        :param filepath: name of file to execute can be e.g. example.py or example or examples/example1.py
                        is always relative to the file you call this function from
        :param kwargs: the arguments which will be given to the template engine
        :param obj_key: is the name of the function we will look for to execute, cannot have arguments
               to pass arguments to the example script, use the templating feature

        :return: result = is the result of the method called

        """
        print ("##: EXAMPLE RUN")
        tpath = "%s/%s"%(self._dirpath,filepath)
        tpath = tpath.replace("//","/")
        if not tpath.endswith(".py"):
            tpath+=".py"
        print ("##: path: %s\n\n" % tpath)
        method = j.tools.jinja2.code_python_render(obj_key=obj_key, path=tpath,**kwargs)
        res = method()
        return res

    @property
    def logger(self):
        if self.__class__._logger is None:
            self.__class__._logger = j.logger.get(self.__location__)
            self.__class__._logger._parent = self
        return self.__class__._logger

    @logger.setter
    def logger(self, logger):
        self.__class__._logger = logger

    def logger_enable(self):
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
