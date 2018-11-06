from Jumpscale import j
#GENERATED CODE CAN CHANGE

SCHEMA="""
@url = threefoldtoken.wallet
@name = wallet
jwt = "" (S)                # JWT Token
addr* = ""                   # Address
ipaddr = (ipaddr)           # IP Address
email = "" (S)              # Email address
username = "" (S)           # User name


"""


bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
ACLIndex = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class threefoldtoken_wallet(ACLIndex,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init()