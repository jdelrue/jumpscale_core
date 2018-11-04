
from Jumpscale import j
from .BCDBTableMeta import ConfigManagerMeta

JSBASE = j.application.JSBaseClass


class ConfigManagerFactory(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.__jslocation__ = "j.tools.configmanager2"
        self._bcdb = None
        self.config_instances = {}  #key is the name
        self.config_models = {}



    @property
    def bcdb(self):
        if not self._bcdb:
            self._bcdb = j.data.bcdb.latest
            if self._bcdb == None:
                self._bcdb =  j.data.bcdb.get(name="core",dbclient=j.core.db)

        return self._bcdb

    def _url_normalize(self,url):
        if not url.startswith("jumpscale.config."):
            url="jumpscale.config.%s"%url
        url=j.core.text.strip_to_ascii_dense(url)
        url=url.lower()
        return url


    def get(self, url, instance="main", cache=True):
        url = self._url_normalize(url)
        key = "%s__%s"%(url,instance)
        if not cache or not key in self.config_instances:
            #make sure model is known
            if not url in self.config_models:
                self.config_models[url]=self.bcdb.model_get_from_schema(url, namespace="config", reload=False)
            model = self.config_models[url]

            q = model.index.select().where(model.index.instance == instance)
            if len(q)==0:
                #model does not exist yet
                o = model.new()
            else:
                j.shell()
                o = model.get(id=q[0])

            o.is_config = True

            self.config_instances[key] = o

        return self.config_instances[key]

    def model_get(self,url):
        """

        :param url: url of config schema e.g. client.redis
        :return:
        """
        url = self._url_normalize(url)
        if not url in self.config_models:
            raise RuntimeError("configmodel for %snot found"%url)
        return self.config_models[url]


    def init(self):
        """
        will intialize config database, CAREFUL ALL DATA WILL BE LOST
        :return:
        """
        self._meta


    def get_from_schema(self,schema, instance="main"):
        """

        :param schema: is the schema of the config, needs to have a key inside
        :param instance:
        :return:
        """
        if not j.data.types.string.check(schema):
            raise RuntimeError("schema needs to be passed as str")
        def process(txt):
            """
            makes sure the index* is part of schema and always indexed
            :param txt:
            :return:
            """
            txt = j.core.text.strip(txt)
            out = ""
            for line in txt.split("\n"):
                if line.startswith("@"):
                    out+="%s\n"%line
                    out+="instance* = \"\"\n"
                    continue
                if line.startswith("instance"):
                    continue
                out+="%s\n"%line
            return out
        schema = process(schema)
        schema = j.data.schema.add(schema)
        return self.get(instance=instance,url=schema.url)

    def test(self,start=True):
        """
        js_shell 'j.data.configmanager.test()'
        """
        schema = """
        @url = myconfig.test
        
        llist2 = "" (LS) #L means = list, S=String        
        nr = 4
        date_start = 0 (D)
        description = ""
        cost = "10 USD" (N)
        alist =  (LI)
        """
        o = self.get_from_schema(schema=schema,instance="main")
        o.description = "something"
        o.cost = "10 EUR"
        o.alist = [2,3]

        j.shell()

        schema = """
        @url = myconfig.test2
        instance* = ""
        nr = 4
        description2 = ""
        """
        m2 = self.get_from_schema(schema=schema)
        o2 = m2.new()
        o2.description = "something"
        o2.nr = 7
        m2.set(o)

        j.shell()
