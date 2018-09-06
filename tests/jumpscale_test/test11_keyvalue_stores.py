""" unit test for key-value stores.

    currently only does etcd, should be possible to use on redis,
    as it has a similar high-level API
"""

import unittest
from .testcases_base import TestcasesBase
from parameterized import parameterized


class TestEtcdNamespace(TestcasesBase):

    def test001_etcd_namespaces(self):
        etcd = self.j.clients.etcd.get()
        ns = self.random_string()

        # check random namespace, create it, check it, delete and check again
        self.assertFalse(etcd.namespace_exists(ns))
        db = etcd.namespace_get(ns)
        self.assertTrue(etcd.namespace_exists(ns))
        etcd.namespace_del(ns)
        self.assertFalse(etcd.namespace_exists(ns))


class TestEtcd(TestcasesBase):

    def setUp(self):
        super().setUp()
        self.etcd = self.j.clients.etcd.get()
        self.ns = self.random_string()
        self.db = self.etcd.namespace_get(self.ns)

    def tearDown(self):
        self.etcd.namespace_del(self.ns)
        super().tearDown()

    def test001_etcd_getset(self):

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

        # delete once (should be ok), delete again (raises KeyError)
        self.db.delete('hello')
        self.assertRaises(KeyError, self.db.delete, 'hello') # second delete

    def test002_etcd_incr(self):

        for i in range(1, 10):
            value = self.db.incr('hello')
            self.assertTrue(value == i)

    @parameterized.expand(['', 'dir'])
    def test002_etcd_keys(self, dirname):

        d = {}
        if dirname:
            _dirname = "%s/" % dirname
        else:
            _dirname = dirname

        # store in database, take a mirror-copy in dict d...
        for i in range(10):
            k = '%skey%d' % (_dirname, i)
            v = b'value%d' % i
            self.db.set(k, v)
            d[k] = v

        keys = self.db.keys(dirname)
        keys.sort()
        if dirname:
            l = len(dirname)+1
        else:
            l = 0
        dkeys = list(map(lambda x: x[l:], d.keys()))
        dkeys.sort()

        print (keys, dkeys)
        self.assertTrue(keys == dkeys)
