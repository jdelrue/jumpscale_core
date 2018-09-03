import unittest
from .testcases_base import TestcasesBase
from nose_parameterized import parameterized


class TestJDataTypes(TestcasesBase):

    def test001_test_uuid4(self):
        """ JS-001

        **Test Scenario:**
        create 100 random uuids.  test them
        """
        y = self.j.data.types.guid
        for i in range(100):
            u = self.j.data.idgenerator.generateGUID()
            self.assertTrue(y.check(u))

        # https://gist.github.com/ShawnMilo/7777304)
        self.assertFalse(y.check('89eb35868a8247a4c911758a62601cf7'))
        self.assertTrue (y.check('89eb35868a8247a4a911758a62601cf7'))

    def test002_test_ipv4(self):
        """ JS-002

        **Test Scenario:**
        check IPv4 addresses
        """
        y = self.j.data.types.ipaddr
        self.assertFalse(y.is_valid_ipv4('1.1.1.1000'))
        self.assertFalse(y.is_valid_ipv4('1.1.1.1.1'))
        self.assertFalse(y.is_valid_ipv4('fred'))
        self.assertTrue (y.is_valid_ipv4('255.255.255.255'))

    @unittest.skip(
        "https://github.com/threefoldtech/jumpscale_core/issues/90")
    def test002_test_ipv6(self):
        """ JS-003

        Issue reported *actually in python*: https://bugs.python.org/issue34453
        **Test Scenario:**
        check IPv6 addresses.  these look fun!
        https://github.com/gws/ipv6-address-test/blob/master/Tests/Ipv6TestCase.php
        """
        y = self.j.data.types.ipaddr

        ipv6_tests = [ \
            ('', False),
            ('2001:0000:1234:0000:0000:C1C0:ABCD:0876', True),
            ('3ffe:0b00:0000:0000:0001:0000:0000:000a', True),
            ('FF02:0000:0000:0000:0000:0000:0000:0001', True),
            ('0000:0000:0000:0000:0000:0000:0000:0001', True),
            ('0000:0000:0000:0000:0000:0000:0000:0000', True),
            ('::ffff:192.168.1.26', True),
            # extra 0 not allowed!
            ('02001:0000:1234:0000:0000:C1C0:ABCD:0876', False),
            # extra 0 not allowed!
            ('2001:0000:1234:0000:00001:C1C0:ABCD:0876', False),
            # leading space
            (' 2001:0000:1234:0000:0000:C1C0:ABCD:0876', False),
            # trailing space
            ('2001:0000:1234:0000:0000:C1C0:ABCD:0876 ', False),
            # leading and trailing space
            (' 2001:0000:1234:0000:0000:C1C0:ABCD:0876  ', False),
            # junk after valid address
            (' 2001:0000:1234:0000:0000:C1C0:ABCD:0876  0', False),
            # internal space
            ('2001:0000:1234: 0000:0000:C1C0:ABCD:0876', False),
            # garbage instead of '.' in IPv4
            ('2001:1:1:1:1:1:255Z255X255Y255', False),
            ('::ffff:192x168.1.26', False),

            # seven segments
            ('3ffe:0b00:0000:0001:0000:0000:000a', False),
            # nine segments
            ('FF02:0000:0000:0000:0000:0000:0000:0000:0001', False),
            # double '::'
            ('3ffe:b00::1::a', False),
            # double '::'
            ('::1111:2222:3333:4444:5555:6666::', False),
            ('2::10', True),
            ('ff02::1', True),
            ('fe80::', True),
            ('2002::', True),
            ('2001:db8::', True),
            ('2001:0db8:1234::', True),
            ('::ffff:0:0', True),
            ('::1', True),
            ('::ffff:192.168.1.1', True),
            ('1:2:3:4:5:6:7:8', True),
            ('1:2:3:4:5:6::8', True),
            ('1:2:3:4:5::8', True),
            ('1:2:3:4::8', True),
            ('1:2:3::8', True),
            ('1:2::8', True),
            ('1::8', True),
            ('1::2:3:4:5:6:7', True),
            ('1::2:3:4:5:6', True),
            ('1::2:3:4:5', True),
            ('1::2:3:4', True),
            ('1::2:3', True),
            ('1::8', True),
            ('::2:3:4:5:6:7:8', True),
            ('::2:3:4:5:6:7', True),
            ('::2:3:4:5:6', True),
            ('::2:3:4:5', True),
            ('::2:3:4', True),
            ('::2:3', True),
            ('::8', True),
            ('1:2:3:4:5:6::', True),
            ('1:2:3:4:5::', True),
            ('1:2:3:4::', True),
            ('1:2:3::', True),
            ('1:2::', True),
            ('1::', True),
            ('1:2:3:4:5::7:8', True),
            # Double '::'
            ('1:2:3::4:5::7:8', False),
            ('12345::6:7:8', False),
            ('1:2:3:4::7:8', True),
            ('1:2:3::7:8', True),
            ('1:2::7:8', True),
            ('1::7:8', True),
            ('1:2:3:4:5:6:1.2.3.4', True),
            ('1:2:3:4:5::1.2.3.4', True),
            ('1:2:3:4::1.2.3.4', True),
            ('1:2:3::1.2.3.4', True),
            ('1:2::1.2.3.4', True),
            ('1::1.2.3.4', True),
            ('1:2:3:4::5:1.2.3.4', True),
            ('1:2:3::5:1.2.3.4', True),
            ('1:2::5:1.2.3.4', True),
            ('1::5:1.2.3.4', True),
            ('1::5:11.22.33.44', True),
            ('1::5:400.2.3.4', False),
            ('1::5:260.2.3.4', False),
            ('1::5:256.2.3.4', False),
            ('1::5:1.256.3.4', False),
            ('1::5:1.2.256.4', False),
            ('1::5:1.2.3.256', False),
            ('1::5:300.2.3.4', False),
            ('1::5:1.300.3.4', False),
            ('1::5:1.2.300.4', False),
            ('1::5:1.2.3.300', False),
            ('1::5:900.2.3.4', False),
            ('1::5:1.900.3.4', False),
            ('1::5:1.2.900.4', False),
            ('1::5:1.2.3.900', False),
            ('1::5:300.300.300.300', False),
            ('1::5:3000.30.30.30', False),
            ('1::400.2.3.4', False),
            ('1::260.2.3.4', False),
            ('1::256.2.3.4', False),
            ('1::1.256.3.4', False),
            ('1::1.2.256.4', False),
            ('1::1.2.3.256', False),
            ('1::300.2.3.4', False),
            ('1::1.300.3.4', False),
            ('1::1.2.300.4', False),
            ('1::1.2.3.300', False),
            ('1::900.2.3.4', False),
            ('1::1.900.3.4', False),
            ('1::1.2.900.4', False),
            ('1::1.2.3.900', False),
            ('1::300.300.300.300', False),
            ('1::3000.30.30.30', False),
            ('::400.2.3.4', False),
            ('::260.2.3.4', False),
            ('::256.2.3.4', False),
            ('::1.256.3.4', False),
            ('::1.2.256.4', False),
            ('::1.2.3.256', False),
            ('::300.2.3.4', False),
            ('::1.300.3.4', False),
            ('::1.2.300.4', False),
            ('::1.2.3.300', False),
            ('::900.2.3.4', False),
            ('::1.900.3.4', False),
            ('::1.2.900.4', False),
            ('::1.2.3.900', False),
            ('::300.300.300.300', False),
            ('::3000.30.30.30', False),
            ('fe80::217:f2ff:254.7.237.98', True),
            ('fe80::217:f2ff:fe07:ed62', True),
            # unicast, full
            ('2001:DB8:0:0:8:800:200C:417A', True),
            # multicast, full
            ('FF01:0:0:0:0:0:0:101', True),
            # loopback, full
            ('0:0:0:0:0:0:0:1', True),
            # unspecified, full
            ('0:0:0:0:0:0:0:0', True),
            # unicast, compressed
            ('2001:DB8::8:800:200C:417A', True),
            # multicast, compressed
            ('FF01::101', True),
            # loopback, compressed, non-routable
            ('::1', True),
            # unspecified, compressed, non-routable
            ('::', True),
            # IPv4-compatible IPv6 address, full, deprecated
            ('0:0:0:0:0:0:13.1.68.3', True),
            # IPv4-mapped IPv6 address, full
            ('0:0:0:0:0:FFFF:129.144.52.38', True),
            # IPv4-compatible IPv6 address, compressed, deprecated
            ('::13.1.68.3', True),
            # IPv4-mapped IPv6 address, compressed
            ('::FFFF:129.144.52.38', True),
            # unicast, full
            ('2001:DB8:0:0:8:800:200C:417A:221', False),
            # multicast, compressed
            ('FF01::101::2', False),
            # nothing
            ('', False),

            ('fe80:0000:0000:0000:0204:61ff:fe9d:f156', True),
            ('fe80:0:0:0:204:61ff:fe9d:f156', True),
            ('fe80::204:61ff:fe9d:f156', True),

            # Not sure about this one; apparently some systems treat the
            # leading '0' in '.086' as the start of an octal number
            ('fe80:0000:0000:0000:0204:61ff:254.157.241.086', False),
            ('fe80:0:0:0:204:61ff:254.157.241.86', True),
            ('fe80::204:61ff:254.157.241.86', True),
            ('::1', True),
            ('fe80::', True),
            ('fe80::1', True),
            (':', False),

            # Aeron supplied these test cases.
            ('1111:2222:3333:4444::5555:', False),
            ('1111:2222:3333::5555:', False),
            ('1111:2222::5555:', False),
            ('1111::5555:', False),
            ('::5555:', False),
            (':::', False),
            ('1111:', False),
            (':', False),

            (':1111:2222:3333:4444::5555', False),
            (':1111:2222:3333::5555', False),
            (':1111:2222::5555', False),
            (':1111::5555', False),
            (':::5555', False),
            (':::', False),

            ('1.2.3.4:1111:2222:3333:4444::5555', False),
            ('1.2.3.4:1111:2222:3333::5555', False),
            ('1.2.3.4:1111:2222::5555', False),
            ('1.2.3.4:1111::5555', False),
            ('1.2.3.4::5555', False),
            ('1.2.3.4::', False),

            # Additional test cases

            # from http:
            #rt.cpan.org/Public/Bug/Display.html?id=50693
            ('2001:0db8:85a3:0000:0000:8a2e:0370:7334', True),
            ('2001:db8:85a3:0:0:8a2e:370:7334', True),
            ('2001:db8:85a3::8a2e:370:7334', True),
            ('2001:0db8:0000:0000:0000:0000:1428:57ab', True),
            ('2001:0db8:0000:0000:0000::1428:57ab', True),
            ('2001:0db8:0:0:0:0:1428:57ab', True),
            ('2001:0db8:0:0::1428:57ab', True),
            ('2001:0db8::1428:57ab', True),
            ('2001:db8::1428:57ab', True),
            ('0000:0000:0000:0000:0000:0000:0000:0001', True),
            ('::1', True),
            ('::ffff:12.34.56.78', True),
            ('::ffff:0c22:384e', True),
            ('2001:0db8:1234:0000:0000:0000:0000:0000', True),
            ('2001:0db8:1234:ffff:ffff:ffff:ffff:ffff', True),
            ('2001:db8:a::123', True),
            ('fe80::', True),
            ('::ffff:192.0.2.128', True),
            ('::ffff:c000:280', True),

            ('123', False),
            ('ldkfj', False),
            ('2001::FFD3::57ab', False),
            ('2001:db8:85a3::8a2e:37023:7334', False),
            ('2001:db8:85a3::8a2e:370k:7334', False),
            ('1:2:3:4:5:6:7:8:9', False),
            ('1::2::3', False),
            ('1:::3:4:5', False),
            ('1:2:3::4:5:6:7:8:9', False),
            ('::ffff:2.3.4', False),
            ('::ffff:257.1.2.3', False),
            ('1.2.3.4', False),

            # New from Aeron
            ('1111:2222:3333:4444:5555:6666:7777:8888', True),
            ('1111:2222:3333:4444:5555:6666:7777::', True),
            ('1111:2222:3333:4444:5555:6666::', True),
            ('1111:2222:3333:4444:5555::', True),
            ('1111:2222:3333:4444::', True),
            ('1111:2222:3333::', True),
            ('1111:2222::', True),
            ('1111::', True),
            ('::', True),
            ('1111:2222:3333:4444:5555:6666::8888', True),
            ('1111:2222:3333:4444:5555::8888', True),
            ('1111:2222:3333:4444::8888', True),
            ('1111:2222:3333::8888', True),
            ('1111:2222::8888', True),
            ('1111::8888', True),
            ('::8888', True),
            ('1111:2222:3333:4444:5555::7777:8888', True),
            ('1111:2222:3333:4444::7777:8888', True),
            ('1111:2222:3333::7777:8888', True),
            ('1111:2222::7777:8888', True),
            ('1111::7777:8888', True),
            ('::7777:8888', True),
            ('1111:2222:3333:4444::6666:7777:8888', True),
            ('1111:2222:3333::6666:7777:8888', True),
            ('1111:2222::6666:7777:8888', True),
            ('1111::6666:7777:8888', True),
            ('::6666:7777:8888', True),
            ('1111:2222:3333::5555:6666:7777:8888', True),
            ('1111:2222::5555:6666:7777:8888', True),
            ('1111::5555:6666:7777:8888', True),
            ('::5555:6666:7777:8888', True),
            ('1111:2222::4444:5555:6666:7777:8888', True),
            ('1111::4444:5555:6666:7777:8888', True),
            ('::4444:5555:6666:7777:8888', True),
            ('1111::3333:4444:5555:6666:7777:8888', True),
            ('::3333:4444:5555:6666:7777:8888', True),
            ('::2222:3333:4444:5555:6666:7777:8888', True),
            ('1111:2222:3333:4444:5555:6666:123.123.123.123', True),
            ('1111:2222:3333:4444:5555::123.123.123.123', True),
            ('1111:2222:3333:4444::123.123.123.123', True),
            ('1111:2222:3333::123.123.123.123', True),
            ('1111:2222::123.123.123.123', True),
            ('1111::123.123.123.123', True),
            ('::123.123.123.123', True),
            ('1111:2222:3333:4444::6666:123.123.123.123', True),
            ('1111:2222:3333::6666:123.123.123.123', True),
            ('1111:2222::6666:123.123.123.123', True),
            ('1111::6666:123.123.123.123', True),
            ('::6666:123.123.123.123', True),
            ('1111:2222:3333::5555:6666:123.123.123.123', True),
            ('1111:2222::5555:6666:123.123.123.123', True),
            ('1111::5555:6666:123.123.123.123', True),
            ('::5555:6666:123.123.123.123', True),
            ('1111:2222::4444:5555:6666:123.123.123.123', True),
            ('1111::4444:5555:6666:123.123.123.123', True),
            ('::4444:5555:6666:123.123.123.123', True),
            ('1111::3333:4444:5555:6666:123.123.123.123', True),
            ('::2222:3333:4444:5555:6666:123.123.123.123', True),

            # New invalid from Aeron
            # Invalid data
            ('XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX', False),

            # Too many components
            ('1111:2222:3333:4444:5555:6666:7777:8888:9999', False),
            ('1111:2222:3333:4444:5555:6666:7777:8888::', False),
            ('::2222:3333:4444:5555:6666:7777:8888:9999', False),

            # Too few components
            ('1111:2222:3333:4444:5555:6666:7777', False),
            ('1111:2222:3333:4444:5555:6666', False),
            ('1111:2222:3333:4444:5555', False),
            ('1111:2222:3333:4444', False),
            ('1111:2222:3333', False),
            ('1111:2222', False),
            ('1111', False),

            # Missing :
            ('11112222:3333:4444:5555:6666:7777:8888', False),
            ('1111:22223333:4444:5555:6666:7777:8888', False),
            ('1111:2222:33334444:5555:6666:7777:8888', False),
            ('1111:2222:3333:44445555:6666:7777:8888', False),
            ('1111:2222:3333:4444:55556666:7777:8888', False),
            ('1111:2222:3333:4444:5555:66667777:8888', False),
            ('1111:2222:3333:4444:5555:6666:77778888', False),

            # Missing : intended for ::
            ('1111:2222:3333:4444:5555:6666:7777:8888:', False),
            ('1111:2222:3333:4444:5555:6666:7777:', False),
            ('1111:2222:3333:4444:5555:6666:', False),
            ('1111:2222:3333:4444:5555:', False),
            ('1111:2222:3333:4444:', False),
            ('1111:2222:3333:', False),
            ('1111:2222:', False),
            ('1111:', False),
            (':', False),
            (':8888', False),
            (':7777:8888', False),
            (':6666:7777:8888', False),
            (':5555:6666:7777:8888', False),
            (':4444:5555:6666:7777:8888', False),
            (':3333:4444:5555:6666:7777:8888', False),
            (':2222:3333:4444:5555:6666:7777:8888', False),
            (':1111:2222:3333:4444:5555:6666:7777:8888', False),

            # :::
            (':::2222:3333:4444:5555:6666:7777:8888', False),
            ('1111:::3333:4444:5555:6666:7777:8888', False),
            ('1111:2222:::4444:5555:6666:7777:8888', False),
            ('1111:2222:3333:::5555:6666:7777:8888', False),
            ('1111:2222:3333:4444:::6666:7777:8888', False),
            ('1111:2222:3333:4444:5555:::7777:8888', False),
            ('1111:2222:3333:4444:5555:6666:::8888', False),
            ('1111:2222:3333:4444:5555:6666:7777:::', False),

            # Double ::'),
            ('::2222::4444:5555:6666:7777:8888', False),
            ('::2222:3333::5555:6666:7777:8888', False),
            ('::2222:3333:4444::6666:7777:8888', False),
            ('::2222:3333:4444:5555::7777:8888', False),
            ('::2222:3333:4444:5555:7777::8888', False),
            ('::2222:3333:4444:5555:7777:8888::', False),

            ('1111::3333::5555:6666:7777:8888', False),
            ('1111::3333:4444::6666:7777:8888', False),
            ('1111::3333:4444:5555::7777:8888', False),
            ('1111::3333:4444:5555:6666::8888', False),
            ('1111::3333:4444:5555:6666:7777::', False),

            ('1111:2222::4444::6666:7777:8888', False),
            ('1111:2222::4444:5555::7777:8888', False),
            ('1111:2222::4444:5555:6666::8888', False),
            ('1111:2222::4444:5555:6666:7777::', False),

            ('1111:2222:3333::5555::7777:8888', False),
            ('1111:2222:3333::5555:6666::8888', False),
            ('1111:2222:3333::5555:6666:7777::', False),

            ('1111:2222:3333:4444::6666::8888', False),
            ('1111:2222:3333:4444::6666:7777::', False),

            ('1111:2222:3333:4444:5555::7777::', False),

            # Too many components'
            ('1111:2222:3333:4444:5555:6666:7777:8888:1.2.3.4', False),
            ('1111:2222:3333:4444:5555:6666:7777:1.2.3.4', False),
            ('1111:2222:3333:4444:5555:6666::1.2.3.4', False),
            ('::2222:3333:4444:5555:6666:7777:1.2.3.4', False),
            ('1111:2222:3333:4444:5555:6666:1.2.3.4.5', False),

            # Too few components
            ('1111:2222:3333:4444:5555:1.2.3.4', False),
            ('1111:2222:3333:4444:1.2.3.4', False),
            ('1111:2222:3333:1.2.3.4', False),
            ('1111:2222:1.2.3.4', False),
            ('1111:1.2.3.4', False),
            ('1.2.3.4', False),

            # Missing :
            ('11112222:3333:4444:5555:6666:1.2.3.4', False),
            ('1111:22223333:4444:5555:6666:1.2.3.4', False),
            ('1111:2222:33334444:5555:6666:1.2.3.4', False),
            ('1111:2222:3333:44445555:6666:1.2.3.4', False),
            ('1111:2222:3333:4444:55556666:1.2.3.4', False),
            ('1111:2222:3333:4444:5555:66661.2.3.4', False),

            # Missing .
            ('1111:2222:3333:4444:5555:6666:255255.255.255', False),
            ('1111:2222:3333:4444:5555:6666:255.255255.255', False),
            ('1111:2222:3333:4444:5555:6666:255.255.255255', False),

            # Missing : intended for ::
            (':1.2.3.4', False),
            (':6666:1.2.3.4', False),
            (':5555:6666:1.2.3.4', False),
            (':4444:5555:6666:1.2.3.4', False),
            (':3333:4444:5555:6666:1.2.3.4', False),
            (':2222:3333:4444:5555:6666:1.2.3.4', False),
            (':1111:2222:3333:4444:5555:6666:1.2.3.4', False),

            # :::
            (':::2222:3333:4444:5555:6666:1.2.3.4', False),
            ('1111:::3333:4444:5555:6666:1.2.3.4', False),
            ('1111:2222:::4444:5555:6666:1.2.3.4', False),
            ('1111:2222:3333:::5555:6666:1.2.3.4', False),
            ('1111:2222:3333:4444:::6666:1.2.3.4', False),
            ('1111:2222:3333:4444:5555:::1.2.3.4', False),

            # Double ::
            ('::2222::4444:5555:6666:1.2.3.4', False),
            ('::2222:3333::5555:6666:1.2.3.4', False),
            ('::2222:3333:4444::6666:1.2.3.4', False),
            ('::2222:3333:4444:5555::1.2.3.4', False),

            ('1111::3333::5555:6666:1.2.3.4', False),
            ('1111::3333:4444::6666:1.2.3.4', False),
            ('1111::3333:4444:5555::1.2.3.4', False),

            ('1111:2222::4444::6666:1.2.3.4', False),
            ('1111:2222::4444:5555::1.2.3.4', False),

            ('1111:2222:3333::5555::1.2.3.4', False),

            # Missing parts
            ('::.', False),
            ('::..', False),
            ('::...', False),
            ('::1...', False),
            ('::1.2..', False),
            ('::1.2.3.', False),
            ('::.2..', False),
            ('::.2.3.', False),
            ('::.2.3.4', False),
            ('::..3.', False),
            ('::..3.4', False),
            ('::...4', False),

            # Extra : in front
            (':1111:2222:3333:4444:5555:6666:7777::', False),
            (':1111:2222:3333:4444:5555:6666::', False),
            (':1111:2222:3333:4444:5555::', False),
            (':1111:2222:3333:4444::', False),
            (':1111:2222:3333::', False),
            (':1111:2222::', False),
            (':1111::', False),
            (':::', False),
            (':1111:2222:3333:4444:5555:6666::8888', False),
            (':1111:2222:3333:4444:5555::8888', False),
            (':1111:2222:3333:4444::8888', False),
            (':1111:2222:3333::8888', False),
            (':1111:2222::8888', False),
            (':1111::8888', False),
            (':::8888', False),
            (':1111:2222:3333:4444:5555::7777:8888', False),
            (':1111:2222:3333:4444::7777:8888', False),
            (':1111:2222:3333::7777:8888', False),
            (':1111:2222::7777:8888', False),
            (':1111::7777:8888', False),
            (':::7777:8888', False),
            (':1111:2222:3333:4444::6666:7777:8888', False),
            (':1111:2222:3333::6666:7777:8888', False),
            (':1111:2222::6666:7777:8888', False),
            (':1111::6666:7777:8888', False),
            (':::6666:7777:8888', False),
            (':1111:2222:3333::5555:6666:7777:8888', False),
            (':1111:2222::5555:6666:7777:8888', False),
            (':1111::5555:6666:7777:8888', False),
            (':::5555:6666:7777:8888', False),
            (':1111:2222::4444:5555:6666:7777:8888', False),
            (':1111::4444:5555:6666:7777:8888', False),
            (':::4444:5555:6666:7777:8888', False),
            (':1111::3333:4444:5555:6666:7777:8888', False),
            (':::3333:4444:5555:6666:7777:8888', False),
            (':::2222:3333:4444:5555:6666:7777:8888', False),
            (':1111:2222:3333:4444:5555:6666:1.2.3.4', False),
            (':1111:2222:3333:4444:5555::1.2.3.4', False),
            (':1111:2222:3333:4444::1.2.3.4', False),
            (':1111:2222:3333::1.2.3.4', False),
            (':1111:2222::1.2.3.4', False),
            (':1111::1.2.3.4', False),
            (':::1.2.3.4', False),
            (':1111:2222:3333:4444::6666:1.2.3.4', False),
            (':1111:2222:3333::6666:1.2.3.4', False),
            (':1111:2222::6666:1.2.3.4', False),
            (':1111::6666:1.2.3.4', False),
            (':::6666:1.2.3.4', False),
            (':1111:2222:3333::5555:6666:1.2.3.4', False),
            (':1111:2222::5555:6666:1.2.3.4', False),
            (':1111::5555:6666:1.2.3.4', False),
            (':::5555:6666:1.2.3.4', False),
            (':1111:2222::4444:5555:6666:1.2.3.4', False),
            (':1111::4444:5555:6666:1.2.3.4', False),
            (':::4444:5555:6666:1.2.3.4', False),
            (':1111::3333:4444:5555:6666:1.2.3.4', False),
            (':::2222:3333:4444:5555:6666:1.2.3.4', False),

            # Extra : at end
            ('1111:2222:3333:4444:5555:6666:7777:::', False),
            ('1111:2222:3333:4444:5555:6666:::', False),
            ('1111:2222:3333:4444:5555:::', False),
            ('1111:2222:3333:4444:::', False),
            ('1111:2222:3333:::', False),
            ('1111:2222:::', False),
            ('1111:::', False),
            (':::', False),
            ('1111:2222:3333:4444:5555:6666::8888:', False),
            ('1111:2222:3333:4444:5555::8888:', False),
            ('1111:2222:3333:4444::8888:', False),
            ('1111:2222:3333::8888:', False),
            ('1111:2222::8888:', False),
            ('1111::8888:', False),
            ('::8888:', False),
            ('1111:2222:3333:4444:5555::7777:8888:', False),
            ('1111:2222:3333:4444::7777:8888:', False),
            ('1111:2222:3333::7777:8888:', False),
            ('1111:2222::7777:8888:', False),
            ('1111::7777:8888:', False),
            ('::7777:8888:', False),
            ('1111:2222:3333:4444::6666:7777:8888:', False),
            ('1111:2222:3333::6666:7777:8888:', False),
            ('1111:2222::6666:7777:8888:', False),
            ('1111::6666:7777:8888:', False),
            ('::6666:7777:8888:', False),
            ('1111:2222:3333::5555:6666:7777:8888:', False),
            ('1111:2222::5555:6666:7777:8888:', False),
            ('1111::5555:6666:7777:8888:', False),
            ('::5555:6666:7777:8888:', False),
            ('1111:2222::4444:5555:6666:7777:8888:', False),
            ('1111::4444:5555:6666:7777:8888:', False),
            ('::4444:5555:6666:7777:8888:', False),
            ('1111::3333:4444:5555:6666:7777:8888:', False),
            ('::3333:4444:5555:6666:7777:8888:', False),
            ('::2222:3333:4444:5555:6666:7777:8888:', False),

            # Invalid data'
            ('XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:1.2.3.4', False),
            ('1111:2222:3333:4444:5555:6666:256.256.256.256', False),

            # These actually fail (!!)  raised as a bug against
            # the *standard* python library: https://bugs.python.org/issue34453
            # turns out it's not the python library, it's an ambiguity
            # in the IPv4 RFC.  so, these are legitimately OK.
            ('1111:2222:3333:4444:5555:6666:00.00.00.00', True),
            ('1111:2222:3333:4444:5555:6666:000.000.000.000', True),
        ]

        for i, (test, expected) in enumerate(ipv6_tests):
            report = "%d %s" % (i, test)
            if expected:
                self.assertTrue(y.is_valid_ipv6(test), report)
            else:
                self.assertFalse(y.is_valid_ipv6(test), report)
