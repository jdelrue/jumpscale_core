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


class Core(object):

    __jslocation__ = 'j.core'
    __jsdeps__ = {
        'application': 'Application',
        'dirs': 'Dirs',
        'logging': ('Jumpscale.logging.LoggerFactory', 'LoggerFactory'),
        'events': ('Jumpscale.errorhandler.EventHandler', 'EventHandler'),
        'platformtype': 'PlatformTypes',
        'errorhandler': ('Jumpscale.errorhandler.ErrorHandler', 'ErrorHandler'),
        'jsbase': 'JSBase',
              }

    def __init__(self):
        self._db = None
        self._state = None

    @property
    def db(self):
        if not self._db:
            if hasattr(self.j.clients, "redis") and \
                tcpPortConnectionTest("localhost", 6379):
                # print("CORE_REDIS")
                self._db = self.j.clients.redis.core_get()
            else:
                # print("CORE_MEMREDIS")
                import fakeredis
                self._db = fakeredis.FakeStrictRedis()
        return self._db

    @db.setter
    def db(self, newdb):
        self.db_reset()
        slf._db = newdb

    def db_reset(self):
        self.j.data.datacache._cache = {}
        self._db = None

    @property
    def state(self):
        if self._state is None:
            return self.j.tools.executorLocal.state
        return self._state

    @state.setter
    def state(self, newstate):
        slf._state = state

