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

        self.assertRaises(KeyError, db.get, 'hello')

