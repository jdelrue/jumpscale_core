import os
from .core.JSBase import JSBase

if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:

    class Jumpscale(JSBase):

        def __init__(self):
            JSBase.__init__(self)
            self.exceptions = None

    def add_dynamic_instance(parent, child, module, kls):
        #print ("adding", parent, child, module, kls)
        if not parent:
            parent = j
        else:
            parent = getattr(j, parent)
        if kls:
            parent._add_instance(child, "Jumpscale." + module, kls, basej=j)
            #print ("added", parent, child)
        else:
            walkfrom = j
            for subname in module.split('.'):
                walkfrom = getattr(walkfrom, subname)
            setattr(parent, child, walkfrom)

    from .logging.LoggerFactory import LoggerFactory

    # LoggerFactory isn't instantiated from JSBase so there has to
    # be a little bit of a dance to get it established and pointing
    # to the right global j.  JSBase now contains a property "j"
    # which is actually a singleton (global), and LoggerFactory is
    # the ONLY class that's not fully aware of it... for now.
    l = LoggerFactory()

    #j = JSBase().j._create_jsbase_instance('Jumpscale')
    j = Jumpscale()
    j.j = j # sets up the global singleton
    add_dynamic_instance('', 'core', 'core', 'Core')
    add_dynamic_instance('', 'sal', 'sal', 'Sal')
    add_dynamic_instance('', 'data', 'data', 'Data')
    add_dynamic_instance('', 'tools', 'tools', 'Tools')
    add_dynamic_instance('', 'clients', 'clients', 'Clients')
    add_dynamic_instance('', 'portal', 'portal', 'Portal')
    add_dynamic_instance('', 'atyourservice', 'atyourservice', 'AtYourService')
    add_dynamic_instance('', 'sal_zos', 'sal_zos', 'SALZos')
    add_dynamic_instance('', 'data_units', 'data_units', 'DataUnits')
    j.logging = l # and the logging instance...
    l.j = j # ... which isn't aware of the JSBase j singleton sigh...

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

    j._profileStart = profileStart
    j._profileStop = profileStop

    class Empty():
        pass

    j.dirs = Empty()
    j.dirs.TMPDIR = "/tmp"

    # IF YOU WANT TO DEBUG THE STARTUP, YOU NEED TO CHANGE THIS ONE
    l.enabled = False
    l.filter = []  # default filter which captures all is *

    from .core.Application import Application
    j.application = Application(logging=l)
    j.core.application = j.application

    for (parent, child, module, kls) in [
        ('data', 'datacache', 'data.cache.Cache', 'Cache'),
        ('', 'cache', 'data.cache', None),
        ('data', 'text', 'data.text.Text', 'Text'),
        ('data', 'types', 'data.types.Types', 'Types'),
        ('data', 'regex', 'data.regex.RegexTools', 'RegexTools'),
        ('sal', 'fs', 'fs.SystemFS', 'SystemFS'),
        ('sal', 'process', 'sal.process.SystemProcess', 'SystemProcess'),
        ('data', 'kvs', 'data.key_value_store.StoreFactory', 'StoreFactory'),
        ('data', 'time', 'data.time.Time', 'Time_'),
        ('data', 'memqueue', 'data.queue.MemQueue', 'MemQueueFactory'),
        ('clients', 'redis', 'clients.redis.RedisFactory', 'RedisFactory'),
        ('tools', 'executorLocal', 'tools.executor.ExecutorLocal',
                                    'ExecutorLocal'),
        ('core', 'platformtype', 'core.PlatformTypes', 'PlatformTypes'),
        ('core', 'state', 'tools.executorLocal.state', None),
        ('', 'dirs', 'core.Dirs', 'Dirs'),
        ('core', 'dirs', 'dirs', None),
        ('data', 'idgenerator', 'data.idgenerator.IDGenerator', 'IDGenerator'),
        ('', 'errorhandler', 'errorhandling.ErrorHandler', 'ErrorHandler'),
        ('core', 'errorhandler', 'errorhandler', None),
        ('sal', 'fswalker', 'fs.SystemFSWalker', 'SystemFSWalker'),
        ('tools', 'jsloader', 'tools.loader.JSLoader', 'JSLoader'),
        ('tools', 'tmux', 'tools.tmux.Tmux', 'Tmux'),
        ('tools', 'path', 'tools.path.PathFactory', 'PathFactory'),
        ('tools', 'console', 'tools.console.Console', 'Console'),
        ('data', 'serializers', 'data.serializers.SerializersFactory',
                                'SerializersFactory'),
        ('clients', 'git ', 'clients.git.GitFactory', 'GitFactory'),
        ('tools', 'formbuilder', 'tools.formbuilder.FormBuilder',
                                        'FormBuilderFactory'),
        ('tools', 'configmanager', 'tools.configmanager.ConfigManager',
                                        'ConfigFactory'),
        ('clients', 'sshkey', 'clients.sshkey.SSHKeys', 'SSHKeys'),
        ('data', 'nacl', 'data.nacl.NACLFactory', 'NACLFactory'),
        ('data', 'hash', 'data.hash.HashTool', 'HashTool'),
        ('tools', 'myconfig', 'tools.myconfig.MyConfig', 'MyConfig'),
        ]:
        add_dynamic_instance(parent, child, module, kls)

    #print (j.core, dir(j.core))
    # check that locally init has been done
    j.tools.executorLocal.env_check_init()

    from Jumpscale.errorhandling import JSExceptions
    j.exceptions = JSExceptions

    j.logging.init()  # will reconfigure the logging to use the config file

