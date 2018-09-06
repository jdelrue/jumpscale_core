import unittest
from .testcases_base import TestcasesBase


class TestJDataTypes(TestcasesBase):

    def test001_etcd_namespaces(self):
        etcd = self.j.clients.etcd.get()
        ns = self.random_string()

        # check random namespace, create it, check it, delete and check again
        self.assertFalse(etcd.namespace_exists(ns))
        db = etcd.namespace_get(ns)
        self.assertTrue(etcd.namespace_exists(ns))
        etcd.namespace_del(ns)
        self.assertFalse(etcd.namespace_exists(ns))

    def test002_etcd_getset(self):
        etcd = self.j.clients.etcd.get()
        ns = self.random_string()
        db = etcd.namespace_get(ns)

        # check get and delete on non-existent value
        self.assertRaises(KeyError, db.get, 'hello')
        self.assertRaises(KeyError, db.delete, 'hello')

        # add value and check it
        db.set('hello', b'val')
        get = db.get('hello')
        self.assertTrue(get == b'val')

        # change value and check it
        db.set('hello', b'newval')
        get = db.get('hello')
        self.assertTrue(get == b'newval')

        # delete once (should be ok), delete again (raises KeyError)
        db.delete('hello')
        self.assertRaises(KeyError, db.delete, 'hello') # second delete
