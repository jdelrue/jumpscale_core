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

    def __init__(self):
        self.__jslocation__ = 'j.core'
        self._db = None

    @property
    def db(self):
        if not self._db:
            if tcpPortConnectionTest("localhost", 6379):
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

