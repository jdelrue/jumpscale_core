from Jumpscale import j
import os
import capnp

ModelBaseCollection = j.data.capnp.getModelBaseClassCollection()
ModelBase = j.data.capnp.getModelBaseClass()
# from Jumpscale.clients.tarantool.KVSInterface import KVSTarantool

JSBASE = j.application.jsbase_get_class()


class TemplateModel(ModelBase):
    '''
    '''
    def __init__(self, key="", new=False, collection=None):
        ModelBase.__init__(self, key=key, new=new, collection=collection)

    def index(self):
        #no need to put indexes because will be done by capnp
        pass

    def save(self):
        self.reSerialize()
        self._pre_save()
        buff = self.dbobj.to_bytes()                    
        return self.collection.client.call("model_template_set",(buff))

    def delete(self):                    
        return self.collection.client.call("model_template_del",(self.key))


class TemplateCollection(ModelBaseCollection):
    '''
    This class represent a collection of Templates
    It's used to list/find/create new Instance of Template Model object
    '''

    def __init__(self):
        category = 'template'
        namespace = ""

        # instanciate the KVS interface on top of tarantool
        # cl = j.clients.tarantool.client_get()  # will get the tarantool from the config file, the main connection
        # db = KVSTarantool(cl, category)
        # mpath = j.sal.fs.getDirName(os.path.abspath(__file__)) + "/model.capnp"
        # SchemaCapnp = j.data.capnp.getSchemaFromPath(mpath, name='Template')

        self.client =  j.clients.tarantool.client_get() #will get the tarantool from the config file, the main connection
        mpath=j.sal.fs.getDirName(os.path.abspath(__file__))+"/model.capnp"
        SchemaCapnp=j.data.capnp.getSchemaFromPath(mpath,name='Template')
        super().__init__(SchemaCapnp, category=category, namespace=namespace, modelBaseClass=TemplateModel, db=self.client, indexDb=self.client)

        self._init()

    def new(self):
        return TemplateModel(collection=self, new=True)

    def get(self,key):                    
        resp=self.client.call("model_template_get",key)
        if len(resp.data) <= 1 and len(resp.data[0]) > 2:
            raise KeyError("value for %s not found" % key)
        # taarantool doesn't support binary value, dont think this is true !
        value = resp.data[0][1]
        if isinstance(value, (str, bytes)):
            value = base64.b64decode(value)
        return value


    # BELOW IS ALL EXAMPLE CODE WHICH NEEDS TO BE REPLACED

    def list(self, actor="", service="", action="", state="", serviceKey="", fromEpoch=0, toEpoch=9999999999999,tags=[]):
        raise NotImplementedError()
        return res
    
    def find(self, actor="", service="", action="", state="", serviceKey="", fromEpoch=0, toEpoch=9999999999999, tags=[]):
        raise NotImplementedError()
        res = []
        for key in self.list(actor, service, action, state, serviceKey, fromEpoch, toEpoch, tags):
            if self.get(key):
                res.append(self.get(key))
        return res

