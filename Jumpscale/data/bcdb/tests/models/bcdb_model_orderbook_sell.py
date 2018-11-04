from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefoldtoken.order.sell
@name = ordersell
comment = ""
currency_to_sell* = "" (S)   # currency types BTC/ETH/XRP/TFT
currency_accept = (LS)      # can accept more than one currency
price_min* = 0 (N)           # can be defined in any currency
amount* = (F)                # amount
expiration* =  (D)           # can be defined as e.g. +1h
sell_to = (LS)              # list of wallet addresses which are allowed to buy from me
secret = (LS)               # if used the buyers need to have one of the secrets
approved* = (B)              # if True, object will be scheduled for matching, further updates/deletes are no more possible
owner_email_addr = (S)      # email addr used through IYO when order was created
wallet_addr* = (S)           # Wallet address


"""
from peewee import *
db = j.data.bcdb.bcdb_instances["test"].sqlitedb

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

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, namespace):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefoldtoken.order.sell", namespace=namespace)
        self.url = "threefoldtoken.order.sell"
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

    