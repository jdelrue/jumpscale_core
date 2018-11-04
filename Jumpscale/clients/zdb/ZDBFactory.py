import os
import uuid
from pprint import pprint

from Jumpscale import j

from .ZDBAdminClient import ZDBAdminClient
from .clients_impl import ZDBClientDirectMode, ZDBClientSeqMode, ZDBClientUserMode

JSBASE = j.application.JSBaseClass


_client_map = {
    'seq': ZDBClientSeqMode,
    'sequential': ZDBClientSeqMode,
    'user': ZDBClientUserMode,
    'direct': ZDBClientDirectMode,
}


class ZDBFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.clients.zdb"
        JSBASE.__init__(self)

    def client_admin_get(self, addr="localhost", port=9900, secret="123456", mode='seq'):
        return ZDBAdminClient(addr=addr, port=port, secret=secret, mode=mode)

    def client_get(self, nsname="test", addr="localhost", port=9900, secret="1234", mode="seq"):
        """
        :param nsname: namespace name
        :param addr:
        :param port:
        :param secret:
        :return:
        """
        if mode not in _client_map:
            return ValueError("mode %s not supported" % mode)
        klass = _client_map[mode]
        return klass(addr=addr, port=port, secret=secret, nsname=nsname)

    def testdb_server_start_client_admin_get(self, reset=False, mode="seq", secret="123456"):
        """
        will start a ZDB server in tmux (will only start when not there yet or when reset asked for)
        erase all content
        and will return client to it

        """

        j.servers.zdb.mode = mode
        j.servers.zdb.name = "test"

        j.servers.zdb.start(reset=reset)

        # if secrets only 1 secret then will be used for all namespaces
        cl = self.client_admin_get(secret=secret)
        return cl


    def test(self, name="", start=True):
        """
        js_shell 'j.clients.zdb.test(start=True)'

        """


        if start:
            j.clients.zdb.testdb_server_start_client_admin_get(reset=True, mode="seq")

        self._test_run(name=name)


