from Jumpscale import j

JSBASE = j.application.JSBaseClass


SCHEMA = """

@url = jumpscale.schemas.meta.1
schemas = (LO) !jumpscale.schemas.meta.schema.1

@url = jumpscale.schemas.meta.schema.1
url = ""
sid = 0  #schema id  
text = ""

"""


class BCDBMeta(JSBASE):

    def __init__(self, bcdb,db):
        JSBASE.__init__(self)
        self.bcdb = bcdb
        self._db = db
        self._db_is_redis = str(self._db).find("Redis")!=-1
        self._schema = j.data.schema.get(SCHEMA)
        self.logger_enable()
        self.reset()

    @property
    def data(self):
        if self._data is None:
            if self._db_is_redis:
                data = self._db.get(b'\x00\x00\x00\x00')
            else:
                data = self.bcdb.kvs.get(0)
            if data is None:
                self.logger.debug("save, empty schema")
                self._data = self._schema.new()
            else:
                self.logger.debug("schemas load from db")
                self._data = self._schema.get(capnpbin=data)
            self.save()

            self._schemas_load()
        return self._data

    def reset(self):
        self._data = None
        self.url2schema = {}
        self.id2schema = {}
        self._schema_last_id = -1
        self.url2model = {}
        self.id2model = {}
        self.url2id = {}
        self.data

    def save(self):
        if self._data is None:
            self.data
        self.logger.debug("save:\n%s"%self.data)
        if self._db_is_redis:
            if self._db.get(b'\x00\x00\x00\x00') == None:
                self._db.execute_command("SET","", self._data._data)
                assert self._db.execute_command("GET",b'\x00\x00\x00\x00') != None
            else:
                self._db.execute_command("SET",b'\x00\x00\x00\x00', self._data._data)
        else:
            self.bcdb.kvs.set(0,self._data._data)

    def schema_get_id(self,schema_id):
        return self.id2schema[schema_id]

    def schema_get_url(self,url):
        return self.url2id[url],self.url2schema[url]

    def model_get_id(self,schema_id,bcdb):
        if not schema_id in self.id2model:
            schema = self.schema_get_id(schema_id)
            self.id2model[schema_id] = self._model_load(schema)
        return self.id2model[schema_id]

    def model_get_url(self,url,bcdb):
        if not url in self.url2model:
            schema = self.schema_get_url(url)
            self.url2model[url] = self._model_load(schema,bcdb)
        return self.url2model[url]

    def schema_set(self, schema):
        if not isinstance(schema, j.data.schema.SCHEMA_CLASS):
            raise RuntimeError("schema needs to be of type: j.data.schema.SCHEMA_CLASS")

        # if "schema_id" in schema.__dict__ or "id" in schema.__dict__:
        #     j.shell()
        #     raise RuntimeError("should be no id in schema")
        self.logger.debug("schema set in meta:%s"%schema.url)
        if False or schema.url in self.url2schema:
            return self.schema_get_url(schema.url)
        else:
            #not known yet in namespace in ZDB
            if self._schema_last_id == -1:
                if self.data.schemas==[]:
                    self._schema_last_id=0
                else:
                    for item in self.data.schemas:
                        if item.sid>self._schema_last_id:
                            self._schema_last_id = item.sid
            self._schema_last_id +=1
            s = self.data.schemas.new()
            s.url = schema.url
            s.sid = self._schema_last_id
            s.text = schema.text.strip()+"\n"  #only 1 \n at end
            self.logger.info("new schema in meta:\n%s"%self.data)
            self.save()

            self._schema_load(s.sid, schema)

            return s.sid,schema

    def _schemas_load(self):
        for schema in self._data.schemas:
            schema_obj=j.data.schema.get(schema.text)
            schema_obj.id = schema.sid  #make sure we know the id on the schema
            if schema_obj.url != schema.url:
                raise RuntimeError("schema url needs to be same")
            self._schema_load(schema.sid, schema_obj)
            if schema.sid > self._schema_last_id:
                self._schema_last_id = schema.sid

    def _schema_load(self,sid,schema_obj):
        self.logger.info("load schema in meta:%s"%schema_obj.url)
        self.url2schema[schema_obj.url]=schema_obj
        self.id2schema[sid]=schema_obj
        self.url2id[schema_obj.url]=sid

    def _models_load(self):
        self.data #make sure we load when needed
        for schema in self.id2schema.values():
            self._model_load(schema)

    def _model_load(self,schema):
        model = self.bcdb.model_get_from_schema(schema=schema, reload=False)
        self.bcdb.models[model.url]=model
        self.url2model[schema.url] = model
        self.id2model[ model.schema_id] = model
        return model


    def __repr__(self):
        return str(self._data)

    __str__ = __repr__
