""" unit test for j.clients.coredns

    for this test to work, etcd and coredns must have been set up
    and properly configured, and "dig" must have been installed
    (apt-get install dnsutils)
"""

import unittest
from .testcases_base import TestcasesBase
from parameterized import parameterized
import subprocess

# we're testing j.clients.coredns here, not jumpscale executor, therefore
# use subprocess directly.
def dig(zone, qtype):
    args = ['dig']
    if qtype:
        args += ['-t', qtype]
    args.append("@localhost")
    args.append(zone)
    print (args)
    resp = subprocess.check_output(args)
    resp = resp.decode()
    resp = resp.split('\n')
    resp = map(str.strip, resp) # strip whitespace
    resp = filter(None, resp) # filter empty lines
    resp = filter(lambda x: not x.startswith(';'), resp) # filter comments
    resp = filter(lambda x: 'SOA' not in x, resp) # filter SOA, XXX not v well!
    return list(resp)

def split_whitespace(lines):
    return list(map(str.split, lines))

def compare_output(_coredns, _dig):
    coredns = list(map(str, _coredns)) # use CoreDNS.RR.__str__ here
    coredns = split_whitespace(coredns)
    dig = split_whitespace(_dig)
    coredns.sort()
    dig.sort()
    _coredns = list(map(lambda x: "c: '%s'" % '\t'.join(x), coredns)) 
    _dig = list(map(lambda x: "d: '%s'" % '\t'.join(x), dig)) 
    _coredns = '\n'.join(_coredns)
    _dig = '\n'.join(_dig)
    assert coredns == dig, "coredns not same answers as dig\n" \
                           "%s\n%s\n" % (_coredns, _dig)


records_for_test = [
                       ('', 'a', '1.1.1.1'),
                       ('x1', 'txt', 'this is a random text message'),
                       ('x2', 'cname', 'cn1.skydns.local skydns.local'),
                       ('x5', 'srv', 'skydns-local.server', 10, 8080),
                       ('x3', 'aaaa', '2003::8:1'),
                    ]

def add_record(d, zzone, key, rtype, rrdata, priority=None, port=None):

        ResourceRecord = d.ResourceRecord

        if key:
            zone = "%s/%s" % (zzone, key)
        else:
            zone = zzone

        z = d.zone_get(zone)

        name = z._get_zonename() + "."
        rr = ResourceRecord(name, rtype, ttl=60,
                               rrdata=rrdata, port=port, priority=priority)
        z.set('', rr)

        return z, rr, zone

def add_records(d, zzone):

        for r in records_for_test:
            if len(r) == 3:
                (key, rtype, name) = r
                port = None
                priority = None
            else:
                (key, rtype, name, priority, port) = r

            add_record(d, zzone, key, rtype, name, priority, port)


class TestCoreDNSSetGet(TestcasesBase):

    @parameterized.expand(records_for_test)
    def test001_etcd_set(self, key, rtype, rrdata, priority=None, port=None):

        self.d = self._j.clients.coredns.get()
        self.zone = "local/%s" % self.random_string()

        # check get and delete on non-existent value
        #self.assertRaises(KeyError, self.db.get, 'hello')
        #self.assertRaises(KeyError, self.db.delete, 'hello')

        (z, rr, zone) = add_record(self.d, self.zone,
                                        key, rtype, rrdata, priority, port)
        q = z.get('')

        self.assertTrue(str(q) == str(rr), "%s != %s" % (str(q), str(rr)))

        self.d.zone_del(zone) # bit drastic, deletes entire zone on each expand

class TestCoreDNS(TestcasesBase):

    def setUp(self):
        super().setUp()
        # create a random zone
        self.d = self._j.clients.coredns.get()
        #self.zone = "local/%s" % self.random_string()
        self.zone = "local/skydns"

    def tearDown(self):
        # get etcd direct and call delete on all records in the zone
        #etcd = self.d.etcd
        #etcd.delete_all()

        # now just remove the zone (doesn't remove data: done above)
        #self._j.clients.coredns.zone_del(self.zone)
        super().tearDown()

    def _test001_etcd_setget(self):

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

    @parameterized.expand([
                           ('', 'a'),
                           ('', 'txt'),
                           ('', 'cname'),
                           ('', 'srv'),
                           ('', 'aaaa'),
                           ('x1', 'a'),
                           ('x1', 'txt'),
                           ('x3', 'srv'),
                           ('x5', 'srv'),
                           ('x3', 'aaaa'),
                           ('', None),
                           ('x2', 'txt'), # should be empty
                           ('cn1', 'srv'), # should be empty
                           ('cn1', 'aaaa'), # should be empty
                           ])
    def test002_etcd_keys(self, subzone, qtype):

        if subzone:
            zone = "%s/%s" % (self.zone, subzone)
        else:
            zone = self.zone
        dzone = zone.split("/")
        dzone.reverse()
        dzone = '.'.join(dzone)

        z = self.d.zone_get(zone)

        cdns = z.get_records('', qtype)
        dresp = dig(dzone, qtype)
        compare_output(cdns, dresp)

        return

        z = d.zone_get('local/skydns/x5')
        print (z.get_records('','srv'))

        z = d.zone_get('local/skydns/x1')
        print (z.get_records('','txt'))

        z = d.zone_get('local/skydns/x3')
        print (z.get_records(''))
        print (z.get_records('', 'aaaa'))

    # for testing of things that don't work, get a different test name
    @parameterized.expand([
                          ])
    def test003_etcd_keys_fail(self, subzone, qtype):

        if subzone:
            zone = "%s/%s" % (self.zone, subzone)
        else:
            zone = self.zone
        dzone = zone.split("/")
        dzone.reverse()
        dzone = '.'.join(dzone)

        z = self.d.zone_get(zone)

        cdns = z.get_records('', qtype)
        dresp = dig(dzone, qtype)
        compare_output(cdns, dresp)

        return

        z = d.zone_get('local/skydns/x5')
        print (z.get_records('','srv'))

        z = d.zone_get('local/skydns/x1')
        print (z.get_records('','txt'))

        z = d.zone_get('local/skydns/x3')
        print (z.get_records(''))
        print (z.get_records('', 'aaaa'))

