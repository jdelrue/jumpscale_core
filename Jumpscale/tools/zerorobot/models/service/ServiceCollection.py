from Jumpscale import j
import os
import capnp

ModelBaseCollection = j.data.capnp.getModelBaseClassCollection()
ModelBase = j.data.capnp.getModelBaseClass()
from Jumpscale.clients.tarantool.KVSInterface import KVSTarantool

JSBASE = j.application.jsbase_get_class()


class ServiceModel(ModelBase):
    '''
    '''
    def __init__(self, key="", new=False, collection=None):
        ModelBase.__init__(self, key=key, new=new, collection=collection)

class ServiceCollection(ModelBaseCollection):
    '''
    This class represent a collection of Services
    It's used to list/find/create new Instance of Service Model object
    '''

    def __init__(self):
        category = 'service'
        namespace = ""

        # instanciate the KVS interface on top of tarantool
        cl = j.clients.tarantool.client_get()  # will get the tarantool from the config file, the main connection
        db = KVSTarantool(cl, category)

        mpath = j.sal.fs.getDirName(os.path.abspath(__file__)) + "/model.capnp"
        SchemaCapnp = j.data.capnp.getSchemaFromPath(mpath, name='Service')

        super().__init__(SchemaCapnp, category=category, namespace=namespace, modelBaseClass=ServiceModel, db=db, indexDb=db)

    def new(self):
        return ServiceModel(collection=self, new=True)

    def get(self, key):
        return ServiceModel(key=key, collection=self, new=False)

    # BELOW IS ALL EXAMPLE CODE WHICH NEEDS TO BE REPLACED

    def list(self):
        """
        list all key in this collection
        """
        return self._db.list()

    def find(self):
        raise NotImplementedError()

    def delete(self, key):
        self._db.delete(key=key)
