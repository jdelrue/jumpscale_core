""" unit test for key-value stores.

    currently only does etcd, should be possible to use on redis,
    as it has a similar high-level API
"""

import unittest
from .testcases_base import TestcasesBase
from parameterized import parameterized


class TestCoreDNS(TestcasesBase):

    def setUp(self):
        super().setUp()
        self.d = self._j.clients.coredns.get()
        #self.zone = self.random_string()
        self.zone = ''

    def tearDown(self):
        #self.etcd.namespace_del(self.ns)
        super().tearDown()

    def _test001_etcd_getset(self):

        # check get and delete on non-existent value
        self.assertRaises(KeyError, self.db.get, 'hello')
        self.assertRaises(KeyError, self.db.delete, 'hello')

        # add value and check it
        self.db.set('hello', b'val')
        get = self.db.get('hello')
        self.assertTrue(get == b'val')

        # change value and check it
        self.db.set('hello', b'newval')
        get = self.db.get('hello')
        self.assertTrue(get == b'newval')

    @parameterized.expand([('x1', 'txt'),
                           ('', 'txt'),
                           ('', 'cname'),
                           ('', 'srv'),
                           ('', 'aaaa'),
                           ('', None)])
    def test002_etcd_keys(self, subzone, qtype):

        if subzone:
            zone = "%s/%s" % (self.zone, subzone)

        z = d.zone_get(zone)

        print (z.get_records(subzone, qtype))

        return

        z = d.zone_get('local/skydns/x5')
        print (z.get_records('','srv'))

        z = d.zone_get('local/skydns/x1')
        print (z.get_records('','txt'))

        z = d.zone_get('local/skydns/x3')
        print (z.get_records(''))
        print (z.get_records('', 'aaaa'))
