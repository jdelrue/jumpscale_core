import os
import socket


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
    class Sal():
        def __init__(self):
            pass

    class SALZos():
        def __init__(self):
            pass

    class Tools():
        def __init__(self):
            pass

    class Data():
        def __init__(self):
            pass

    class Clients():
        def __init__(self):
            pass

    class Core():
        def __init__(self):
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

    class Servers():
        def __init__(self):
            pass

    class DataUnits():
        def __init__(self):
            pass

    class Portal():
        def __init__(self):
            pass

    class AtYourService():
        def __init__(self):
            pass

    class Jumpscale():

        def __init__(self):
            self.tools = Tools()
            self.sal = Sal()
            self.sal_zos = SALZos()
            self.data = Data()
            self.clients = Clients()
            self.core = Core()
            self.servers = Servers()
            self.data_units = DataUnits()
            self.portal = Portal()
            self.atyourservice = AtYourService()
            self.exceptions = None

    j = Jumpscale()

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

    from .logging.LoggerFactory import LoggerFactory

    j.logger = LoggerFactory()

    # IF YOU WANT TO DEBUG THE STARTUP, YOU NEED TO CHANGE THIS ONE
    j.logger.enabled = False
    j.logger.filter = []  # default filter which captures all is *

    from .core.Application import Application
    j.application = Application()
    j.core.application = j.application

    from .data.text.Text import Text

    j.data.text = Text()

    from .data.types.Types import Types

    j.data.types = Types()

    from .data.regex.RegexTools import RegexTools

    j.data.regex = RegexTools()

    from .fs.SystemFS import SystemFS

    j.sal.fs = SystemFS()

    from .sal.process.SystemProcess import SystemProcess

    j.sal.process = SystemProcess()

    from .data.key_value_store.StoreFactory import StoreFactory

    j.data.kvs = StoreFactory()

    from .data.time.Time import Time_

    j.data.time = Time_()

    from .data.cache.Cache import Cache

    j.data.cache = Cache()

    from .data.queue.MemQueue import MemQueueFactory

    j.data.memqueue = MemQueueFactory()

    from .clients.redis.RedisFactory import RedisFactory

    j.clients.redis = RedisFactory()

    from .tools.executor.ExecutorLocal import ExecutorLocal

    j.tools.executorLocal = ExecutorLocal()  # needed in platformtypes

    from .core.PlatformTypes import PlatformTypes

    j.core.platformtype = PlatformTypes()

    j.core.state = j.tools.executorLocal.state

    # check that locally init has been done
    j.tools.executorLocal.env_check_init()

    from .core.Dirs import Dirs

    j.dirs = Dirs()
    j.core.dirs = j.dirs

    from .data.idgenerator.IDGenerator import IDGenerator

    j.data.idgenerator = IDGenerator()

    from .errorhandling.ErrorHandler import ErrorHandler

    j.errorhandler = ErrorHandler()

    j.core.errorhandler = j.errorhandler

    from .fs.SystemFSWalker import SystemFSWalker

    j.sal.fswalker = SystemFSWalker

    from .tools.loader.JSLoader import JSLoader

    j.tools.jsloader = JSLoader()

    from .tools.tmux.Tmux import Tmux

    j.tools.tmux = Tmux()

    # from .clients.git.GitFactory import GitFactory

    # j.clients.git = GitFactory()

    from .tools.path.PathFactory import PathFactory

    j.tools.path = PathFactory()

    from .tools.console.Console import Console

    j.tools.console = Console()

    from Jumpscale.errorhandling import JSExceptions

    j.exceptions = JSExceptions

    j.logger.init()  # will reconfigure the logging to use the config file

    from .data.serializers.SerializersFactory import SerializersFactory
    j.data.serializers = SerializersFactory()

    from .clients.git.GitFactory import GitFactory
    j.clients.git = GitFactory()

    from .tools.formbuilder.FormBuilder import FormBuilderFactory
    j.tools.formbuilder = FormBuilderFactory()  # needed in ConfigManager

    from .tools.formbuilder.FormBuilder import FormBuilderFactory
    j.tools.formbuilder = FormBuilderFactory()  # needed in ConfigManager

    from .tools.configmanager.ConfigManager import ConfigFactory
    j.tools.configmanager = ConfigFactory()  # needed in platformtypes

    from .clients.sshkey.SSHKeys import SSHKeys
    j.clients.sshkey = SSHKeys()

