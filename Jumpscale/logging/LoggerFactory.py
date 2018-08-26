import logging
import os
import sys
import time

class LoggerFactory():

    __jslocation__ = "j.core.logging"

    def __init__(self, j=None):
        """ WARNING: JSBase now contains a singleton (global) j and
            LoggerFactory can't get at it.

            WARNING: self.j must be patched afterwards to point to
            an updated j. JSLogger instances will happily refer back
            to the LoggerFactory that contains them, however for now,
            because LoggerFactory is not derived from JSBase, it can't
            get the global j singleton.
        """
        if j is not None:
            self.j = j # must patch this after instantiation to break loop
        self.logger_name = 'j'
        self._handlers = None
        self.loggers = {}
        self.exclude = []

        self._logger = None # JSBase sets this as well
        self.__default = None

        self.JSLogger = self._jsbase(('JSLogger',
                           'Jumpscale.logging.JSLogger'))
        self.enabled = True
        self.filter = ["*"]  # default filter to see which loggers will
                             # be attached needs to have * or j.sal... inside

        # self.logger.debug("started logger factory")

    @property
    def handlers(self):
        if self._handlers is None:
            self.Handlers = self._jsbase(('Handlers',
                               'Jumpscale.logging.Handlers'))
            self._handlers = self.Handlers()
        return self._handlers

    @property
    def logger(self): # JSBase still has a logger property setter
        if self._logger is None:
            self._logger = self.JSLogger("logger", self)
            self._logger.addHandler(self.handlers.consoleHandler)
        return self._logger

    @property
    def _default(self):
        if self.__default is None:
            self.JSLoggerDefault = self._jsbase(('JSLoggerDefault',
                               'Jumpscale.logging.JSLoggerDefault'))
            self.__default = self.JSLoggerDefault("default", self)
        return self.__default

    def _getName(self, name):

        name = name.strip().lower()

        if name == "":
            path, ln, name, info = logging.root.findCaller()
            if path.startswith(self.j.dirs.LIBDIR):
                path = path.lstrip(self.j.dirs.LIBDIR)
                name = path.replace(os.sep, '.')

        if not name.startswith(self.logger_name):
            name = "%s.%s" % (self.logger_name, name)

        if len(name) > 22:
            name = name[-22:]

        return name

    def get(self, name="", force=False):  # -> JSLogger:
        """
        Return a logger with the given name. Name will be prepend with
        'j.' so every logger returned by this function is a child of the
        jumpscale root logger 'j'

        """
        name = self._getName(name)

        def check_(name):
            # print("check %s"%name)
            for item in self.exclude:
                # print("check exclude:%s"%item)
                if item == "*":
                    # print("exclude %s:%s" % (item, name))
                    return False
                if name.find(item) != -1:
                    # print("exclude %s:%s" % (item, name))
                    return False
            for item in self.filter:
                # print("check include:%s"%item)
                if item == "*":
                    # print("include: %s:%s" % (item, name))
                    return True
                if name.find(item) != -1:
                    # print("include: %s:%s" % (item, name))
                    return True
            return False

        if force == False and self.enabled is False:
            self.loggers[name] = self._default
            # print("DEFAULT LOGGER (disabledlogger):%s" % name)
        else:
            if force or check_(name):
                # print("JSLOGGER:%s" % name)
                # logger = logging.getLogger(name)
                logger = self.JSLogger(name, self)
                logger.level = self.j.core.state.configGetFromDict(
                                            "logging","level", logging.DEBUG)

                for handler in self.handlers._all:
                    logger.handlers = []
                    logger.addHandler(handler)

                self.loggers[name] = logger
            else:
                # print("DEFAULT LOGGER:%s" % name)
                self.loggers[name] = self._default

        return self.loggers[name]

    def disable(self):
        """ will transform all loggers to empty loggers which only act
            on errors, but ignore logs
        """
        if self.enabled:
            self.enabled = False
            self.filter = []

            # for key, logger in self.loggers.items():
            #     # print("disable logger: %s"%key)
            #     logger.setLevel(20)
            self.j.application.debug = False

            self.logger_filters_add()

    def enable(self):
        """
        """
        if self.enabled is False:
            self.enabled = True
            self.filter = []
            self.init()

    # def set_quiet(self, quiet):
    #     self._quiet = quiet

    # def set_mode(self, mode):
    #     if isinstance(mode, str):
    #         if mode in _name_to_mode:
    #             mode = _name_to_mode[mode]
    #         else:
    #             raise j.exceptions.Input("mode %s doesn't exist" % mode)

    #     if mode == self.PRODUCTION:
    #         self._enable_production_mode()
    #     elif mode == self.DEV:
    #         self._enable_dev_mode()

    # def set_level(self, level=10):
    #     """
    #     Set logging levels on all loggers and handlers
    #     Added to support backward compatability
    #     """
    #     self.loggers_level_set(level=level)

    def handlers_level_set(self, level=10):
        """

        sets level in all handlers

        10=debug
        20=info

        info see:
        https://docs.python.org/3/library/logging.html#levels

        """
        for handler in self.handlers._all:
            handler.setLevel(level)

    def loggers_level_set(self, level='DEBUG'):
        """

        sets level in all handlers & loggers

        10=debug
        20=info

        info see:
        https://docs.python.org/3/library/logging.html#levels

        """
        for key, logger in self.loggers.items():
            logger.setLevel(level)
        self.handlers_level_set(level)

    def handlers_attach(self):
        """
        walk over all loggers, attach the handlers
        """
        for key, logger in self.loggers.items():
            for handler in self.handlers._all:
                logger.handlers = []
                logger.addHandler(handler)

    def memhandler_enable(self):
        # self.logger.propagate = True
        self.logger.addHandler(self.handlers.memoryHandler)

    def consolehandler_enable(self):
        # self.logger.propagate = True
        self.logger.addHandler(self.handlers.consoleHandler)

    def telegramhandler_enable(self, client, chat_id):
        """
        Enable a telegram handler to forward logs to a telegram group.
        @param client: A jumpscale telegram_bot client
        @param chat_id: Telegram chat id to which logs need to be forwarded
        """
        self.logger.addHandler(self.handlers.telegramHandler(client, chat_id))

    def handlers_reset(self):
        self.logger.handlers = []

    def logger_filters_get(self):
        return self.j.core.state.config_js["logging"]["filter"]

    def logger_filters_add(self, items=[], exclude=[], level=10, save=False):
        """
        items is list or string e.g. prefab, exec
        will add the filters to the logger and save it in the config file

        """
        items = self.j.data.types.list.fromString(items)
        exclude = self.j.data.types.list.fromString(exclude)
        if save:
            new = False
            logging = self.j.core.state.config_js["logging"]
            for item in items:
                if item not in logging["filter"]:
                    logging["filter"].append(item)
                    new = True
            for item in exclude:
                if item not in logging["exclude"]:
                    logging["exclude"].append(item)
                    new = True
            if new:
                self.j.core.state.configSave()
                self.init()

        for item in items:
            item = item.strip().lower()
            if item not in self.filter:
                self.filter.append(item)

        for item in exclude:
            item = item.strip().lower()
            if item not in self.exclude:
                self.exclude.append(item)

        self.logger.debug("start re-init for logging")

        self.handlers_level_set(level)

        # make sure all loggers are empty again
        self.j.dirs._logger = None
        self.j.core.platformtype._logger = None
        self.j.core.state._logger = None
        self.j.core.dirs._logger = None
        self.j.core.application._logger = None
        for cat in [self.j.data, self.j.clients, self.j.tools, self.j.sal]:
            for key, item in cat.__dict__.items():
                if item is not None:
                    # if hasattr(item, '__jslocation__'):
                    #     print (item.__jslocation__)
                    if not hasattr(item, '__dict__'):
                        continue
                    if 'logger' in item.__dict__:
                        item.__dict__["logger"] = self.get(item.__jslocation__)
                    item._logger = None
        self.loggers = {}

        # print(self.j.tools.jsloader._logger)
        # print(self.j.tools.jsloader.logger)

    def init(self):
        """
        get info from config file & make sure all logging is done properly
        """
        self.enabled = self.j.core.state.configGetFromDict("logging",
                                                    "enabled", True)
        level = self.j.core.state.configGetFromDict("logging", "level", 'DEBUG')
        self.loggers_level_set(level)
        self.handlers_level_set(level)
        self.filter = []
        self.loggers = {}
        items = self.j.core.state.configGetFromDict("logging", "filter", [])
        exclude = self.j.core.state.configGetFromDict("logging", "exclude", [])
        self.logger_filters_add(items=items, exclude=exclude, save=False)

    # def enableConsoleMemHandler(self):
    #     self.logger.handlers = []
    #     # self.logger.propagate = True
    #     self.logger.addHandler(self.handlers.memoryHandler)
    #     self.logger.addHandler(self.handlers.consoleHandler)

    # def _enable_production_mode(self):
    #     self.logger.handlers = []
    #     self.logger.addHandler(logging.NullHandler())
    #     # self.logger.propagate = True

    # def _enable_dev_mode(self):
    #     logging.setLoggerClass(JSLogger)
    #     self.logger.setLevel(logging.DEBUG)
    #     self.logger.propagate = False
    #     logging.lastResort = None
    #     self.enableConsoleHandler()
    #     self.logger.addHandler(self.handlers.fileRotateHandler)

    def test(self):
        """
        js_shell 'j.logging.test()'
        """


        self.handlers_reset()
        self.memhandler_enable()

        logger = self.get("loggerTest")

        logger.info("a test")

        def perftest(logger):
            print("start perftest logger")
            start = time.time()
            nr = 30000
            for i in range(nr):
                logger.info("this is an info message")
                # self.getActionObjFromMethod(test)
            stop = time.time()
            print("nr of logs per sec:%s" % int(nr / (stop - start)))

        perftest(logger)

