redisFound = False
try:
    from .Redis import Redis
    from .RedisQueue import RedisQueue
    from redis._compat import nativestr
    # import itertools
    import socket
    redisFound = True
except:
    pass
import os
import time
# import sys
from ...core import tcpPortConnectionTest

class RedisFactory:

    """
    """

    __jslocation__ = "j.clients.redis"

    def __init__(self):
        self.cache_clear()
        self._running = None

    def cache_clear(self):
        """
        clear the cache formed by the functions get() and getQueue()
        """
        self._redis = {}
        self._redisq = {}
        self._config = {}

    def get(
            self,
            ipaddr="localhost",
            port=6379,
            password="",
            fromcache=True,
            unixsocket=None,
            ardb_patch=False,
            set_patch=False,
            ssl=False,
            ssl_certfile=None,
            ssl_keyfile=None,
            timeout=4,
            ping=True,
            die=True,
            **args):
        """
        get an instance of redis client, store it in cache so we could easily retrieve it later

        :param ipaddr: used to form the key when no unixsocket
        :param port: used to form the key when no unixsocket
        :param fromcache: if False, will create a new one instead of checking cache
        :param unixsocket: path of unixsocket to be used while creating Redis

        other arguments to redis: ssl_cert_reqs=None, ssl_ca_certs=None 

        set_patch is needed when using the client for gedis

        """
        

        if redisFound == False:
            raise RuntimeError("redis libraries are not installed, please pip3 install them.")
        if unixsocket is None:
            key = "%s_%s" % (ipaddr, port)
        else:
            key = unixsocket

        if key not in self._redis or not fromcache:
            if unixsocket is None:
                self._redis[key] = Redis(ipaddr, port, password=password, ssl=ssl, ssl_certfile=ssl_certfile, \
                                         ssl_keyfile=ssl_keyfile,
                                         # socket_timeout=timeout,
                                         **args)
            else:
                self._redis[key] = Redis(unix_socket_path=unixsocket,
                                         # socket_timeout=timeout,
                                         password=password,
                                         ssl=ssl, ssl_certfile=ssl_certfile,
                                         ssl_keyfile=ssl_keyfile, **args)

        if ardb_patch:
            self._ardb_patch(self._redis[key])
        
        if set_patch:
            self._set_patch(self._redis[key])

        if ping:
            try:
                res = self._redis[key].ping()
            except Exception as e:
                if "Timeout" in str(e) or "Connection refused" in str(e):
                    if die==False:
                        return None
                    else:
                        raise RuntimeError("Redis on %s:%s did not answer"%(ipaddr,port))
                else:
                    raise e

        return self._redis[key]

    def _ardb_patch(self, client):
        client.response_callbacks['HDEL'] = lambda r: r and nativestr(r) == 'OK'

    def _set_patch(self, client):
        client.response_callbacks['SET'] = lambda r: r

    def getQueue(self, ipaddr, port, name, namespace="queues", fromcache=True):
        """
        get an instance of redis queue, store it in cache so we can easily retrieve it later

        :param ipaddr: used to form the key when no unixsocket
        :param port: used to form the key when no unixsocket
        :param name: name of the queue
        :param namespace: value of namespace for the queue
        :param fromcache: if False, will create a new one instead of checking cache
        """
        if not fromcache:
            return RedisQueue(self.get(ipaddr, port, fromcache=False), name, namespace=namespace)
        key = "%s_%s_%s_%s" % (ipaddr, port, name, namespace)
        if key not in self._redisq:
            self._redisq[key] = RedisQueue(
                self.get(ipaddr, port), name, namespace=namespace)
        return self._redisq[key]


    def core_get(self):
        """
        will try to create redis connection to $tmpdir/redis.sock
        if that doesn't work then will look for std redis port
        if that does not work then will return None

        j.clients.redis.core_get()

        """
        unix_socket_path = '%s/redis.sock' % self.j.dirs.TMPDIR

        db = None
        if os.path.exists(path=unix_socket_path):
            db = Redis(unix_socket_path=unix_socket_path)
        else:
            self.core_start()
            db = Redis(unix_socket_path=unix_socket_path)
        return db

    def kill(self):
        """
        kill all running redis instances
        """
        self.j.sal.process.execute("redis-cli -s %s/redis.sock shutdown" %
                              self.j.dirs.TMPDIR, die=False, showout=False)
        self.j.sal.process.execute("redis-cli shutdown", die=False, showout=False)
        self.j.sal.process.killall("redis")
        self.j.sal.process.killall("redis-server")

    def core_running(self):
        if self._running==None:
            self._running=self.j.sal.nettools.tcpPortConnectionTest("localhost",6379)
        return self._running

    def core_check(self):
        if not self.core_running():
            self.core_start()
        return self._running        

    def core_start(self, timeout=20):
        """
        starts a redis instance in separate ProcessLookupError
        standard on $tmpdir/redis.sock
        """
        if self.j.core.platformtype.myplatform.isMac:
            if not self.j.sal.process.checkInstalled("redis-server"):
                # prefab.system.package.install('redis')
                self.j.sal.process.execute("brew unlink redis", die=False)
                self.j.sal.process.execute("brew install redis;brew link redis")
            if not self.j.sal.process.checkInstalled("redis-server"):
                raise RuntimeError("Cannot find redis-server even after install")
            self.j.sal.process.execute("redis-cli -s %s/redis.sock shutdown" %
                                  self.j.dirs.TMPDIR, die=False, showout=False)
            self.j.sal.process.execute("redis-cli shutdown", die=False, showout=False)
        elif self.j.core.platformtype.myplatform.isLinux:
            if self.j.core.platformtype.myplatform.isAlpine:
                os.system("apk add redis")
            elif self.j.core.platformtype.myplatform.isUbuntu:
                os.system("apt install redis-server -y")
        else:
            raise RuntimeError("platform not supported for start redis")

        # cmd = "redis-server --port 6379 --unixsocket %s/redis.sock --maxmemory 100000000 --daemonize yes" % tmpdir  # 100MB
        # self.logger.info("start redis in background (osx)")
        # os.system(cmd)
        # self.logger.info("started")
        # time.sleep(1)
        # elif self.j.core.platformtype.myplatform.isCygwin:
        #     cmd = "redis-server --maxmemory 100000000 & "
        #     self.logger.info("start redis in background (win)")
        #     os.system(cmd)

        cmd = "echo never > /sys/kernel/mm/transparent_hugepage/enabled"
        os.system(cmd)
        if not self.j.core.platformtype.myplatform.isMac:
            cmd = "sysctl vm.overcommit_memory=1"
            os.system(cmd)

        # redis_bin = "redis-server"
        if "TMPDIR" in os.environ:
            tmpdir = os.environ["TMPDIR"]
        else:
            tmpdir = "/tmp"
        cmd = "redis-server --port 6379 --unixsocket %s/redis.sock --maxmemory 100000000 --daemonize yes" % tmpdir
        self.logger.info(cmd)
        self.j.sal.process.execute(cmd)
        limit_timeout = time.time() + timeout
        while time.time() < limit_timeout:
            if tcpPortConnectionTest("localhost", 6379):
                break
            time.sleep(2)
        else:
            raise self.j.exceptions.Timeout("Couldn't start redis server")
