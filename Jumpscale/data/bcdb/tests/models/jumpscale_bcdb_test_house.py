from Jumpscale import j
#GENERATED CODE CAN CHANGE

SCHEMA="""
@url = jumpscale.bcdb.test.house
name* = "" (S)
active* = "" (B)
cost* = (N)
room = (LO) !jumpscale.bcdb.test.room


"""


bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
ACLIndex = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class jumpscale_bcdb_test_house(ACLIndex,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init()