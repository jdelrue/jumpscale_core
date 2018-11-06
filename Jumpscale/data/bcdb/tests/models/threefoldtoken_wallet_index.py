from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class threefoldtoken_wallet_index:

    def _init_index(self):
        pass #to make sure works if no index

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db

        class Index_threefoldtoken_wallet(BaseModel):
            id = IntegerField(unique=True)
            addr = TextField(index=True)

        self.index = Index_threefoldtoken_wallet
            
        self.index.create_table()


        self.index = Index_threefoldtoken_wallet
        self.index.create_table()

    
    def index_set(self,obj):
        idict={}
        idict["addr"] = obj.addr
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    