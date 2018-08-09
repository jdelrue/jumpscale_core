import os
import unittest
import random
from .testcases_base import TestcasesBase
from jumpscale import j
from JumpscaleLib.sal.nic.UnixNetworkManager import NetworkingError


class TestNICS(TestcasesBase):

    @unittest.skip(
        "https://github.com/threefoldtech/jumpscale_core/issues/169")
    def test001_get_nic(self):
        """ JS-025

        **Test Scenario:**
        #. Get the nics from j.sal.nic[sal_nic].
        #. Get the nics from ifconfig[ifconfig_nic].
        #. Compare between [sal_nic] and [ifconfig_nic],should be same .

        """
        self.lg.info("Get the nics from j.sal.nic[sal_nic]")
        nics = j.sal.nic.nics

        self.lg.info("Get the nics from ifconfig[ifconfig_nic].")
        nic_orgional = os.popen("ifconfig").read()

        self.lg.info(
            "Compare between [sal_nic] and [ifconfig_nic],should be same ")
        for nic in nics:
            self.assertIn(nic, nic_orgional)

    @unittest.skip(
        "https://github.com/threefoldtech/jumpscale_core/issues/169")
    def test002_get_nic_ip(self):
        """ JS-026

        **Test Scenario:**
        #. Get Ip and mask [nic_ip_mask] of one device from nic.ipGet.
        #. Get Ip and mask[ifconfig_ip_mask] of one device from ifconfig.
        #. Compare between [nic_ip_mask] and [ifconfig_ip_mask],should be same .

        """
        self.lg.info(
            "Get Ip and mask [nic_ip_mask] of one device from nic.ipGet.")
        nics = j.sal.nic.nics
        device = random.choice(nics)
        nic_ip_mask = j.sal.nic.ipGet(device)

        self.lg.info(
            "Get Ip and mask[ifconfig_ip_mask] of one device from ifconfig.")
        device_ip = os.popen(
            "ifconfig %s | grep 'inet ' | awk -F'[: ]+' '{ print $4 }'" %
            device).read().strip()
        device_mask = os.popen(
            "ifconfig %s | grep 'inet ' | awk -F'[: ]+' '{ print $8 }'" %
            device).read().strip()
        ifconfig_ip_mask = (device_ip, device_mask)

        self.lg.info(
            "Compare between [nic_ip_mask] and [ifconfig_ip_mask],should be same .")
        self.assertEqual(nic_ip_mask, ifconfig_ip_mask)

    @unittest.skip(
        "https://github.com/threefoldtech/jumpscale_core/issues/153")
    def test003_set_nic_ip(self):
        """ JS-027

        **Test Scenario:**
        #. Set ip for one device with  nic.ipSet.
        #. Get Ip for this device ,check tha device ip is updated.

        """

        self.lg.info("Set ip for one device with  nic.ipSet.")
        device = random.choice(j.sal.nic.nics)
        device_ip = os.popen(
            "ifconfig %s | grep 'inet ' | awk -F'[: ]+' '{ print $4 }'" %
            device).read().strip()
        new_ip = ".".join(device_ip.split(
            '.')[0:-1]) + '.%s' % random.randint(1, 254)
        j.sal.nic.ipSet(
            device,
            ip=None,
            netmask=None,
            gw=None,
            inet='dhcp',
            commit=False)
        j.sal.nic.commit(device)

        self.lg.info("Get Ip for this device ,check tha device ip is updated")
        self.assertEqual(j.sal.nic.ipGet(device), new_ip)

    def test004_using_nonexist_device(self):
        """ JS-028
        **Test Scenario:**
        #. Get ip for nonexist device ,should fail.
        #. Set ip for nonexist device with nic.ipset,should fail .

        """
        self.lg.info("Get ip for nonexist device ,should fail.")
        device = self.random_string()
        with self.assertRaises(NetworkingError):
            j.sal.nic.ipGet(device)

        self.lg.info("Set ip for nonexist device with nic.ipset,should fail ")
        with self.assertRaises(NetworkingError):
            j.sal.nic.ipSet(device)
