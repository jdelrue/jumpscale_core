from Jumpscale import j

# import JSModel
import time
# from abc import ABCMeta, abstractmethod
import collections

import msgpack

import re
JSBASE = j.application.jsbase_get_class()
class KeyValueStoreBase(JSBASE):  # , metaclass=ABCMeta):
    '''KeyValueStoreBase defines a store interface.'''

    def __init__(self, namespace, name="", serializers=[], masterdb=None, cache=None, changelog=None):
        JSBASE.__init__(self)
        self.namespace = namespace
        self.name = name
        self.serializers = serializers or list()
        self.unserializers = list(reversed(self.serializers))
        self.changelog = changelog
        self.masterdb = masterdb
        self._schema = b""
        self.owner = ""  # std empty
        self.inMem = False

    def __new__(cls, *args, **kwargs):
        '''
        Copies the doc strings (when available) from the base implementation
        '''

        attrs = iter(list(cls.__dict__.items()))

        for attrName, attr in attrs:
            if not attr.__doc__ and \
                    hasattr(KeyValueStoreBase, attrName) and \
                    not attrName.startswith('_') \
                    and isinstance(attr, collections.Callable):

                baseAttr = getattr(KeyValueStoreBase, attrName)
                attr.__doc__ = baseAttr.__doc__

        return object.__new__(cls)

    @property
    def keys(self):
        raise RuntimeError("keys not implemented, only works for mem & redis")

    def destroy(self):
        # delete data
        for key in self.keys:
            self.logger.debug("delete:%s" % key)
            self.delete(key)
        self.index_destroy()

    @property
    def schema(self):
        return j.data.hash.bin2hex(self._schema).decode()

    @schema.setter
    def schema(self, val):
        """
        is 32 or 16 byte key to schema as used for this namespace
        """
        if len(val) == 32:
            val = j.data.hash.hex2bin(val)
        elif len(val) != 16:
            raise j.exceptions.Input(message="schema needs to be 32 or 16 bytes",
                                     level=1, source="", tags="", msgpub="")
        if not j.data.types.bytes.check(val):
            raise j.exceptions.Input(message="schema needs to be in bytes")
        self._schema = val

    @property
    def owner(self):
        """
        to define who owns this object, normally when you open a store, you set the owner if not the default
        """
        if self._owner == "":
            return ""
        return j.data.hash.bin2hex(self._owner).decode()

    @owner.setter
    def owner(self, val):
        if val == "":
            self._owner = ""
            return

        if len(val) == 32:
            val = j.data.hash.hex2bin(val)
        elif len(val) != 16:
            raise j.exceptions.Input(message="owner needs to be 32 or 16 bytes",
                                     level=1, source="", tags="", msgpub="")
        if not j.data.types.bytes.check(val):
            raise j.exceptions.Input(message="owner needs to be in bytes")

        self._owner = val

    def _encode(self, val, expire=0, acl={}):

        # data = $type + $owner + $schema + $expire + $lengthacllist +
        # [acllist] + snappyencoded(val) + $crcOfAllPrevious

        #
        # serialize type  (is more like a version e.g. version 1.0)
        #

        # type of this encoding, to make sure we have backwards compatibility
        # type = 4bits:  $schemaYesNo,$expireYesNo,0,0 + 4 bit version of format now 0
        ttype = 0

        if expire is None:
            expire = 0

        if self._schema != b"":
            ttype += 0b1000000

        if expire != 0:
            expire = j.data.time.getTimeEpoch() + expire
            ttype += 0b0100000
            expireb = expire.to_bytes(4, byteorder='big', signed=False)
        else:
            expireb = b""

        if self._owner != "":
            ttype += 0b0001000

        # data should be binary if not lets msgpack or leave as string
        if j.data.types.string.check(val):
            val = val.encode()
            ttype += 0b0000100
        elif j.data.types.bytes.check(val) == False:
            val = j.data.serializers.msgpack.dumps(val)
            ttype += 0b0010000

        typeb = ttype.to_bytes(1, byteorder='big', signed=False)

        aclb = j.data.kvs._aclSerialze(acl)

        # val = snappy.compress(val)

        if self._owner == "":
            serialized = typeb + self._schema + expireb + aclb + val
        else:
            serialized = typeb + self._owner + self._schema + expireb + aclb + val

        # checksum
        crc = j.data.hash.crc32_string(serialized)
        crc = crc.to_bytes(4, byteorder='big', signed=False)

        return serialized + crc

    def _decode(self, data):
        """
        @return [val,owner="",schema="",expire=0,acl={}]
        """

        crcint = j.data.hash.crc32_string(data[:-4])
        crc = crcint.to_bytes(4, byteorder='big', signed=False)

        if not crc == data[-4:]:
            raise j.exceptions.Input(message="Invalid checksum (CRC), is this a valid object ?:%s" % data)

        #
        # parsing header
        #
        header = data[0]

        counter = 1

        if header & 0b0001000:  # means there is an owner defined, get it
            owner = j.data.hash.bin2hex(data[counter:counter + 16]).decode()
            counter += 16
        else:
            owner = ""

        if header & 0b1000000:
            # schema defined
            schema = j.data.hash.bin2hex(data[counter:counter + 16])
            counter += 16
        else:
            # no schema
            schema = ""

        if header & 0b0100000:
            # expire is set
            expire = int.from_bytes(data[counter:counter + 4], byteorder='big', signed=False)
            counter += 4
        else:
            expire = 0

        nrsecrets = int.from_bytes(data[counter:counter + 1], byteorder='big', signed=False)
        aclbin = data[counter:counter + 17 * nrsecrets + 1]
        counter += 17 * nrsecrets + 1

        acl = j.data.kvs._aclUnserialze(aclbin)

        val = data[counter:-4]

        # val = snappy.decompress(val)

        if header & 0b0000100:
            # is string
            val = val.decode()
        elif header & 0b0010000:
            val = j.data.serializers.msgpack.loads(val)

        return (val, owner, schema, expire, acl)

    def set(self, key, value=None, expire=None, acl={}, secret=""):
        """
        @param secret, when not specified the owner will be used, allows to specify different secret than youw own owner key
        @param expire is seconds from now, when obj will expire
            if you want to set then needs to be an int>0 or 0

        """
        # print("Expire0:%s"%expire)
        if acl != {} or secret != "":
            res = self.getraw(key, secret=secret, die=False, modecheck="w")

            if res is not None:
                (valOld, owner, schemaOld, expireOld, aclOld) = res

                if schemaOld != self.schema:
                    msg = "schema of this db instance should be same as what is found in db"
                    raise j.exceptions.Input(message=msg, level=1)

                acl.update(aclOld)

        else:
            if value is None:
                raise j.exceptions.Input(message="value needs to be set (not None), key:%s" %
                                                 key)

        value2 = self.serialize(value)

        data = self._encode(value2, expire, acl)
        self._set(key, data, expire=expire)

        # if self.cache != None:
        #     self.cache._set(key=key, category=category, value=value1)

    def exists(self, key, secret=""):
        try:
            res = self.get(key, secret=secret)
        except Exception as e:
            if "not allowed" in str(e):
                # exists but no access, should just return False
                # return False
                # raise j.exceptions.Input(message="Object '%s' does exist but I have not rights." %
                #  key)
                return True
            if "Cannot find" in str(e):
                return False
            raise e
        return res is not None

    def get(self, key, secret="", die=False):
        '''
        Gets a key value pair from the store

        @param: key of the key value pair
        @type: String

        @return: value of the key value pair

        '''
        (val, owner, schema, expire, acl) = self.getraw(key, secret, die=die)
        if expire != 0 and expire < j.data.time.getTimeEpoch():
            return None
        return val

    def getraw(self, key, secret="", die=False, modecheck="r"):
        '''
        Gets a key value pair from the store

        @param: key of the key value pair
        @type: String

        @param: modecheck is r,w or d, normally get always needs to check on r but can overrule this, can be more than 1 e.g. rw

        @return: (val, owner, schema, expire, acl)

        '''

        # if self.cache != None:
        #     res = self.cache._get(key=key, category=category)  # get raw data
        #     if res != None:
        #         return self.unserialize(self._decode(res))

        data = self._get(key)

        if data is None:
            if die:
                raise j.exceptions.Input(message="Cannot find object: %s" % key)
            else:
                return (None, "", "", 0, {})

        if secret == "":
            secret = self.owner

        (val, owner, schema, expire, acl) = self._decode(data)

        if j.data.kvs._aclCheck(acl, owner, secret, modecheck) is False:
            raise j.exceptions.Input(message="cannot get obj with key '%s' because mode '%s' is not allowed." % (
                key, modecheck))

        val = self.unserialize(val)

        return (val, owner, schema, expire, acl)

    def delete(self, key, secret=""):

        val, owner, schema, expire, acl = self.getraw(key, secret=secret, modecheck='d', die=True)

        if secret is not None and secret != '' and owner != secret:
            raise j.exceptions.Input(message="Cannot delete object, only owner can delete an object",
                                     level=1, source="", tags="", msgpub="")

        self._delete(key=key)

    def serialize(self, value):
        for serializer in self.serializers:
            value = serializer.dumps(value)

        return value

    def unserialize(self, value):
        for serializer in self.unserializers:
            if value is not None:
                value = serializer.loads(value)

        return value

    def index(self, items, secret=""):
        """
        @param items is {indexitem:key}
            indexitem is e.g. $actorname:$state:$role (is a text which will be index to key)
                indexitems are always made lowercase
            key links to the object in the db
        ':' is not allowed in indexitem
        """
        if secret == "":
            secret = self.owner

        indexobj = self.getraw("index", die=False, secret=secret)

        if indexobj is None:
            ddict = {}
        else:
            ddict = msgpack.loads(indexobj)
        ddict.update(items)

        data2 = msgpack.dumps(ddict)
        self.set("index", data2, secret=secret)

    def index_remove(self, key, secret=""):
        raise RuntimeError("not implemented")

    def index_destroy(self):
        raise RuntimeError("not implemented")

    def index_list(self, regex=".*", returnIndex=False, secret=""):
        """
        regex is regex on the index, will return matched keys
        e.g. .*:new:.* would match e.g. all obj with state new

        when returnIndex:
            return [(indexitem,key),...]
        """

        indexobj = self.getraw("index", die=False, secret=secret)

        if indexobj is None:
            ddict = {}
        else:
            ddict = msgpack.loads(indexobj)

        res = set()
        for item, key in ddict.items():
            item = item.decode()
            key = key.decode()
            if re.match(regex, item) is not None:
                if returnIndex is False:
                    for key2 in key.split(","):
                        res.add(key2)
                else:
                    for key2 in key.split(","):
                        res.add((item, key2))
        return list(res)

    def lookupSet(self, name, key, fkey):
        raise NotImplemented()

    def lookupGet(self, name, key):
        raise NotImplemented()

    # DO NOT LOOK AT BELOW RIGHT NOW IS FOR FUTURE

    # def checkChangeLog(self):
    #     pass

    #
    # def cacheSet(self, key, value, expirationInSecondsFromNow=120):
    #     ttime = j.data.time.getTimeEpoch()
    #     value = [ttime + expirationInSecondsFromNow, value]
    #     if key == "":
    #         key = j.data.idgenerator.generateGUID()
    #     self.set(category="cache", key=key, value=value)
    #     return key
    #
    # def cacheGet(self, key, deleteAfterGet=False):
    #     r = self.get("cache", key)
    #     if deleteAfterGet:
    #         self.delete("cache", key)
    #     return r[1]
    #
    # def cacheDelete(self, key):
    #     self.delete("cache", key)
    #
    # def cacheExists(self, key):
    #     return self.exists("cache", key)
    #
    # def cacheList(self):
    #
    #     if "cache" in self.listCategories():
    #         return self.list("cache")
    #     else:
    #         return []
    #
    # def cacheExpire(self):
    #     now = j.data.time.getTimeEpoch()
    #     for key in self.list():
    #         expiretime, val = self.get(key)
    #         if expiretime > now:
    #             self.delete("cache", key)
    #
    # @abstractmethod
    # def exists(self, category, key):
    #     '''
    #     Checks if a key value pair exists in the store.
    #
    #     @param: category of the key value pair
    #     @type: String
    #
    #     @param: key of the key value pair
    #     @type: String
    #
    #     @return: flag that states if the key value pair exists or not
    #     @rtype: Boolean
    #     '''
    #
    # @abstractmethod
    # def list(self, category, prefix):
    #     '''
    #     Lists the keys matching `prefix` in `category`.
    #
    #     @param category: category the keys should be in
    #     @type category: String
    #     @param prefix: prefix the keys should start with
    #     @type prefix: String
    #     @return: keys that match `prefix` in `category`.
    #     @rtype: List(String)
    #     '''
    #     raise j.exceptions.NotImplemented("list is only supported on selected db's")
    #
    # @abstractmethod
    # def listCategories(self):
    #     '''
    #     Lists the categories in this db.
    #
    #     @return: categories in this db
    #     @rtype: List(String)
    #     '''
    #
    # @abstractmethod
    # def _categoryExists(self, category):
    #     '''
    #     Checks if a category exists
    #
    #     @param category: category to check
    #     @type category: String
    #     @return: True if the category exists, False otherwise
    #     @rtype: Boolean
    #     '''
    #
    # def lock(self, locktype, info="", timeout=5, timeoutwait=0, force=False):
    #     """
    #     if locked will wait for time specified
    #     @param locktype of lock is in style machine.disk.import  (dot notation)
    #     @param timeout is the time we want our lock to last
    #     @param timeoutwait wait till lock becomes free
    #     @param info is info which will be kept in lock, can be handy to e.g. mention why lock taken
    #     @param force, if force will erase lock when timeout is reached
    #     @return None
    #     """
    #     category = "lock"
    #     lockfree = self._lockWait(locktype, timeoutwait)
    #     if not lockfree:
    #         if force == False:
    #             raise j.exceptions.RuntimeError("Cannot lock %s %s" % (locktype, info))
    #     value = [self.id, j.data.time.getTimeEpoch() + timeout, info]
    #     encodedValue = j.data.serializers.json.dumps(value)
    #     self.settest(category, locktype, encodedValue)
    #
    # def lockCheck(self, locktype):
    #     """
    #     @param locktype of lock is in style machine.disk.import  (dot notation)
    #     @return result,id,lockEnd,info  (lockEnd is time when lock times out, info is descr of lock, id is who locked)
    #                    result is False when free, True when lock is active
    #     """
    #     if self.exists("lock", locktype):
    #         encodedValue = self.get("lock", locktype)
    #         try:
    #             id, lockEnd, info = j.data.serializers.json.loads(encodedValue)
    #         except ValueError:
    #             self.logger.error("Failed to decode lock value")
    #             raise ValueError("Invalid lock type %s" % locktype)
    #
    #         if j.data.time.getTimeEpoch() > lockEnd:
    #             self.delete("lock", locktype)
    #             return False, 0, 0, ""
    #         value = [True, id, lockEnd, info]
    #         return value
    #     else:
    #         return False, 0, 0, ""
    #
    # def _lockWait(self, locktype, timeoutwait=0):
    #     """
    #     wait till lock free
    #     @return True when free, False when unable to free
    #     """
    #     locked, id, lockEnd, info = self.lockCheck(locktype)
    #     if locked:
    #         start = j.data.time.getTimeEpoch()
    #         if lockEnd + timeoutwait < start:
    #             # the lock was already timed out so is free
    #             return True
    #
    #         while True:
    #             now = j.data.time.getTimeEpoch()
    #             if now > start + timeoutwait:
    #                 return False
    #             if now > lockEnd:
    #                 return True
    #             time.sleep(0.1)
    #     return True
    #
    # def unlock(self, locktype, timeoutwait=0, force=False):
    #     """
    #     @param locktype of lock is in style machine.disk.import  (dot notation)
    #     """
    #     lockfree = self._lockWait(locktype, timeoutwait)
    #     if not lockfree:
    #         if force == False:
    #             raise j.exceptions.RuntimeError("Cannot unlock %s" % locktype)
    #     self.delete("lock", locktype)
    #
    # def incrementReset(self, incrementtype, newint=0):
    #     """
    #     @param incrementtype : type of increment is in style machine.disk.nrdisk  (dot notation)
    #     """
    #     self.set("increment", incrementtype, str(newint))
    #
    # def increment(self, incrementtype):
    #     """
    #     @param incrementtype : type of increment is in style machine.disk.nrdisk  (dot notation)
    #     """
    #     if not self.exists("increment", incrementtype):
    #         self.set("increment", incrementtype, "1")
    #         incr = 1
    #     else:
    #         rawOldIncr = self.get("increment", incrementtype)
    #         if not rawOldIncr.isdigit():
    #             raise ValueError("Increment type %s does not have a digit value: %s" % (incrementtype, rawOldIncr))
    #         oldIncr = int(rawOldIncr)
    #         incr = oldIncr + 1
    #         self.set("increment", incrementtype, str(incr))
    #     return incr
    #
    # def getNrRecords(self, incrementtype):
    #     if not self.exists("increment", incrementtype):
    #         self.set("increment", incrementtype, "1")
    #         incr = 1
    #     return int(self.get("increment", incrementtype))
    #
    # def settest(self, category, key, value):
    #     """
    #     if well stored return True
    #     """
    #     self.set(category, key, value)
    #     if self.get(category, key) == value:
    #         return True
    #     return False
    #
    # def _assertValidCategory(self, category):
    #     if not isinstance(category, str) or not category:
    #         raise ValueError('Invalid category, non empty string expected')
    #
    # def _assertValidKey(self, key):
    #     if not isinstance(key, str) or not key:
    #         raise ValueError('Invalid key, non empty string expected')
    #
    # def _assertExists(self, category, key):
    #     if not self.exists(category, key):
    #         errorMessage = 'Key value store doesnt have a value for key '\
    #             '"%s" in category "%s"' % (key, category)
    #         self.logger.error(errorMessage)
    #         raise KeyError(errorMessage)
    #
    # def _assertCategoryExists(self, category):
    #     if not self._categoryExists(category):
    #         errorMessage = 'Key value store doesn\'t have a category %s' % (category)
    #         self.logger.error(errorMessage)
    #         raise KeyError(errorMessage)
    #
    # def now(self):
    #     """
    #     return current time
    #     """
    #     return j.data.time.getTimeEpoch()
    #
    # def getModifySet(self, category, key, modfunction, **kwargs):
    #     """
    #     get value
    #     give as parameter to modfunction
    #     try to set by means of testset, if not succesfull try again, will use random function to maximize chance to set
    #     @param kwargs are other parameters as required (see usage in subscriber function)
    #     """
    #     counter = 0
    #     while counter < 30:
    #         data = self.get(category, key)
    #         data2 = modfunction(data)
    #         if self.settest(category, key, data2):
    #             break  # go out  of loop, could store well
    #         time.time.sleep(float(j.data.idgenerator.generateRandomInt(1, 10)) / 50)
    #         counter += 1
    #     return data2
    #
    # def subscribe(self, subscriberid, category, startid=0):
    #     """
    #     each subscriber is identified by a key
    #     in db there is a dict stored on key for category = category of this method
    #     value= dict with as keys the subscribers
    #     {"kristof":[lastaccessedTime,lastId],"pol":...}
    #
    #     """
    #     if not self.exists("subscribers", category):
    #         data = {subscriberid: [self.now(), startid]}
    #     else:
    #         if startid != 0:
    #             if not self.exists(category, startid):
    #                 raise j.exceptions.RuntimeError(
    #                     "Cannot find %s:%s in db, cannot subscribe, select valid startid" % (category, startid))
    #
    #             def modfunction(data, subscriberid, db, startid):
    #                 data[subscriberid] = [db.now(), startid]
    #                 return data
    #
    #             self.getModifySet("subscribers", category, modfunction,
    #                               subscriberid=subscriberid, db=self, startid=startid)
    #
    # def subscriptionGetNextItem(self, subscriberid, category, autoConfirm=True):
    #     """
    #     get next item from subscription
    #     returns
    #        False,None when no next
    #        True,the data when a next
    #     """
    #     if not self.exists("subscribers", category):
    #         raise j.exceptions.RuntimeError("cannot find subscription")
    #     data = self.get("subscribers", category)
    #     if subscriberid not in data:
    #         raise j.exceptions.RuntimeError("cannot find subscriber")
    #     lastaccesstime, lastid = data[subscriberid]
    #     lastid += 1
    #     if not self.exists(category, startid):
    #         return False, None
    #     else:
    #         return True, self.get(category, startid)
    #     if autoConfirm:
    #         self.subscriptionAdvance(subscriberid, category, lastid)
    #     return self.get(category, key)
    #
    # def subscriptionAdvance(self, subscriberid, category, lastProcessedId):
    #
    #     def modfunction(data, subscriberid, db, lastProcessedId):
    #         data[subscriberid] = [db.now(), lastProcessedId]
    #         return data
    #
    #     self.getModifySet("subscribers", category, modfunction, subscriberid=subscriberid,
    #                       db=self, lastProcessedId=lastProcessedId)
    #
    # def setDedupe(self, category, data):
    #     """
    #     will return unique key which references the data, if it exists or not
    #     """
    #     if data == "" or data is None:
    #         return ""
    #     if len(data) < 32:
    #         return data
    #     md5 = j.data.hash.md5_string(data)
    #     if not self.exists(category, md5):
    #         self.set(category, md5, data)
    #     return md5
    #
    # def getDedupe(self, category, key):
    #     if len(key) < 32:
    #         return key.encode()
    #     return self.get(category, key)
