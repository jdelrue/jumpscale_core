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
        self.latest=None
        self.bcdb_instances = {}  #key is the name
        self.logger_enable()

    def new(self, name, zdbclient=None, cache=True):
        if cache==False or not name in self.bcdb_instances:
            self.logger.info("new bcdb:%s"%name)
            if self.latest is not None:
                self.latest.stop()
            if zdbclient!=None and j.data.types.string.check(zdbclient):
                raise RuntimeError("zdbclient cannot be str")
            self.bcdb_instances[name] = BCDB(zdbclient=zdbclient,name=name)
        return self.bcdb_instances[name]


    def get(self, name):
        if name not in self.bcdb_instances:
            raise RuntimeError("did not find bcdb with name:%s"%name)
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

        if zdbclient_addr is None, will use sqlite embedded backend

        trick: use RDM to investigate (Redis Desktop Manager) to investigate DB.

        js_shell "j.data.bcdb.redis_server_start(background=True)"

        js_shell "j.data.bcdb.redis_server_start(background=False,zdbclient_addr=None)"


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
            if zdbclient_addr not in ["None",None]:
                zdbclient = j.clients.zdb.client_get(nsname=zdbclient_namespace, addr=zdbclient_addr, port=zdbclient_port,
                                                 secret=zdbclient_secret, mode=zdbclient_mode)
            else:
                zdbclient=None
            bcdb=self.new(name,zdbclient=zdbclient,cache=False)
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

        if self.latest != None:
            self.latest.stop()

        if sqlitestor:
            bcdb = j.data.bcdb.new(name="test", zdbclient=None,cache=False)
            assert j.data.bcdb.latest.zdbclient == None
        else:
            if self.bcdb_instances == {}:
                self.logger.debug("start bcdb in tmux")
                j.servers.zdb.start_test_instance(reset=reset)
                zdbclient_admin = j.servers.zdb.client_admin_get()
                zdbclient = zdbclient_admin.namespace_new("test",secret="1234")
                bcdb = j.data.bcdb.new(name="test", zdbclient=zdbclient)
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


