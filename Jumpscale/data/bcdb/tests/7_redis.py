from Jumpscale import j

import redis

def main(self):
    """
    to run:

    js_shell 'j.data.bcdb.test(name="redis")'

    use a bcdb which is using sqlite

    REQUIREMENTS:

    ```
    apt-get install python3.6-dev
    mkdir -p /root/opt/bin
    js_shell 'j.servers.zdb.build()'
    pip3 install pycapnp peewee cryptocompare

    #MAKE SURE YOU DON't USE THE SSH CONFIG, USE THE LOCAL CONFIG
    js_shell 'j.tools.myconfig'

    ```


    """

    #TODO: need to use prefab to check the prerequisites are installed if not DO



    def do(zdb=False):


        j.sal.nettools.waitConnectionTest("127.0.0.1", port=6380, timeoutTotal=20)

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

        self.logger.debug("delete data")
        r.delete("objects:despiegk.test2")  #removes the data mainly tested on sqlite db now

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
            print(i)
            o = get_obj(i)
            id = r.hset("objects:despiegk.test2","new",o._json)

        if zdb:
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

        if zdb:
            self.logger.debug("validate list2")
            assert cl.list() == [0, 2, 3, 4, 6, 7, 8, 9, 10, 11]

        resp = r.hget("objects:despiegk.test2",i+1)
        assert resp == None
        resp = r.hget("objects:despiegk.test2",i)
        json = j.data.serializers.json.loads(resp)
        json2 = j.data.serializers.json.loads(o._json)
        json2['id'] = i
        assert json == json2



        self.logger.debug("update obj")
        o.name="UPDATE"
        r.hset("objects:despiegk.test2",i, o._json)
        resp = r.hget("objects:despiegk.test2", i)
        json3 = j.data.serializers.json.loads(resp)
        assert json3['name'] == "UPDATE"
        json4 = j.data.serializers.json.loads(o._json)
        json4['id'] = i

        assert json != json3 #should have been updated in db, so no longer same
        assert json4 == json3

        #should be none because does not exist
        assert r.hget("objects:despiegk.test2",15) == None

        try:
            r.hset("objects:despiegk.test2",15, o._json)
            raise RuntimeError("should have been in error")
        except Exception as e:
            assert str(e).find("cannot update object with id:15, it does not exist")!=-1
            #should not be able to set because the id does not exist

    def check_after_restart():
        r = j.clients.redis.get(ipaddr="localhost", port=6380)

        assert r.hlen("objects:despiegk.test2") == 9

        json =  r.hget("objects:despiegk.test2", 3)
        ddict = j.data.serializers.json.loads(json)

        assert ddict == {'name': 'somename3',
             'email': '',
             'nr': 3,
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


    #SQLITE BACKEND
    self.redis_server_start(port=6380, background=True, zdbclient_addr=None)
    do()
    #restart redis lets see if schema's are there autoloaded
    self.redis_server_start(port=6380, background=True, zdbclient_addr=None)
    check_after_restart()


    # #ZDB test
    # c = j.clients.zdb.client_admin_get()
    # c.namespace_new("test", secret="1234")
    # self.redis_server_start(port=6380, background=True)
    # do()

    self.logger.debug("TEST OK")

    return ("OK")





def _compare_strings(s1, s2):
    # TODO: move somewhere into jumpscale tree
    def convert(s):
        if isinstance(s, bytes):
            s = s.decode()
        return s

    return convert(s1).strip() == convert(s2).strip()
