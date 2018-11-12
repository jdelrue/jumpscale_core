from importlib import import_module
from Jumpscale import j
import sys
from peewee import *
JSBASE = j.application.JSBaseClass
from .BCDBIndexMeta import BCDBIndexMeta
from .RedisServer import RedisServer
from .BCDBDecorator import *
from .BCDBMeta import BCDBMeta
from .BCDBModel import BCDBModel
from .BCDBModelSQLITE import BCDBModelSQLITE
from .KVSSQLite import KVSSQLite
from gevent import queue
from Jumpscale.clients.zdb.ZDBClientBase import ZDBClientBase
import msgpack



import gevent

class BCDB(JSBASE):

    def __init__(self, name=None, zdbclient=None):
        """
        :param name: name for the BCDB
        :param zdbclient: if zdbclient == None then will only use sqlite db
        """
        JSBASE.__init__(self)

        if name is None:
            raise RuntimeError("name needs to be specified")

        if zdbclient is not None:
            if not isinstance(zdbclient, ZDBClientBase):
                raise RuntimeError("zdbclient needs to be type: JumpscaleLib.clients.zdb.ZDBClientBase")

        self.name = name
        j.data.bcdb.bcdb_instances[self.name]=self
        j.data.bcdb.latest = self

        if not j.data.types.string.check(self.name):
            raise RuntimeError("name needs to be string")

        self.zdbclient = zdbclient

        self.models = {}

        self._sqlitedb = None
        self._data_dir = j.sal.fs.joinPaths(j.dirs.VARDIR, "bcdb")

        self._index_schema_class_cache = {}  #cache for the index classes

        self.logger_enable()

        if zdbclient is None:
            self.kvs = KVSSQLite(self) #KEY VALUE STOR IMPLEMENTED IN SQLITE
        else:
            self.kvs = None

        if self.zdbclient:
            db = self.zdbclient.redis
        else:
            db = self.kvs

        self.meta = BCDBMeta(bcdb=self,db=db)

        if self.zdbclient:
            if self.zdbclient.list()==[] or self.zdbclient.list()==[0]:
                self.index_rebuild()
                self.meta = BCDBMeta(bcdb=self,db=db)

        #needed for async processing
        self.results={}
        self.results_id = 0

        #need to do this to make sure we load the classes from scratch
        for item in ["ACL","USER","GROUP"]:
            key = "Jumpscale.data.bcdb.models_system.%s"%item
            if key in sys.modules:
                sys.modules.pop(key)

        from .models_system.ACL import ACL
        from .models_system.USER import USER
        from .models_system.GROUP import GROUP

        self.acl = self.model_add(ACL())
        self.user = self.model_add(USER())
        self.group = self.model_add(GROUP())

        self.dataprocessor_greenlet = None
        self.dataprocessor_start()

        self._load()

        self.logger_enable()
        self.logger.info("BCDB INIT DONE:%s"%self.name)

    def redis_server_start(self,port=6380,secret="123456"):

        self.redis_server = RedisServer(bcdb=self,port=port,secret=secret)
        self.redis_server.init()
        self.redis_server.start()

    def _data_process(self):
        # needs gevent loop to process incoming data
        self.logger.info("DATAPROCESSOR STARTS")
        while True:
            method, args, kwargs, event, returnid = self.queue.get()
            res = method(*args,**kwargs)
            if returnid:
                self.results[returnid]=res
            event.set()
        self.logger.warning("DATAPROCESSOR STOPS")

    def dataprocessor_start(self):
        """
        will start a gevent loop and process the data in a greenlet

        this allows us to make sure there will be no race conditions when gevent used or when subprocess
        main issue is the way how we populate the sqlite db (if there is any)

        :return:
        """
        if self.dataprocessor_greenlet is None:
            self.sqlitedb
            self.queue = gevent.queue.Queue()
            self.dataprocessor_greenlet = gevent.spawn(self._data_process)
            self.dataprocessor_state = "RUNNING"


    @queue_method
    def reset(self):
        self.stop()
        j.sal.fs.remove(j.sal.fs.joinPaths(self._data_dir, self.name + ".db"))

    def stop(self):
        self.logger.warning("STOP BCDB")
        self.dataprocessor_greenlet.kill()
        self.sqlitedb.close()
        self._sqlitedb = None

    def index_rebuild(self):
        self.logger.warning("REBUILD INDEX")
        if self._sqlitedb is not None:
            self.sqlitedb.close()
        j.sal.fs.remove(j.sal.fs.joinPaths(self._data_dir, self.name + ".db"))
        self._sqlitedb = None
        self.sqlitedb #recreate
        if self.zdbclient is None:
            self.kvs = KVSSQLite(self)
        self.cache_flush()
        self.meta.reset()

        for url,model in self.models.items():
            # self.logger.warning("init index:%s"%model.schema.url)
            # if self.zdbclient is None:
            #     from pudb import set_trace; set_trace()
            # model.bcdb = self
            if model.bcdb != self:
                raise RuntimeError("bcdb on model needs to be same as myself")
            model._init_index()
            self.meta.schema_set(model.schema)


        for obj in self.iterate():
            obj.model.index_set(obj) #is not scheduled


    def cache_flush(self):
        #put all caches on zero
        for model in self.models.values():
            if model.cache_expiration>0:
                model.obj_cache = {}
            else:
                model.obj_cache = None
            model._init()


    @property
    def sqlitedb(self):
        if self._sqlitedb is None:
            self._indexfile = j.sal.fs.joinPaths(self._data_dir, self.name + ".db")
            if j.sal.fs.exists(self._indexfile):
                self.logger.info("SQLITEDB in %s"%self._indexfile)
            else:
                self.logger.warning("NEW SQLITEDB in %s"%self._indexfile)
            j.sal.fs.createDir(self._data_dir)
            self._sqlitedb = SqliteDatabase(self._indexfile)
        return self._sqlitedb

    def reset_data(self):
        """
        remove index, walk over all zdb's & remove data
        :param zdbclient_admin:
        :return:
        """
        self.logger.info("reset data")
        if self.zdbclient:
            self.zdbclient.flush(meta=self.meta)  #new flush command
        self.index_rebuild() #will make index empty

    def model_get(self, url):
        # url = j.core.text.strip_to_ascii_dense(url).replace(".", "_")
        if url in self.models:
            return self.models[url]
        raise RuntimeError("could not find model for url:%s" % url)

    def model_add(self, model):
        """

        :param model: is the model object  : inherits of self.MODEL_CLASS
        :return:
        """
        if not isinstance(model, self._BCDBModelClass_get()):
            raise RuntimeError("model needs to be of type:%s"%self._BCDBModelClass_get())
        self.models[model.schema.url] = model
        return self.models[model.schema.url]

    def model_get_from_schema(self, schema, reload=True, overwrite=True, dest=""):
        """
        :param schema: is schema as text or as schema obj
        :param reload: will reload template
        :param overwrite: will overwrite the resulting file even if it already exists
        :return:
        """
        if j.data.types.str.check(schema):
            schema_text=schema
            schema = j.data.schema.get(schema_text)
            self.logger.debug("model get from schema:%s, original was text."%schema.url)
        else:
            self.logger.debug("model get from schema:%s"%schema.url)
            if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
                raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")
            schema_text=schema.text


        if schema.key not in self.models or overwrite:
            tpath = "%s/templates/BCDBModelClass.py" % j.data.bcdb._path
            objForHash = schema_text
            myclass = j.tools.jinja2.code_python_render( path=tpath,
                                                         reload=reload, dest=dest,objForHash=objForHash,
                                                         schema_text=schema_text, bcdb=self, schema=schema,
                                                         overwrite=overwrite)

            model = myclass()
            self.models[schema.url] = model
            self.meta.schema_set(schema)  # should always be the first record !

        return self.models[schema.url]


    def _BCDBModelIndexClass_generate(self,schema, path_parent=None ):
        """

        :param schema: is schema object j.data.schema... or text
        :return: class of the model which is used for indexing

        """
        self.logger.debug("generate schema:%s"%schema.url)
        if path_parent:
            name = j.sal.fs.getBaseName(path_parent)[:-3]
            dir_path =  j.sal.fs.getDirName(path_parent)
            dest = "%s/%s_index.py"%(dir_path,name)

        if j.data.types.str.check(schema):
            schema = j.data.schema.get(schema)

        elif not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        if schema.key not in self._index_schema_class_cache:

            imodel = BCDBIndexMeta(schema=schema)  # model with info to generate
            imodel.enable = True
            imodel.include_schema = True
            tpath = "%s/templates/BCDBModelIndexClass.py" % j.data.bcdb._path
            myclass=j.tools.jinja2.code_python_render(path=tpath,
                                                      reload=True, dest=dest,
                                                      schema=schema, bcdb=self, index=imodel)

            self._index_schema_class_cache[schema.key] = myclass

        return self._index_schema_class_cache[schema.key]

    def _BCDBModelClass_get(self):
        if self.zdbclient:
            return BCDBModel
        else:
            return BCDBModelSQLITE


    def model_get_from_file(self, path):
        """
        add model to BCDB
        is path to python file which represents the model

        """
        self.logger.debug("model get from file:%s"%path)
        obj_key = j.sal.fs.getBaseName(path)[:-3]
        cl = j.tools.loader.load(obj_key=obj_key,path=path,reload=False)
        model = cl()
        self.models[model.schema.url] = model
        return model

    def models_add(self, path, overwrite=True):
        """
        will walk over directory and each class needs to be a model
        when overwrite used it will overwrite the generated models (careful)
        :param path:
        :return: None
        """
        self.logger.debug("models_add:%s"%path)

        if not j.sal.fs.isDir(path):
            raise RuntimeError("path: %s needs to be dir, to load models from"%path)


        pyfiles_base = []
        for fpath in j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True):
            pyfile_base = j.tools.loader._basename(fpath)
            if pyfile_base.find("_index")==-1:
                pyfiles_base.append(pyfile_base)

        tocheck = j.sal.fs.listFilesInDir(path, recursive=True, filter="*.toml", followSymlinks=True)
        for schemapath in tocheck:

            bname = j.sal.fs.getBaseName(schemapath)[:-5]
            if bname.startswith("_"):
                continue

            schema_text = j.sal.fs.readFile(schemapath)
            schema = j.data.schema.get(schema_text)
            toml_path = "%s.toml"%(schema.key)
            if j.sal.fs.getBaseName(schemapath)!=toml_path:
                toml_path = "%s/%s.toml"%(j.sal.fs.getDirName(schemapath),schema.key)
                j.sal.fs.renameFile(schemapath,toml_path)
                schemapath = toml_path

            dest = "%s/%s.py" % (path, bname)
            self.model_get_from_schema(schema=schema_text, overwrite=True, dest=dest)


        for pyfile_base in pyfiles_base:
            if pyfile_base.startswith("_"):
                continue
            path2 = "%s/%s.py"%(path,pyfile_base)
            self.model_get_from_file(path2)

    def _load(self):
        return self.meta._models_load()

    def _unserialize(self, id, data, return_as_capnp=False, model=None):

        res = msgpack.unpackb(data)

        if len(res) == 3:
            schema_id, acl_id, bdata_encrypted = res
            if model:
                if schema_id != model.schema_id:
                    raise RuntimeError("this id: %s is not of right type"%(id))
            else:
                model =self.meta.model_get_id(schema_id,bcdb=self)
        else:
            raise RuntimeError("not supported format in table yet")

        bdata = j.data.nacl.default.decryptSymmetric(bdata_encrypted)

        if return_as_capnp:
            return bdata
        else:
            obj = model.schema.get(capnpbin=bdata)
            obj.id = id
            obj.acl_id = acl_id
            obj.model = model
            if model.write_once:
                obj.readonly = True #means we fetched from DB, we need to make sure cannot be changed
            return obj

    def obj_get(self,id):

        data = self.zdbclient.get(id)
        if data is  None:
            return None
        return self._unserialize(id, data)


    def iterate(self, key_start=None, reverse=False, keyonly=False):
        """
        walk over all the namespace and yield each object in the database

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
        if self.zdbclient:
            db = self.zdbclient
        else:
            db = self.kvs
        for key, data in db.iterate(key_start=key_start, reverse=reverse, keyonly=keyonly):
            if key == 0:  # skip first metadata entry
                continue
            obj = self._unserialize(key, data)
            yield obj

    def get_all(self):
        return [obj for obj in self.iterate()]
