import os
import socket
from .core.JSBase import JSBase

def tcpPortConnectionTest(ipaddr, port, timeout=None):
    conn = None
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout:
            conn.settimeout(timeout)
        try:
            conn.connect((ipaddr, port))
        except BaseException:
            return False
    finally:
        if conn:
            conn.close()
    return True


if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:
    class SALZos(JSBase):
        pass

    class Core(JSBase):
        def __init__(self):
            JSBase.__init__(self)
            self._db = None

        @property
        def db(self):
            if not self._db:
                if tcpPortConnectionTest("localhost", 6379):
                    # print("CORE_REDIS")
                    self._db = j.clients.redis.core_get()
                else:
                    # print("CORE_MEMREDIS")
                    import fakeredis
                    self._db = fakeredis.FakeStrictRedis()
            return self._db

        def db_reset(self):
            j.data.cache._cache = {}
            self._db = None

    class DataUnits(JSBase):
        pass

    class Jumpscale(JSBase):

        def __init__(self):
            JSBase.__init__(self)
            for name in ['Tools', 'Sal', 'Data', 'Clients', 'Servers',
                         'Portal', 'AtYourService']:
                instancename = name.lower()
                instance = self._create_jsbase_instance(name)
                setattr(self, instancename, instance)
            self.core = Core()
            self.sal_zos = SALZos()
            self.data_units = DataUnits()
            self.exceptions = None

    from .logging.LoggerFactory import LoggerFactory

    # LoggerFactory isn't instantiated from JSBase so there has to
    # be a little bit of a dance to get it established and pointing
    # to the right global j.  JSBase now contains a property "j"
    # which is actually a singleton (global), and LoggerFactory is
    # the ONLY class that's not fully aware of it... for now.
    l = LoggerFactory()

    j = Jumpscale()
    j.j = j # sets up the global singleton
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

    # hmmm property cache in JSBase interfering *sigh*...
    from .data.cache.Cache import Cache
    j.data.cache = Cache()

    def add_dynamic_instance(parent, child, module, kls):
        #print ("adding", parent, child, module, kls)
        if not parent:
            parent = j
        else:
            parent = getattr(j, parent)
        if kls:
            parent._add_instance(child, "Jumpscale." + module, kls)
            #print ("added", parent, child)
        else:
            walkfrom = j
            for subname in module.split('.'):
                walkfrom = getattr(walkfrom, subname)
            setattr(parent, child, walkfrom)

    for (parent, child, module, kls) in [
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
        ('core', 'dirs', 'dirs', None)
        ]:
        add_dynamic_instance(parent, child, module, kls)

    # check that locally init has been done
    j.tools.executorLocal.env_check_init()

    for (parent, child, module, kls) in [
        ('data', 'idgenerator', 'data.idgenerator.IDGenerator', 'IDGenerator'),
        ('', 'errorhandler', 'errorhandling.ErrorHandler', 'ErrorHandler'),
        ('core', 'errorhandler', 'errorhandler', None),
        ('sal', 'fswalker', 'fs.SystemFSWalker', 'SystemFSWalker'),
        ('tools', 'jsloader', 'tools.loader.JSLoader', 'JSLoader'),
        ('tools', 'tmux', 'tools.tmux.Tmux', 'Tmux'),
        ('tools', 'path', 'tools.path.PathFactory', 'PathFactory'),
        ('tools', 'console', 'tools.console.Console', 'Console'),
        ]:
        add_dynamic_instance(parent, child, module, kls)

    from Jumpscale.errorhandling import JSExceptions

    j.exceptions = JSExceptions

    j.logging.init()  # will reconfigure the logging to use the config file

    for (parent, child, module, kls) in [
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

    print (j.__subgetters__)
    print (j.data.__subgetters__)
