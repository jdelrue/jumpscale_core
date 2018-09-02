from Jumpscale import j
from collections import OrderedDict

JSBASE = j.application.jsbase_get_class()

class _JSBaseClassConfig:

    def __init__(self, instance="main", data=None, parent=None,
                 template=None, ui=None,
                 interactive=False): # XXX issue #36, set to False (was True)
        if data is None: # issue #131 - REALLY important
            data = {}

        #print ("jsbaseclassconfig", self._template)
        if parent is not None:
            self.__jslocation__ = parent.__jslocation__
        self._single_item = True

        if ui is None:
            self._ui = self.j.tools.formbuilder.baseclass_get() # the default class
        else:
            self._ui = ui
        if template is not None:
            self._template = template
        if self._template is None:
            raise RuntimeError("template needs to be specified, "
                               "needs to be yaml or dict")
        self._config = None
        self._instance = instance
        self._parent = parent
        self.interactive = interactive and self.j.tools.configmanager.interactive

        self._config = self.j.tools.configmanager._get_for_obj(
            self, instance=self._instance, data=data,
            template=self._template, ui=self._ui)

        if self.config.new and data == {} and self.interactive:
            self.configure()
            self.config.error = False

        if self.config.error and self.interactive:
            self.configure()

    @property
    def logger(self):
        if self._logger is None:
            self._logger = self.j.logging.get(
                "%s.%s" %
                (self.__jslocation__,
                 self._instance),
                force=self._logger_force)
        return self._logger

    def reset(self):
        self.config.instance_set(self.instance)

    @property
    def config(self):
        if self._config is None:
            raise RuntimeError("self._config cannot be empty")
        return self._config

    @config.setter
    def config(self, val):
        self.config.data = val

    @property
    def instance(self):
        return self.config.instance

    @property
    def config_template(self):
        return self.config.template

    def configure(self):
        """
        call the form build to represent this object
        """
        if self._ui is None:
            raise RuntimeError(
                "cannot call configure UI because not defined yet, is None")

        template_sorted = sorted(self.config.template, key=str.casefold)
        template_ordered = OrderedDict()
        for k in template_sorted:
            template_ordered[k] = self.config.template[k]
        myui = self._ui(name=self.config.path,
                        config=self.config.data,
                        template=template_ordered)

        while True:
            myui.run()
            self.config.data = myui.config  # config in the ui is a std dict
            msg = self.config_check()
            if msg is not None and msg != "":
                self.logger.debug(msg)
                self.j.tools.console.askString("please correct the information in "
                                        "next configuraton screen, press enter")
            else:
                break

        self.config.save()

        return self.config

    def config_check(self):
        return None

    def __str__(self):
        out = "js_object:"
        out += str(self.config)
        return out

    __repr__ = __str__


class JSBaseClassConfig(JSBASE, _JSBaseClassConfig):

    def __init__(self, instance="main", data=None, parent=None,
                 template=None, ui=None,
                 interactive=False):
        JSBASE.__init__(self)
        _JSBaseClassConfig.__init__(self, instance, data, parent,
                 template, ui, interactive)
