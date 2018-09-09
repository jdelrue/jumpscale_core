from Jumpscale.data.key_value_store.store import KeyValueStoreBase
from Jumpscale import j
import shelve
import re


class FileKeyValueStore(KeyValueStoreBase):
    """
    This file store will open the file for writing in the init and do sync for every write/delete entery
    for high performance
    sync simply flush the buffer to disk without having to open/close the file every time
    """

    def __init__(self, name, namespace="db", baseDir='/tmp', host='localhost', serializers=[]):
        self._db_path = '{baseDir}/{name}'.format(baseDir=baseDir, name=name)
        self.db = shelve.open(self._db_path, writeback=True)
        self.name = name
        self.namespace = namespace
        self.serializers = serializers
        self._indexkey = "index:%s" % namespace
        self.type = "file"
        KeyValueStoreBase.__init__(self, serializers)

    def _getKey(self, key):
        return '%s:%s' % (self.namespace, key)

    def _get(self, key):
        item = self.db.get(self._getKey(key))
        return item

    def _set(self, key, val, expire=0):
        self.db[self._getKey(key)] = val
        self.db.sync()
        return val

    def _delete(self, key):
        if self._getKey(key) in self.db:
            self.db.pop(self._getKey(key))
            self.db.sync()
        # return None

    def _exists(self, key):
        return self._getKey(key) in self.db

    @property
    def keys(self):
        keys = list(filter(lambda x: x.startswith('%s:' % self.namespace), self.db.keys()))
        return keys

    def index(self, items, secret=""):
        """
        @param items is {indexitem:key}
            indexitem is e.g. $actorname:$state:$role (is a text which will be index to key)
            key links to the object in the db
        ':' is not allowed in indexitem
        """
        for key, val in items.items():
            index = self._get(self._indexkey) or {}
            current_val = index.get(key)
            if current_val is not None:
                if val not in current_val.split(','):
                    current_val += "," + val
                    index[key] = current_val
            else:
                index[key] = val
        self._set(self._indexkey, index)
        return True

    def index_destroy(self):
        self.delete(self._indexkey)

    def index_remove(self, keys, secret=""):
        """
        @param keys is the key to remove from index
        """
        index = self._get(self._indexkey) or {}
        for key in keys:
            if key in index:
                del index[key]
        self._set(self._indexkey, index)

    def list(self, regex=".*", returnIndex=False, secret=""):
        """
        regex is regex on the index, will return matched keys
        e.g. .*:new:.* would match all actors with state new
        """
        res = set()
        index = self._get(self._indexkey) or {}
        for item in index.keys():
            if re.match(regex, item) is not None:
                key = index[item]
                if returnIndex is False:
                    for key2 in key.split(","):
                        res.add(key2)
                else:
                    for key2 in key.split(","):
                        res.add((item, key2))
        return list(res)

    def delete(self, key):
        if self.exists(key):
            self._delete(key)

    def __del__(self):
        self.logger = None
        self.db.close()
