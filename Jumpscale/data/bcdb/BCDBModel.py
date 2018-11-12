from Jumpscale import j
import msgpack
# import struct
# import gevent
# from gevent.event import Event
from .BCDBDecorator import *
JSBASE = j.application.JSBaseClass

# # is the base class for the model which gets generated from the template
# from JumpscaleLib.clients.zdb.ZDBClientBase import ZDBClientBase


class BCDBModel(JSBASE):
    def __init__(self, bcdb, schema=None,url=None, index_enable=True, cache_expiration=3600):
        """
        for query example see http://docs.peewee-orm.com/en/latest/peewee/query_examples.html

        e.g.
        ```
        query = self.index.name.select().where(index.cost > 0)
        for item in self.select(query):
            print(item.name)
        ```
        """

        JSBASE.__init__(self)

        if bcdb is None:
            raise RuntimeError("bcdb should be set")
        self.bcdb = bcdb

        if schema:
            url=schema.url

        if url in self.bcdb.meta.url2schema:
            sid, schema = self.bcdb.meta.schema_get_url(url=url)
        else:
            #means we don't have it in the zdbclient yet, needs to be added
            schema = j.data.schema.get(url=url)
            sid,schema = self.bcdb.meta.schema_set(schema)

        if self.bcdb.zdbclient:
            # if self.bcdb.zdbclient.get(0) == None:
            #     self.bcdb.meta.schema_set(schema)
            assert self.bcdb.zdbclient.get(0) != None #just test that the metadata has been filled in
        else:
            assert self.bcdb.kvs.get(0) != None #just test that the metadata has been filled in

        self.schema = schema
        self.schema_id = sid

        self.url = url

        self.is_config = False  # when used for config management
        self.write_once = False

        self.zdbclient = bcdb.zdbclient

        self.index_enable = index_enable
        self.autosave = False  # if set it will make sure data is automatically set from object

        self.objects_in_queue = {}

        if  self.bcdb.zdbclient:
            self.key = "%s_%s"%(self.zdbclient.nsname,self.url)  #is unique id for a bcdbmodel (unique per zdbclient !)
        else:
            self.key = self.url
        self.key = self.key.replace(".","_")

        self.logger_enable()

        if cache_expiration>0:
            self.obj_cache = {}
        else:
            self.obj_cache = None
        self.cache_expiration=cache_expiration

    def _init(self):
        self._init_index()

    def cache_reset(self):
        self.obj_cache = {}


    @queue_method
    def index_ready(self):
        """
        doesn't do much, just makes sure that we wait that queue has been processed upto this point
        :return:
        """
        return True

    @queue_method
    def index_rebuild(self):
        self.bcdb.index_rebuild()

    @queue_method
    def delete(self, obj_id):
        if hasattr(obj_id, "_JSOBJ"):
            obj_id = obj_id.id
        self._delete2(obj_id)
        if obj_id in self.obj_cache:
            self.obj_cache.pop(obj_id)
        if self.index:
            self.index_delete(obj_id)


    def _delete2(self,id):
        return self.zdbclient.delete(id)


    def check(self, obj):
        if not hasattr(obj, "_JSOBJ"):
            raise RuntimeError("argument needs to be a bcdb obj")

    @queue_method
    def set_dynamic(self, data, obj_id=None):
        """
        if string -> will consider to be json
        if binary -> will consider data for capnp
        if obj -> will check of JSOBJ
        if ddict will put inside JSOBJ
        """
        if j.data.types.string.check(data):
            data = j.data.serializers.json.loads(data)
            if obj_id == None and "id" in data:
                obj_id = data["id"]
            obj = self.schema.get(data)
        elif j.data.types.bytes.check(data):
            obj = self.schema.get(capnpbin=data)
            if obj_id is None:
                raise RuntimeError("objid cannot be None")
        elif getattr(data, "_JSOBJ", None):
            obj = data
            if obj_id is None and obj.id is not None:
                obj_id = obj.id
        elif j.data.types.dict.check(data):
            if obj_id == None and "id" in data:
                obj_id = data["id"]
            obj = self.schema.get(data)
        else:
            raise RuntimeError("Cannot find data type, str,bin,obj or ddict is only supported")
        obj.id = obj_id  # do not forget
        return self._set(obj)

    @queue_method_results
    def _set(self, obj, index=True):
        """
        :param obj
        :return: obj
        """
        self.check(obj)

        # prepare
        store,obj = self._set_pre(obj)

        if store:

            # later:
            if obj.acl_id is None:
                obj.acl_id = 0

            if obj._acl is not None:
                if obj.acl.id is None:
                    #need to save the acl
                    obj.acl.save()
                else:
                    acl2 = obj.model.bcdb.acl.get(obj.acl.id)
                    if acl2 is None:
                        #means is not in db
                        obj.acl.save()
                    else:
                        if obj.acl.hash != acl2.hash:
                            obj.acl.id = None
                            obj.acl.save() #means there is acl but not same as in DB, need to save
                            self.cache_reset()
                obj.acl_id = obj.acl.id

            bdata = obj._data
            bdata_encrypted = j.data.nacl.default.encryptSymmetric(bdata)

            l = [self.schema_id, obj.acl_id, bdata_encrypted]
            data = msgpack.packb(l)

            obj.id = self._set2(obj=obj,data=data)

            if index:
                self.index_set(obj)

            if self.obj_cache is not None:
                self.obj_cache[obj.id]=(j.data.time.epoch,obj)


        return obj


    def _set2(self,obj,data):

        if obj.id is None:
            # means a new one
            obj.id = self.zdbclient.set(data)
            if self.write_once:
                obj.readonly = True
            self.logger.debug("NEW:\n%s"%obj)
        else:
            try:
                self.zdbclient.set(data, key=obj.id)
            except Exception as e:
                if str(e).find("only update authorized")!=-1:
                    raise RuntimeError("cannot update object:%s\n with id:%s, does not exist"%(obj,obj.id))
                raise e

        return obj.id

    def _dict_process_out(self,ddict):
        """
        whenever dict is needed this method will be called before returning
        :param ddict:
        :return:
        """
        return ddict

    def _dict_process_in(self,ddict):
        """
        when data is inserted back into object
        :param ddict:
        :return:
        """
        return ddict


    def new(self,data=None, capnpbin=None):
        if data:
            data = self._dict_process_in(data)
        if data or capnpbin:
            obj = self.schema.get(data=data,capnpbin=capnpbin)
        else:
            obj = self.schema.new()
        obj.model = self
        obj = self._methods_add(obj)
        return obj

    def _methods_add(self,obj):
        return obj

    def _set_pre(self, obj):
        """

        :param obj:
        :return: True,obj when want to store
        """
        return True,obj

    def index_set(self, obj):
        pass

    def index_delete(self, obj):
        if not j.data.types.int.check(obj):
            obj = obj.id
        self.index.delete_by_id(obj)

    @queue_method_results
    def get(self, id, return_as_capnp=False,usecache=True):
        """
        @PARAM id is an int or a key
        @PARAM capnp if true will return data as capnp binary object,
               no hook will be done !
        @RETURN obj    (.index is in obj)
        """


        if id in [None,0,'0',b'0']:
            raise RuntimeError("id cannot be None or 0")

        if self.obj_cache is not None and usecache:
            # print("use cache")
            if id in self.obj_cache:
                epoch,obj = self.obj_cache[id]
                if j.data.time.epoch>self.cache_expiration+epoch:
                     self.obj_cache.pop(id)
                     # print("dirty cache")
                else:
                    # print("cache hit")
                    return obj


        data = self._get2(id)



        if not data:
            return None


        obj = self.bcdb._unserialize(id, data, return_as_capnp=return_as_capnp,model=self)
        self.obj_cache[id] = (j.data.time.epoch,obj)
        return obj


    def _get2(self,id):
        return self.zdbclient.get(id)

    def delete_all(self):
        for item in self.index.select():
             self.delete(item.id)

    def iterate(self, key='id', key_start=None, reverse=False, keyonly=False):
        """
        walk over objects which are of type of this model

        :param key_start: if specified start to walk from that key instead of the first one, defaults to None
        :param key_start: str, optional
        :param reverse: decide how to walk the namespace
                if False, walk from older to newer keys
                if True walk from newer to older keys
                defaults to False
        :param reverse: bool, optional
        :param keyonly: [description], defaults to False
        :param keyonly: bool, optional
        :raises e: [description]
        """
        if key_start:
            items = self.index.select().where(getattr(self.index, key) >= key_start)
        else:
            items = self.index.select()
        self.index_ready()
        for item in items:
            yield self.get(item.id)

    def get_all(self):
        res = []
        for obj in self.iterate():
            if obj==None:
                raise RuntimeError("iterate should not return None, ever")
            res.append(obj)
        return res

    def __str__(self):
        out = "model:%s\n" % self.schema.url
        out += j.core.text.prefix("    ", self.schema.text)
        return out

    __repr__ = __str__
