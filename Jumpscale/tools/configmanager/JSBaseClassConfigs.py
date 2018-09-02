from inspect import isclass
from Jumpscale import j # required because jumpscale.py doesn't exist at setup

JSBASE = j.application.jsbase_get_class()


class _JSBaseClassConfigs:
    """ collection class to deal with multiple instances
    """

    # XXX don't add __jslocation__ it recursively loads configs
    # and things get very confuUuused...
    # __jslocation__ = 'j.tools.configmanager.base_class_configs'

    def __init__(self, child_class=None, single_item=False):
        """
        @param child_class: The class that this factory will create
        @param single_item: In the case this factory will only ever return the same instance
                            set single_item to True
        """
        if child_class is not None:
            self._child_class = child_class
        #print ("JSBaseClassConfigs", self, self._child_class)

        if not isclass(self._child_class):
            raise TypeError("child_class need to be a class not %s" %
                            type(self._child_class))

        self._single_item = single_item

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
        self.j.tools.configmanager.delete(location=self.__jslocation__, instance="*")
        self.getall()

    def delete(self, instance="", prefix=""):
        if prefix != "":
            for item in self.list(prefix=prefix):
                self.delete(instance=item)
            return
        self.j.tools.configmanager.delete(location=self.__jslocation__,
                                     instance=instance)

    def count(self):
        return len(self.list())

    def list(self, prefix=""):
        res = []
        for item in self.j.tools.configmanager.list(location=self.__jslocation__):
            if prefix != "":
                if item.startswith(prefix):
                    res.append(item)
            else:
                res.append(item)
        return res

    def getall(self):
        res = []
        for name in self.j.tools.configmanager.list(location=self.__jslocation__):
            res.append(self.get(name, create=False))
        return res

class JSBaseClassConfigs(JSBASE, _JSBaseClassConfigs):
    def __init__(self, child_class=None, single_item=False):
        JSBASE.__init__(self)
        _JSBaseClassConfigs.__init__(self, child_class, single_item)
