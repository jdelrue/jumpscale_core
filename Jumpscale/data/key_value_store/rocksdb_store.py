from Jumpscale import j
from Jumpscale.data.key_value_store.store import KeyValueStoreBase
import rocksdb
import re


class RocksDBKeyValueStore(KeyValueStoreBase):
    """
    Warning: this rockdb implementation doesn't support anything except get/set
    """

    def __init__(
            self,
            name,
            namespace=None,
            dbpath='/tmp/default.db',
            serializers=[],
            masterdb=None,
            cache=None,
            changelog=None):
        if namespace:
            self.logger.info("Warning: namespace is not supported with rockdb backend")

        self.rocksdb = rocksdb.DB(dbpath, rocksdb.Options(create_if_missing=True))

        KeyValueStoreBase.__init__(
            self,
            namespace=None,
            name=name,
            serializers=[],
            masterdb=None,
            cache=None,
            changelog=None
        )

        self._indexkey = "index:%s" % namespace

    def close(self):
        """
        close database
        """
        del self.rocksdb
        self.rocksdb = None

    def _getKey(self, key):
        # return ('%s:%s' % (self.namespace, key)).encode('utf-8')
        return key.encode('utf-8')

    def _get(self, key):
        return self.rocksdb.get(self._getKey(key))

    def get(self, key, secret=None):
        return self._get(key)

    def _set(self, key, val):
        return self.rocksdb.put(self._getKey(key), val)

    def set(self, key, value=None, expire=None, acl={}, secret=""):
        return self._set(key, value)

    def _delete(self, key):
        return self.rocksdb.delete(self._getKey(key))

    def _exists(self, key):
        return (self.rocksdb.get(self._getKey(key)) is not None)

    """
    def increment(self, key):
        # only overrule if supporting DB has better ways
        return self.redisclient.incr(self._getKey(key))

    def destroy(self):
        # delete data
        for key in self.redisclient.keys(self.namespace + "*"):
            self.redisclient.delete(key)
        # delete index to data
        self.redisclient.delete(self._indexkey)
    """

    def index(self, items, secret=""):
        return None
        """
        @param items is {indexitem:key}
            indexitem is e.g. $actorname:$state:$role (is a text which will be index to key)
            key links to the object in the db
        ':' is not allowed in indexitem
        """

        """
        # if in non redis, implement as e.g. str index in 1 key and if gets too big then create multiple
        for key, val in items.items():
            k = "%s:%s" % (self._indexkey, key)
            current_val = self.rocksdb.get(k.encode('utf-8'))
            if current_val is not None:
                current_val = current_val.decode()
                if val not in current_val.split(','):
                    current_val += "," + val
                    k = "%s:%s" % (self._indexkey, key)
                    self.rocksdb.put(k.encode('utf-8'), current_val.encode('utf-8'))
            else:
                k = "%s:%s" % (self._indexkey, key)
                self.rocksdb.put(k.encode('utf-8'), val.encode('utf-8'))
        return True
        """

    '''

    def index_remove(self, key, secret=""):
        """
        @param keys is the key to remove from index
        """
        if self.redisclient.hexists(self._indexkey, key):
            self.redisclient.hdel(self._indexkey, key)

    def list(self, regex=".*", returnIndex=False, secret=""):
        """
        regex is regex on the index, will return matched keys
        e.g. .*:new:.* would match all actors with state new
        """
        res = set()
        for item in self.redisclient.hkeys(self._indexkey):
            item = item.decode()
            if re.match(regex, item) is not None:
                key = self.redisclient.hget(self._indexkey, item).decode()
                if returnIndex is False:
                    for key2 in key.split(","):
                        res.add(key2)
                else:
                    for key2 in key.split(","):
                        res.add((item, key2))
        return list(res)

    def _getQueueNameKey(self, name):
        return "%s:queue:%s" % (self.namespace, name)

    def queueSize(self, name):
        """Return the approximate size of the queue."""
        return self.redisclient.llen(self._getQueueNameKey(name))

    def queuePut(self, name, item):
        """Put item into the queue."""
        self.redisclient.rpush(self._getQueueNameKey(name), item)

    def queueGet(self, name, timeout=20):
        """Remove and return an item from the queue."""
        if timeout > 0:
            item = self.redisclient.blpop(self._getQueueNameKey(name), timeout=timeout)
            if item:
                item = item[1]
        else:
            item = self.redisclient.lpop(self._getQueueNameKey(name))
        return item

    def queueFetch(self, name, block=True, timeout=None):
        """ Like get but without remove"""
        if block:
            item = self.redisclient.brpoplpush(self._getQueueNameKey(name), self._getQueueNameKey(name), timeout)
        else:
            item = self.redisclient.lindex(self._getQueueNameKey(name), 0)
        return item
    '''

    def lookupSet(self, name, key, fkey):
        return None

        k = '%slookup:%d' % (self._indexkey, key)
        self.rocksdb.put(k.encode('utf-8'), fkey.encode('utf-8'))

    def lookupGet(self, name, key):
        return None

        k = '%slookup:%d' % (self._indexkey, key)
        self.rocksdb.get(k.encode('utf-8'))

    """
    def lookupDestroy(self, name):
        self.rocksdb.delete(self._indexkey + "lookup")
    """
