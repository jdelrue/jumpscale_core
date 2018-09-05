import os
import shutil
import random
from .testcases_base import TestcasesBase
from JumpscaleLib.sal.nic.UnixNetworkManager import NetworkingError
import unittest
import string
import uuid
from pwd import getpwuid


class TestUNIX(TestcasesBase):

    def test001_check_application_installed(self):
        """ JS-029

        **Test Scenario:**
        #. Check that nosetests app is installed, should return true.
        #. Check that fake app is installed, should return false.

        """
        self.lg.info(
            " Check that nosetests app is installed, should return true. ")
        app_name = "python3"
        self.assertTrue(self.j.sal.unix.checkApplicationInstalled(app_name))

        self.lg.info(
            " Check that fake app is installed, should return false. ")
        app_name = "fake_name"
        self.assertFalse(self.j.sal.unix.checkApplicationInstalled(app_name))

    def test002_crypt(self):
        """ JS-030

        **Test Scenario:**
        #. Crypt word with 2 characters salt , should return crypted word started with salt characters .
        #. Crypt word with more than  2 characters salt,
                        should return crypted word started with first two chars of salt.

        """
        self.lg.info(
            "Crypt word with 2 characters salt, should return crypted word started with salt characters .")
        salt = str(uuid.uuid4()).replace('-', '')[1:3]
        encrypted_word = self.j.sal.unix.crypt("test", salt)
        self.assertIn(salt, encrypted_word)

        self.lg.info(
            "Crypt word with more than 2 characters salt, Should return crypted word started with first two chars of salt.")
        salt = str(uuid.uuid4()).replace('-', '')[1:10]
        encrypted_word = self.j.sal.unix.crypt("test", salt)
        self.assertNotIn(salt, encrypted_word)
        self.assertIn(salt[0:2], encrypted_word)

    def test003_check_user_exist(self):
        """ JS-031

        **Test Scenario:**
        #. Check that one of system users is exist, should succeed.
        #. Check that fake user isn't exist, should succeed .

        """
        self.lg.info("Check that one of system users is exist, should succeed")
        system_users = os.popen(
            "cat /etc/passwd | cut -d : -f 1").read().splitlines()
        random_user = random.choice(system_users)
        self.assertTrue(self.j.sal.unix.unixUserExists(random_user))

        self.lg.info("Check that fake user isn't exist, should succeed ")
        fake_user = self.random_string()
        self.assertFalse(self.j.sal.unix.unixUserExists(fake_user))

    def test004_check_group_exist(self):
        """ JS-032

        **Test Scenario:**
        #. Check that one of system groups is exist, should succeed.
        #. Check that fake group isn't exist, should succeed.

        """
        self.lg.info(
            "Check that one of system groups is exist, should succeed.")
        system_groups = os.popen(
            "cat /etc/group | cut -d : -f 1").read().splitlines()
        random_group = random.choice(system_groups)
        self.assertTrue(self.j.sal.unix.unixGroupExists(random_group))

        self.lg.info("Check that fake group isn't exist, should succeed")
        fake_group = self.random_string()
        self.assertFalse(self.j.sal.unix.unixGroupExists(fake_group))

    def test05_create_new_group(self):
        """ JS-033

        **Test Scenario:**
        #. Create new group [G1], should succeed.
        #. Check that [G1] exist, should succeed.

        """
        self.lg.info("Create new group [G1] ,should succeed.")
        group_name = self.random_string()
        self.j.sal.unix.addSystemGroup(group_name)

        self.lg.info("Check that [G1] exist, should succeed.")
        self.assertTrue(self.j.sal.unix.unixGroupExists(group_name))
        self.assertIn(group_name, os.popen(
            "cat /etc/group | cut -d : -f 1").read().splitlines())

    def test06_add_user_to_group(self):
        """ JS-034

        **Test Scenario:**

        #. Create new user [U1], should succeed.
        #. Add [U1] to one of existing groups [G1], should succeed.
        #. Check that [U1] exist on [G1], should succeed.
        #. Add fake_user to one of existing groups [G1], should fail.
        #. Add [U1] to fake_group, should fail.

        """
        self.lg.info("Create new user [U1],should succeed .")
        user_name = self.random_string()
        self.j.sal.unix.addSystemUser(user_name)

        self.lg.info(
            "Add [U1] to one of existing groups [G1], should succeed.")
        system_groups = os.popen(
            "cat /etc/group | cut -d : -f 1").read().splitlines()
        random_group = random.choice(system_groups)
        self.j.sal.unix.addUserToGroup(user_name, random_group)

        self.lg.info("Check that [U1] exist on [G1], should succeed.")
        self.assertTrue(self.j.sal.unix.unixUserIsInGroup(user_name, random_group))

        self.lg.info(
            "Add fake_user to one of existing groups [G1], should fail.")
        fake_user_name = self.random_string()
        with self.assertRaises(AssertionError):
            self.j.sal.unix.addUserToGroup(fake_user_name, random_group)

        self.lg.info("Add [U1] to fake_group, should fail .")
        fake_group_name = self.random_string()
        with self.assertRaises(AssertionError):
            self.j.sal.unix.addUserToGroup(user_name, fake_group_name)

    def test07_change_file_owner(self):
        """ JS-035

        **Test Scenario:**
        #. Create new file [f1].
        #. Create  new user [U1], should succeed.
        #. Change the owner of [f1] to [U1], should succeed.
        #. Check that the owner of [f1] updated to [U1], should succeed.
        #. Change the [f1] owner to non-exist user, should fail.
        #. Change the owner of non-exist file to [U1], should fail.
        #. Change the owner of [f1] to [U1] with non-exist group, should fail.

        """
        self.lg.info(" Create new file[f1].")
        file_path = "/{}".format(self.random_string())
        os.popen("touch {}".format(file_path))

        self.lg.info("Create  new user [U1], should succeed.")
        user_name = self.random_string()
        self.j.sal.unix.addSystemUser(user_name)

        self.lg.info(" Change the owner of [f1] to [U1], should succeed.")
        system_groups = os.popen(
            "cat /etc/group | cut -d : -f 1").read().splitlines()
        random_group = random.choice(system_groups)
        self.j.sal.unix.chown(file_path, user_name, random_group)

        self.lg.info(
            "Check that the owner of [f1] updated to [U1], should succeed")
        self.assertEqual(
            getpwuid(
                os.stat(file_path).st_uid).pw_name,
            user_name)

        self.lg.info("Change the [f1] owner to non-exist user, should fail")
        fake_user_name = self.random_string()
        with self.assertRaises(KeyError):
            self.j.sal.unix.chown(file_path, fake_user_name, random_group)

        self.lg.info(
            " Change the owner of non-exist file to [U1], should fail.")
        fake_file_path = "/{}".format(self.random_string())
        with self.assertRaises(FileNotFoundError):
            self.j.sal.unix.chown(fake_file_path, user_name, random_group)

        self.lg.info(
            " Change the owner of  [f1] to [U1] with non-exist group, should fail")
        fake_group_name = self.random_string()
        with self.assertRaises(KeyError):
            self.j.sal.unix.chown(file_path, user_name, fake_group_name)

    @unittest.skip(
        "https://github.com/threefoldtech/jumpscale_core/issues/163")
    def test08_change_folder_owner_recursively(self):
        """ JS-036

        **Test Scenario:**
        #. Create new directory[D1] and create new file [F1] on it .
        #. Create  new user [U1], should succeed.
        #. Change the owner of [D1] to [U1], should succeed.
        #. Check that the owner of [D1] is updated to [U1], and [F1] owner isn't updated.
        #. Change the [D1] owner to [U1] recursively, should succeed.
        #. Check that the owner of [D1] is updated to [U1], and [F1] owner too.
        """
        self.lg.info(
            "Create new directory[D1] and create new file [F1]on it .")
        dir_path = "/{}".format(self.random_string())
        file_path = "{}/{}".format(dir_path, self.random_string())
        os.popen("touch {}".format(file_path))

        self.lg.info("Create  new user [U1], should succeed.")
        user_name = self.random_string()
        self.j.sal.unix.addSystemUser(user_name)

        self.lg.info("Change the owner of [D1] to [U1], should succeed.")
        system_groups = os.popen(
            "cat /etc/group | cut -d : -f 1").read().splitlines()
        random_group = random.choice(system_groups)
        self.j.sal.unix.chown(dir_path, user_name, random_group)

        self.lg.info(
            "Check that the owner of [D1] is updated to [U1], and [F1] owner isn't updated.")
        self.assertNotEqual(
            getpwuid(
                os.stat(file_path).st_uid).pw_name,
            user_name)
        self.assertEqual(getpwuid(os.stat(dir_path).st_uid).pw_name, user_name)

        self.lg.info(
            "Change the [D1] owner to [U1] recursively, should succeed.")
        self.j.sal.unix.chown(dir_path, user_name, random_group, recursive=True)

        self.lg.info(
            "Check that the owner of [D1] is updated to [U1], and [F1] owner too .")
        self.assertEqual(
            getpwuid(
                os.stat(file_path).st_uid).pw_name,
            user_name)
        self.assertEqual(getpwuid(os.stat(dir_path).st_uid).pw_name, user_name)
