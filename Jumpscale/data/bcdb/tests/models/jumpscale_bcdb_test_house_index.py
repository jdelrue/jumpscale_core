from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class jumpscale_bcdb_test_house_index:

    def _init_index(self):
        pass #to make sure works if no index

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db

        class Index_jumpscale_bcdb_test_house(BaseModel):
            id = IntegerField(unique=True)
            name = TextField(index=True)
            active = BooleanField(index=True)
            cost = FloatField(index=True)

        self.index = Index_jumpscale_bcdb_test_house
            
        self.index.create_table()


        self.index = Index_jumpscale_bcdb_test_house
        self.index.create_table()

    
    def index_set(self,obj):
        idict={}
        idict["name"] = obj.name
        idict["active"] = obj.active
        idict["cost"] = obj.cost_usd
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    