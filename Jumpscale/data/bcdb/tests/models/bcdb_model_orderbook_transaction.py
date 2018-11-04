from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefoldtoken.transaction
@name = transaction
buy_order_id* = (I)          # id of buy order
sell_order_id* = (I)         # id of sell order
amount_bought = (F)         # the trade amount
currency = (S)              # the currency in which the transaction will happen
total_price = (F)           # total price of the transaction
state* = (S)                 # state of the transaction new/pending/failed/succeeded
buyer_wallet_addr = (S)     # Buyer wallet address
seller_wallet_addr = (S)    # Seller Wallet address
buyer_email_addr = (S)      # email addr used through IYO for the buyer
seller_email_addr = (S)     # email addr used through IYO for the seller



"""
from peewee import *
db = j.data.bcdb.bcdb_instances["test"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_threefoldtoken_transaction(BaseModel):
    id = IntegerField(unique=True)
    buy_order_id = IntegerField(index=True)
    sell_order_id = IntegerField(index=True)
    state = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, namespace):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefoldtoken.transaction", namespace=namespace)
        self.url = "threefoldtoken.transaction"
        self.index = Index_threefoldtoken_transaction
        self.index.create_table()
    
    def index_set(self,obj):
        idict={}
        idict["buy_order_id"] = obj.buy_order_id
        idict["sell_order_id"] = obj.sell_order_id
        idict["state"] = obj.state
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    