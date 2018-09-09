from Jumpscale.data.key_value_store.redis_store import RedisKeyValueStore
from Jumpscale.data.key_value_store.store import KeyValueStoreBase
from Jumpscale import j

class ARDBKeyValueStore(RedisKeyValueStore):

    def __init__(
            self,
            name,
            namespace="db",
            host='localhost',
            port=6379,
            unixsocket=None,
            db=0,
            password='',
            serializers=[],
            masterdb=None,
            cache=None,
            changelog=None):
        self.redisclient = j.clients.redis.get(host, port, password=password, unixsocket=unixsocket, ardb_patch=False)
        KeyValueStoreBase.__init__(self, namespace=namespace, name=name, serializers=serializers,
                                   masterdb=masterdb, cache=cache, changelog=changelog)
        self._indexkey = "index:%s" % namespace
        self.inMem = False
        self.type = "ardb"
