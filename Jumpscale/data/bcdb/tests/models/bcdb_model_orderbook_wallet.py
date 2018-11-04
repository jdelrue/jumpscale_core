from Jumpscale import j
#GENERATED CODE, can now change


SCHEMA="""
@url = threefoldtoken.wallet
@name = wallet
jwt = "" (S)                # JWT Token
addr* = ""                   # Address
ipaddr = (ipaddr)           # IP Address
email = "" (S)              # Email address
username = "" (S)           # User name


"""
from peewee import *
db = j.data.bcdb.bcdb_instances["test"].sqlitedb

class BaseModel(Model):
    class Meta:
        database = db

class Index_threefoldtoken_wallet(BaseModel):
    id = IntegerField(unique=True)
    addr = TextField(index=True)

MODEL_CLASS=j.data.bcdb.MODEL_CLASS

class Model(MODEL_CLASS):
    def __init__(self, bcdb, namespace):
        MODEL_CLASS.__init__(self, bcdb=bcdb, url="threefoldtoken.wallet", namespace=namespace)
        self.url = "threefoldtoken.wallet"
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

    