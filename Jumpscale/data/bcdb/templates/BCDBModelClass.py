from Jumpscale import j
#GENERATED CODE CAN CHANGE

SCHEMA="""
{{schema_text}}
"""

import types

bcdb = j.data.bcdb.latest
schema = j.data.schema.get(SCHEMA)
ACLIndex = bcdb._BCDBModelIndexClass_generate(schema,__file__)
MODEL_CLASS = bcdb._BCDBModelClass_get()


class Model{{schema.key}}(ACLIndex,MODEL_CLASS):
    def __init__(self):
        MODEL_CLASS.__init__(self, bcdb=bcdb,schema=schema)
        self.write_once = False
        self._init_index()
