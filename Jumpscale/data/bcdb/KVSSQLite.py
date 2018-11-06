from Jumpscale import j
from peewee import *

JSBASE = j.application.JSBaseClass

class KVSSQLite(JSBASE):

    def __init__(self,bcdb):
        JSBASE.__init__(self)
        self.bcdb = bcdb
        self.sqlitedb = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = self.sqlitedb

        class KVS(BaseModel):
            id = IntegerField(unique=True,index=True)
            value = BlobField()

        self._table_model = KVS
        self.logger_enable()
        self.logger.info("TABLE CREATED FOR KVS")
        self._table_model.create_table()

    def set(self,key,val):
        key=int(key)
        if self.exists(key):
            self._table_model.update(value=val).where(self._table_model.id ==key).execute()
        else:
            self._table_model.create(id=key,value=val)
        v=  self.get(key)
        return key

    def exists(self,key):
        return self.count(key)>0

    def count(self,key):
        return self._table_model.select().where(self._table_model.id ==key).count()

    def get(self,key):
        res = self._table_model.select().where(self._table_model.id ==key)
        if len(res)==0:
            return None
        elif len(res)>1:
            raise RuntimeError("error, can only be 1 item")
        return res[0].value

    def delete(self,key):
        j.shell()

    def iterate(self,key_start=None,**kwargs):
        if key_start:
            items = self._table_model.select().where(getattr(self._table_model, id) >= key_start)
        else:
            items = self._table_model.select()
        for item in items:
            yield self.get(item.id)

