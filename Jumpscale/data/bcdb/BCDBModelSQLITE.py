from Jumpscale import j

from .BCDBModel import  BCDBModel

class BCDBModelSQLITE(BCDBModel):


    def _delete2(self,id):
        j.shell()
        return self.zdbclient.delete(id)

    def _set2(self,obj,data):
        j.shell()
        if obj.id is None:
            # means a new one
            obj.id = self.zdbclient.set(data)
            if self.write_once:
                obj.readonly = True
            self.logger.debug("NEW:\n%s"%obj)
        else:
            try:
                self.zdbclient.set(data, key=obj.id)
            except Exception as e:
                if str(e).find("only update authorized")!=-1:
                    raise RuntimeError("cannot update object:%s\n with id:%s, does not exist"%(obj,obj.id))
                raise e

        return obj.id


    def _get2(self,id):
        return self.zdbclient.get(id)


    def __str__(self):
        out = "model_sqlite:%s\n" % self.url
        out += j.core.text.prefix("    ", self.schema.text)
        return out
