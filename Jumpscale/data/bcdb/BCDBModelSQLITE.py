from Jumpscale import j

from .BCDBModel import  BCDBModel

class BCDBModelSQLITE(BCDBModel):


    def _delete2(self,id):
        return self.bcdb.kvs.delete(id)

    def _set2(self,obj,data):
        if obj.id is None:
            # means a new one
            obj.id = self.bcdb.kvs.set(key=None, val=data)
            if self.write_once:
                obj.readonly = True
            self.logger.debug("NEW:\n%s"%obj)
        else:
            if self.bcdb.kvs.get(obj.id) is None:
                #new one
                raise RuntimeError("cannot update object:%s\n with id:%s, does not exist"%(obj,obj.id))
            else:
                self.bcdb.kvs.set(key=obj.id, val=data)

        return obj.id


    def _get2(self,id):
        return self.bcdb.kvs.get(id)


    def __str__(self):
        out = "model_sqlite:%s\n" % self.url
        out += j.core.text.prefix("    ", self.schema.text)
        return out
