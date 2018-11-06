from Jumpscale import j
#GENERATED CODE, can now change
from peewee import *


class threefoldtoken_order_sell_index:

    def _init_index(self):
        pass #to make sure works if no index

        db = self.bcdb.sqlitedb

        class BaseModel(Model):
            class Meta:
                database = db

        class Index_threefoldtoken_order_sell(BaseModel):
            id = IntegerField(unique=True)
            currency_to_sell = TextField(index=True)
            price_min = FloatField(index=True)
            amount = FloatField(index=True)
            expiration = IntegerField(index=True)
            approved = BooleanField(index=True)
            wallet_addr = TextField(index=True)

        self.index = Index_threefoldtoken_order_sell
            
        self.index.create_table()


        self.index = Index_threefoldtoken_order_sell
        self.index.create_table()

    
    def index_set(self,obj):
        idict={}
        idict["currency_to_sell"] = obj.currency_to_sell
        idict["price_min"] = obj.price_min_usd
        idict["amount"] = obj.amount
        idict["expiration"] = obj.expiration
        idict["approved"] = obj.approved
        idict["wallet_addr"] = obj.wallet_addr
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    