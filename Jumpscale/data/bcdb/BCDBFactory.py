from Jumpscale import j

from .BCDB import BCDB
import os
import sys
import redis

JSBASE = j.application.JSBaseClass


class BCDBFactory(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.__jslocation__ = "j.data.bcdb"
        self._path = j.sal.fs.getDirName(os.path.abspath(__file__))
        self._code_generation_dir = None
        self.bcdb_instances = {}  #key is the name
        self.logger_enable()


    def get(self, name, zdbclient=None, cache=True):
        if not name in self.bcdb_instances or cache==False:
            if j.data.types.string.check(zdbclient):
                raise RuntimeError("zdbclient cannot be str")
            self.bcdb_instances[name] = BCDB(zdbclient=zdbclient,name=name)
        return self.bcdb_instances[name]

    def redis_server_start(self, name="test",
                                 ipaddr="localhost",
                                 port=6380,
                                 background=False,
                                 secret="123456",
                                 zdbclient_addr="localhost",
                                 zdbclient_port=9900,
                                 zdbclient_namespace="test",
                                 zdbclient_secret="1234",
                                 zdbclient_mode="seq",
                          ):

        """
        start a redis server on port 6380 on localhost only

        you need to feed it with schema's

        trick: use RDM to investigate (Redis Desktop Manager) to investigate DB.

        js_shell "j.data.bcdb.redis_server_start(background=True)"


        :return:
        """
        # try:
        #     zdbclient = j.clients.zdb.client_get(nsname=zdbclient_namespace, addr=zdbclient_addr, port=zdbclient_port,
        #                                          secret=zdbclient_secret, mode=zdbclient_mode)
        # except Exception as e:
        #     if str(e).find("Access denied")!=-1:
        #         print("TIP: if you want to create an empty ZDB server in test mode with admin secret:123456 do:")
        #         print("TIP: ''")
        #         raise RuntimeError("cannot connect to ZDB server, check arguments, server: %s:%s namespace:%s, check secret"%(zdbclient_addr,zdbclient_port,zdbclient_namespace))
        # if zdbclient_reset:
        #     #a hack untill we have delete support in ZDB per namespace
        #     adminsecret = "123456"

        #     j.shell()

        if background:

            args="ipaddr=\"%s\", "%ipaddr
            args+="name=\"%s\", "%name
            args+="port=%s, "%port
            args+="secret=\"%s\", "%secret
            args+="zdbclient_addr=\"%s\", "%zdbclient_addr
            args+="zdbclient_port=%s, "%zdbclient_port
            args+="zdbclient_namespace=\"%s\", "%zdbclient_namespace
            args+="zdbclient_secret=\"%s\", "%zdbclient_secret
            args+="zdbclient_mode=\"%s\", "%zdbclient_mode


            cmd = 'js_shell \'j.data.bcdb.redis_server_start(%s)\''%args
            j.tools.tmux.execute(
                cmd,
                session='main',
                window='bcdb_server',
                pane='main',
                session_reset=False,
                window_reset=True
            )
            j.sal.nettools.waitConnectionTest(ipaddr=ipaddr, port=port, timeoutTotal=5)
            r = j.clients.redis.get(ipaddr=ipaddr, port=port, password=secret)
            assert r.ping()

        else:
            zdbclient = j.clients.zdb.client_get(nsname=zdbclient_namespace, addr=zdbclient_addr, port=zdbclient_port,
                                                 secret=zdbclient_secret, mode=zdbclient_mode)
            bcdb=self.get(name,zdbclient=zdbclient)
            bcdb.redis_server_start(port=port)



    @property
    def code_generation_dir(self):
        if not self._code_generation_dir:
            path = j.sal.fs.joinPaths(j.dirs.VARDIR, "codegen", "models")
            j.sal.fs.createDir(path)
            if path not in sys.path:
                sys.path.append(path)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, "__init__.py"))
            self.logger.debug("codegendir:%s" % path)
            self._code_generation_dir = path
        return self._code_generation_dir

    def _load_test_model(self,reset=True,sqlitestor=False):

        schema = """
        @url = despiegk.test
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        token_price* = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        llist5 = "1,2,3" (LI)
        U = 0.0
        #pool_type = "managed,unmanaged" (E)  #NOT DONE FOR NOW
        """

        if sqlitestor:
            bcdb = j.data.bcdb.get(name="test", zdbclient=None)
        else:
            if self.bcdb_instances == {}:
                self.logger.debug("start bcdb in tmux")
                j.servers.zdb.start_test_instance(reset=reset)
                zdbclient_admin = j.servers.zdb.client_admin_get()
                zdbclient = zdbclient_admin.namespace_new("test",secret="1234")
                bcdb = j.data.bcdb.get(name="test", zdbclient=zdbclient)
            else:
                zdbclient = j.servers.zdb.client_get("test", secret="1234")
                bcdb = self.bcdb_instances["test"]

        if reset:
            bcdb.reset_data()  # empty

        schemaobj = j.data.schema.get(schema)
        bcdb.model_get_from_schema(schemaobj)

        self.logger.debug("bcdb already exists")

        model = bcdb.model_get("despiegk.test")

        assert model.get_all()==[]

        return bcdb,model

    def test(self, name="", start=True):
        """
        following will run all tests

        js_shell 'j.data.bcdb.test()'

        """
        if start:
            j.clients.zdb.testdb_server_start_client_admin_get(reset=True, mode="seq")

        self._test_run(name=name)



    # def test3(self, start=True):
    #     """
    #     js_shell 'j.data.bcdb.test3(start=False)'
    #     """
    #

    def test4(self,start=True):
        """
        js_shell 'j.data.bcdb.test4(start=True)'

        this is a test for the redis interface
        """
        if start:
            j.servers.zdb.start_test_instance(reset=True,namespaces=["test"])
            self.redis_server_start(port=6380, background=True)
            j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeoutTotal=5)

        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        S = """
        @url = despiegk.test2
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        token_price* = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        """
        S=j.core.text.strip(S)
        self.logger.debug("set schema to 'despiegk.test2'")
        r.set("schemas:despiegk.test2", S)
        self.logger.debug('compare schema')
        s2=r.get("schemas:despiegk.test2")
        #test schemas are same

        assert _compare_strings(S, s2)

        self.logger.debug("delete schema")
        r.delete("schemas:despiegk.test2")
        self.logger.debug("delete data")
        r.delete("objects:despiegk.test2")

        r.set("schemas:despiegk.test2", S)

        self.logger.debug('there should be 0 objects')
        assert r.hlen("objects:despiegk.test2") == 0


        schema=j.data.schema.get(S)

        self.logger.debug("add objects")
        def get_obj(i):
            o = schema.new()
            o.nr = i
            o.name= "somename%s"%i
            o.token_price = "10 EUR"
            return o

        try:
            o = get_obj(0)
            id = r.hset("objects:despiegk.test2", 0, o._json)
            raise RuntimeError("should have raise runtime error when trying to write to index 0")
        except redis.exceptions.ResponseError as err:
            # runtime error is expected when trying to write to index 0
            pass

        for i in range(1, 11):
            # print(i)
            o = get_obj(i)
            id = r.hset("objects:despiegk.test2","new",o._json)

        self.logger.debug("validate list")
        cl=j.clients.zdb.client_get()
        assert cl.list() == [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


        self.logger.debug("validate added objects")
        #there should be 10 items now there
        assert r.hlen("objects:despiegk.test2") == 10
        assert r.hdel("objects:despiegk.test2", 5) == 1
        assert r.hlen("objects:despiegk.test2") == 9
        assert r.hget("objects:despiegk.test2", 5) == None
        assert r.hget("objects:despiegk.test2", 5) == r.hget("objects:despiegk.test2", "5")

        assert cl.list() == [0, 2, 3, 4, 6, 7, 8, 9, 10, 11]

        resp = r.hget("objects:despiegk.test2",i+1)
        json = j.data.serializers.json.loads(resp)
        json2 = j.data.serializers.json.loads(o._json)
        json2['id'] = i+1
        assert json == json2

        self.logger.debug("update obj")
        o.name="UPDATE"
        r.hset("objects:despiegk.test2",11, o._json)
        resp = r.hget("objects:despiegk.test2", 11)
        json3 = j.data.serializers.json.loads(resp)
        assert json3['name'] == "UPDATE"
        json4 = j.data.serializers.json.loads(o._json)
        json4['id'] = 11

        assert json != json3 #should have been updated in db, so no longer same
        assert json4 == json3

        try:
            r.hset("objects:despiegk.test2",1, o._json)
        except Exception as e:
            assert str(e).find("cannot update object with id:1, it does not exist")!=-1
            #should not be able to set because the id does not exist
        #restart redis lets see if schema's are there autoloaded
        self.redis_server_start(port=6380, background=True)
        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        assert r.hlen("objects:despiegk.test2") == 9

        json =  r.hget("objects:despiegk.test2", 3)
        ddict = j.data.serializers.json.loads(json)

        assert ddict == {'name': 'somename2',
             'email': '',
             'nr': 2,
             'date_start': 0,
             'description': '',
             'token_price': '10 EUR',
             'cost_estimate': 0.0,
             'llist2': [],
             'llist': [],
             'llist3': [],
             'llist4': [],
             'id': 3}

        self.logger.debug("clean up database")
        r.delete("objects:despiegk.test2")

        #there should be 0 objects
        assert r.hlen("objects:despiegk.test2") == 0

        cl=j.clients.zdb.client_get()  #need to get new client because namespace removed because of the delete
        assert cl.list() == [0]

        self.logger.debug("TEST OK")


    def _test4_populate_data(self,start=False):
        """
        js_shell 'j.data.bcdb.test5_populate_data(start=True)'

        this populates  redis with data so we can test e.g. with RDM (redis desktop manager)
        """
        if start:
            j.servers.zdb.start_test_instance(reset=True,namespaces=["test"])
            self.redis_server_start(port=6380, background=True)
            j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeoutTotal=5)

        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        S = """
        @url = despiegk.test2
        llist2 = "" (LS)
        name* = ""
        email* = ""
        nr* = 0
        date_start* = 0 (D)
        description = ""
        token_price* = "10 USD" (N)
        cost_estimate:hw_cost = 0.0 #this is a comment
        llist = []
        llist3 = "1,2,3" (LF)
        llist4 = "1,2,3" (L)
        """
        S=j.core.text.strip(S)
        self.logger.debug("set schema to 'despiegk.test2'")
        r.set("schemas:despiegk.test2", S)
        self.logger.debug('compare schema')
        schema=j.data.schema.get(S)

        self.logger.debug("add objects")
        def get_obj(i):
            o = schema.new()
            o.nr = i
            o.name= "somename%s"%i
            o.token_price = "10 EUR"
            return o

        for i in range(1, 11):
            # print(i)
            o = get_obj(i)
            id = r.hset("objects:despiegk.test2","new",o._json)

        S = """
        @url = another.test
        name* = ""
        nr* = 0
        token_price* = "10 USD" (N)
        """
        S=j.core.text.strip(S)
        self.logger.debug("set schema to 'another.test'")
        r.set("schemas:another.test", S)
        schema=j.data.schema.get(S)
        for i in range(1, 100):
            # print(i)
            o = get_obj(i)
            id = r.hset("objects:another.test","new",o._json)






def _compare_strings(s1, s2):
    # TODO: move somewhere into jumpsclale tree
    def convert(s):
        if isinstance(s, bytes):
            s = s.decode()
        return s

    return convert(s1).strip() == convert(s2).strip()
