import os

from .core.JSBase import JSBase, global_j
from .tools.jsloader.JSLoader import add_dynamic_instance

def profileStart():
    import cProfile
    pr = cProfile.Profile()
    pr.enable()
    return pr

def profileStop(pr):
    pr.disable()
    import io
    import pstats
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

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
('core', 'exceptions', 'errorhandler.JSExceptions',
                        'JSExceptions'),
('', 'dirs', 'core.Dirs', 'Dirs'),
('core', 'platformtype', 'core.PlatformTypes', 'PlatformTypes'),
# needed in cases where config file doesn't exist
('sal', 'process', 'sal.process.SystemProcess', 'SystemProcess'),
('', 'application', 'core.application', None),
('', 'cache', 'data.cache', None),
#('core', 'state', 'tools.executorLocal.state', None),
('core', 'dirs', 'dirs', None),
('', 'errorhandler', 'core.errorhandler', None),
('', 'exceptions', 'core.exceptions', None),
('', 'errorhandler.exceptions', 'exceptions', None),
# annoyingly needed due to name confusion (not for bootstrap)
('data', 'serializers', 'data.serializers.SerializersFactory',
                        'SerializersFactory'),
('data', 'serializer', 'data.serializers', None),
]

class Jumpscale(JSBase): # deliberately deriving from JSBase

    __jslocation__ = "j"

    _profileStart = profileStart
    _profileStop = profileStop

    def __init__(self, logging_enabled=False, filter=None, config_dir=None):
        JSBase.__init__(self)
        self._shell = None
        self.bootstrap(logging_enabled, filter, config_dir)

    def shell(self,name="",loc=True):
        """ runs an embedded IPython shell - do not use remotely
            (rpyc) as the terminal (stdout.isatty()) will fail.
        """
        if self._shell == None:
            from IPython.terminal.embed import InteractiveShellEmbed
            if name is not "":
                name = "SHELL:%s" % name
            self._shell = InteractiveShellEmbed(banner1= name, exit_msg="")
        if loc:
            import inspect
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            f = calframe[1]
            print("\n*** file: %s"%f.filename)
            print("*** function: %s [linenr:%s]\n" % (f.function,f.lineno))
        return self._shell(stack_depth=2)

    def bootstrap(self, logging_enabled=False, filter=None,
                        config_dir=None):
        """ bootstraps a new jumpscale object: over-rides the global
            "j" so use with care.  config_dir sets the config directory:
            the default is usually ~/jumpscale/cfg and can be over-ridden
            with $HOSTCFGDIR environment variable.
        """

        # LoggerFactory isn't instantiated from JSBase so there has to
        # be a little bit of a dance to get it established and pointing
        # to the right global j.  JSBase now contains a property "j"
        # which is actually a singleton (global)

        if config_dir:
            os.environ['HOSTCFGDIR'] = config_dir

        #print ("toplevelpth", top_level_path)

        plugin_path = os.path.abspath(__file__)
        #plugin_path = os.path.dirname(plugin_path)

        self.__jsfullpath__ = os.path.join(plugin_path, "Jumpscale.py")
        self.__jsmodulepath__ = 'Jumpscale'
        self.__jsmodbase__ = {}
        self.__jsmodlookup__ = {}
        self.j = self  # sets up the global singleton
        self.j.__dynamic_ready__ = False  # set global dynamic loading OFF

        DLoggerFactory = self._jsbase(
            ('LoggerFactory', 'Jumpscale.logging.LoggerFactory'),
            basej=self)
        l = DLoggerFactory()
        l.enabled = logging_enabled
        l.filter = filter or []  # default filter which captures all is *
        self.logging = l

        for (parent, child, module, kls) in bootstrap:
            add_dynamic_instance(self, parent, child, module, kls)

        # initialise
        self.tools.executorLocal.env_check_init()  # no config: make one!
        self.dirs.reload()  # ... directories got recreated (possibly)
        # will reconfigure the logging to use the config file
        self.logging.init()

        # now load the json files
        loader = self.tools.jsloader
        loader.load_json()
        for pluginname, (modlist, baselist) in self.__jsmodbase__.items():
            #print (pluginname, modlist.keys())
            loader._dynamic_merge(self, modlist, baselist, {})

        # now finally set dynamic on.  if the json loader was empty
        # or if ever something is requested that's not *in* the json
        # file, dynamic checking kicks in.
        self.__dynamic_ready__ = True  # set global dynamic loading ON

        # used fake redis up to now: move to real redis (if it exists)
        self.core.db_reset()

if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:

    # slightly hacky (invisible) way to add a -c/--config option
    # which (because of add_help=False and del on the help action)
    # doesn't cause an exit (right here) if ANOTHER argparse happens
    # to be called (later) with more arguments.

    # hacking things in here avoids the need to have to add "-c" to
    # absolutely every single one of the core9/cmd/js_* commands.
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-c', '--config', default=None,
                        help="Config Directory Name")
    del parser._registries['action']['help'] # remove help action (stops exit)
    options, args = parser.parse_known_args()


    if global_j is None:
        j = Jumpscale(config_dir=options.config)
    else:
        j = global_j
