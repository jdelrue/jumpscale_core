from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class ACL_index:

    def _init_index(self):
        pass #to make sure works if no index
        self.logger.info("init index:%s"%self.schema.url)

        db = self.bcdb.sqlitedb
        print(db)

        class BaseModel(Model):
            class Meta:
                print("*%s"%db)
                database = db

        class Index_jumpscale_bcdb_acl_1(BaseModel):
            id = IntegerField(unique=True)
            hash = TextField(index=True)

        self.index = Index_jumpscale_bcdb_acl_1
        self.index.create_table(safe=True)

    
    def index_set(self,obj):
        idict={}
        idict["hash"] = obj.hash
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    