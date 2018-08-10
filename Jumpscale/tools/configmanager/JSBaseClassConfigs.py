from inspect import isclass
from Jumpscale import j # required because jumpscale.py doesn't exist at setup

JSBASE = j.application.jsbase_get_class()


class JSBaseClassConfigs(JSBASE):
    """
    collection class to deal with multiple instances
    """

    def __init__(self, child_class, single_item=False):
        """
        @param child_class: The class that this factory will create
        @param single_item: In the case this factory will only ever return the same instance
                            set single_item to True
        """
        if not isclass(child_class):
            raise TypeError("child_class need to be a class not %s" %
                            type(child_class))

        self._single_item = single_item
        self._child_class = child_class

        JSBASE.__init__(self)

        # self.getall()

    def get(
            self,
            instance="main",
            data={},
            create=True,
            die=True,
            interactive=True,
            **kwargs):
        """
        Get an instance of the child_class set in the constructor

        @param instance: instance name to get. If an instance is already loaded in memory, return it
        @data data: dictionary of data use to configure the instance
        @PARAM interactive means that the config will be shown to user when new and user needs to accept
        """
        if not create and instance not in self.list():
            if die:
                raise RuntimeError("could not find instance:%s" % (instance))
            else:
                return None

        return self._child_class(
            instance=instance,
            data=data,
            parent=self,
            interactive=interactive,
            **kwargs)

    def exists(self, instance):
        return instance in self.list()

    def new(self, instance, data={}):
        return self.get(instance=instance, data=data, create=True)

    def reset(self):
        j.tools.configmanager.delete(
            location=self.__jslocation__, instance="*")
        self.getall()

    def delete(self, instance="", prefix=""):
        if prefix != "":
            for item in self.list(prefix=prefix):
                self.delete(instance=item)
            return
        j.tools.configmanager.delete(
            location=self.__jslocation__, instance=instance)

    def count(self):
        return len(self.list())

    def list(self, prefix=""):
        res = []
        for item in j.tools.configmanager.list(location=self.__jslocation__):
            if prefix != "":
                if item.startswith(prefix):
                    res.append(item)
            else:
                res.append(item)
        return res

    def getall(self):
        res = []
        for name in j.tools.configmanager.list(location=self.__jslocation__):
            res.append(self.get(name, create=False))
        return res
