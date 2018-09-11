import os
import socket
import pytoml
import sys
os.environ["LC_ALL"]='en_US.UTF-8'

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


class Core():
    def __init__(self,j):
        self._db = None
        self._dir_home = None
        self._dir_jumpscale_core = None

        conf = ""
        if self.db.get("jumpscale.config") is not None:
            conf = self.db.get("jumpscale.config").decode()

        if conf == "":
            path = self.jsconfig_path
            if os.path.exists(path):
                with open(path, 'rb') as ff:
                    conf = ff.read().decode()
        if conf == "":
            with open(os.path.join(self.dir_jumpscale_core,"Jumpscale","core","jumpscale.toml"), 'rb') as ff:
                conf = ff.read().decode()
        conf = conf.replace("{{HOME}}",self.dir_home)
        self.config = pytoml.loads(conf)


    @property
    def db(self):
        if not self._db:
            if tcpPortConnectionTest("localhost", 6379):
                from redis import StrictRedis
                # print("CORE_REDIS")
                self._db = StrictRedis(host='localhost', port=6379, db=0)
                self._db_fakeredis = False
            else:
                # print("CORE_MEMREDIS")
                import fakeredis
                self._db = fakeredis.FakeStrictRedis()
                self._db_fakeredis = True
        return self._db

    def db_reset(self):
        j.data.cache._cache = {}
        self._db = None

    @property
    def dir_home(self):
        if "HOMEDIR" in os.environ:
            self._dir_home = os.environ["HOMEDIR"]
        elif "HOME" in os.environ:
            self._dir_home = os.environ["HOME"]
        else:
            self._dir_home = "/root"
        return self._dir_home

    @property
    def dir_jumpscale_core(self):
        if self._dir_jumpscale_core is None:
            self._dir_jumpscale_core = os.path.dirname(os.path.dirname(__file__))
        return self._dir_jumpscale_core

    @property
    def jsconfig_path(self):
        options = ["%s/opt/cfg/jumpscale.toml" % self.dir_home,
                     "/opt/jumpscale.toml",
                     "%s/jumpscale/jumpscale.toml" % self.dir_home]
        for path in options:
            if os.path.exists(path):
                return path
        return options[0]



class Jumpscale():

    def __init__(self):
        self._shell = None
        self.exceptions = None

    def shell(self,name="",loc=True):
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



j = Jumpscale()
j.core = Core(j)

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

# pr=profileStart()

from .core.Text import Text
j.core.text = Text(j)

from .core.Dirs import Dirs
j.dirs = Dirs(j)
j.core.dirs = j.dirs

from .core.State import State
j.core.state = State(j)

from .core.logging.LoggerFactory import LoggerFactory
j.logger = LoggerFactory(j)
j.core.logger = j.logger

# IF YOU WANT TO DEBUG THE STARTUP, YOU NEED TO CHANGE THIS ONE
j.logger.enabled = False
j.logger.filter = []  # default filter which captures all is *

from .core.Application import Application
j.application = Application(j)
j.core.application = j.application

from .core.cache.Cache import Cache
j.core.cache = Cache(j)

from .core.PlatformTypes import PlatformTypes
j.core.platformtype = PlatformTypes(j)

from .core.errorhandler.ErrorHandler import ErrorHandler
j.errorhandler = ErrorHandler(j)
j.core.errorhandler = j.errorhandler
j.exceptions = j.errorhandler.exceptions
j.core.exceptions = j.exceptions


#THIS SHOULD BE THE END OF OUR CORE, EVERYTHING AFTER THIS SHOULD BE LOADED DYNAMICALLY


if "JSRELOAD" in os.environ  and os.path.exists("%s/jumpscale_generated.py"%j.dirs.TMPDIR):
    print("RELOAD JUMPSCALE LIBS")
    os.remove("%s/jumpscale_generated.py"%j.dirs.TMPDIR)

if not os.path.exists("%s/jumpscale_generated.py"%j.dirs.TMPDIR):
    from .core.generator.JSGenerator import JSGenerator
    j.core.jsgenerator = JSGenerator(j)
    j.core.jsgenerator.generate(methods_find=True)

ipath = "%s/jumpscale"%(j.dirs.TMPDIR)
if ipath not in sys.path:
    sys.path.append(ipath)

import jumpscale_generated

if j.core.jsgenerator.report_errors()>0:
    print("THERE ARE ERRORS: look in /tmp/jumpscale/ERRORS_report.md")
else:
    print ("INIT DONE")

# profileStop(pr)

# j.shell()
