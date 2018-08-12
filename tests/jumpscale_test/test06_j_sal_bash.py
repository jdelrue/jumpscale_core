from jumpscale import j
import os
import random
import unittest
from .testcases_base import TestcasesBase, squash_dictionaries


class TestBASH(TestcasesBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bash = j.tools.bash.get()

    def test001_env(self):
        """ JS-038

        **Test Scenario:**
        #. Get all environment variables using bash.env.
        #. Check that all environment variables exsits.
        """

        v1, v2 = squash_dictionaries(self.bash.env, os.environ._data)
        self.assertEqual(v1, v2)

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/175')
    def test002_get_env(self):
        """ JS-039

        **Test Scenario:**
        #. Get specific environment variable and validate its value, should succeed.
        #. Get non-existing environment variable, should fail.
        """
        self.lg.info(
            'Get specific environment variable and validate its value, should succeed')
        env_var = random.choice(list(self.bash.env.keys()))
        self.assertEqual(self.bash.envGet(env_var), os.getenv(env_var))

        self.lg.info('Get non-existing environment variable, should fail')
        with self.assertRaises(KeyError):
            self.bash.envGet(self.random_string())

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/175')
    def test003_set_env(self):
        """ JS-040

        **Test Scenario:**
        #. Set new environment variable.
        #. Check that the new environment variable is added, should succeed.
        #. Update existing environment variable's value, should succeed.
        """
        self.lg.info('Set new environment variable')
        key = self.random_string()
        value = self.random_string()
        self.bash.envSet(key, value)

        self.lg.info(
            'Check that the new environment variable is added, should succeed')
        self.assertEqual(self.bash.envGet(key), value)
        self.assertEqual(self.bash.env[key], value)

        self.lg.info(
            'Update existing environment variable\'s value, should succeed')
        new_value = self.random_string()
        self.bash.envSet(key, new_value)
        self.assertEqual(self.bash.envGet(key), value)
        self.assertEqual(self.bash.env[key], value)

    def test004_delete_env(self):
        """ JS-041

        **Test Scenario:**
        #. Set new environment variable.
        #. Delete environment variable, should succeed.
        #. Delete non-existing environment variable, shoild fail.
        """
        self.lg.info('Set new environment variable')
        key = self.random_string()
        value = self.random_string()
        self.bash.envSet(key, value)

        self.lg.info('Delete environment variable, should succeed')
        self.bash.envDelete(key)

        with self.assertRaises(KeyError):
            self.bash.env[key]

        with self.assertRaises(KeyError):
            self.bash.envGet(key)


class TestPROFILEJS(TestcasesBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        bash = j.tools.bash.get()
        cls.profileJS = bash.profileJS

    def test01_env_set(self):
        """ JS-044

        **Test Scenario:**
        #. Set new environment variables.
        #. Check that the environment variable in profilejs, should succeed.
        #. Get the environment variable, should succeed.
        """
        self.lg.info('Set new environment variables')
        key = self.random_string()
        value = self.random_string()
        self.profileJS.envSet(key, value)

        self.lg.info(
            'Check that the environment variable in profilejs, should succeed')
        self.assertEqual(self.profileJS.envGet(key), value)
        self.assertIn(
            '{0}="{1}"\nexport {0}'.format(
                key, value), str(
                self.profileJS))

        self.lg.info('Get the environment variable, should succeed')
        self.assertEqual(self.profileJS.env[key], value)
        self.assertEqual(self.profileJS.envGet(key), value)

    def test02_env_get(self):
        """ JS-045

        **Test Scenario:**
        #. Choose random environment variable.
        #. Get the environment variable, should succeed.
        """
        env_vars = self.profileJS.env
        random_key = random.choice(list(env_vars.keys()))
        self.assertEqual(
            self.profileJS.envGet(random_key),
            self.profileJS.env[random_key])

    def test03_env_exists(self):
        """ JS-046

        **Test Scenario:**
        #. Choose random environment variable.
        #. Check if the environment variable exists, should return true.
        #. Check if false environment variable exists, should return false.
        """
        self.lg.info('Choose random environment variable')
        env_vars = self.profileJS.env
        random_key = random.choice(list(env_vars.keys()))

        self.lg.info(
            ' Check if the environment variable exists, should return true')
        self.assertTrue(self.profileJS.envExists(random_key))

        self.lg.info(
            'Check if false environment variable exists, should return false')
        self.assertFalse(self.profileJS.envExists(self.random_string()))

    def test04_env_delete(self):
        """ JS-047

        **Test Scenario:**
        #. Set new environment variable.
        #. Delete environment variable, should succeed.
        #. Delete non-existing environment variable, shoild fail.
        """
        self.lg.info('Set new environment variables')
        key = self.random_string()
        value = self.random_string()
        self.profileJS.envSet(key, value)

        self.lg.info('Delete environment variable, should succeed')
        self.profileJS.envDelete(key)

        self.lg.info(
            'Check that the environment variable is removed from profilejs, should succeed')
        self.assertNotIn(
            '{0}="{1}"\nexport {0}'.format(
                key, value), str(
                self.profileJS))

        with self.assertRaises(KeyError):
            self.profileJS.envGet(key)

        self.lg.info('Delete non-existing environment variable, shoild fail')
        with self.assertRaises(KeyError):
            self.profileJS.envDelete(self.random_string())

    def test05_add_path(self):
        """ JS-048

        **Test Scenario:**
        #. Add new path, should succeed.
        #. Check that the new path is added to paths list, should succeed.
        """
        self.lg.info('Add new path')
        path = self.random_string()
        self.profileJS.addPath(path)

        self.lg.info(
            'Check that the new path is added to paths list, should succeed')
        self.assertIn(path, self.profileJS.paths)

    def test06_delete_path(self):
        """ JS-049

        **Test Scenario:**
        #. Add new path, should succeed.
        #. Delete the new path, should succeed.
        """
        self.lg.info('Add new path, should succeed')
        path = self.random_string()
        self.profileJS.addPath(path)

        self.lg.info('Delete the new path, should succeed')
        self.profileJS.pathDelete(path)
        self.assertNotIn(path, self.profileJS.paths)


class TestPROFILEDEFAULT(TestcasesBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        bash = j.tools.bash.get()
        cls.profileDefault = bash.profileDefault

    def test01_env_set(self):
        """ JS-050

        **Test Scenario:**
        #. Set new environment variables.
        #. Check that the environment variable in profileDefault, should succeed.
        #. Get the environment variable, should succeed.
        """
        self.lg.info('Set new environment variables')
        key = self.random_string()
        value = self.random_string()
        self.profileDefault.envSet(key, value)

        self.lg.info(
            'Check that the environment variable in profileDefault, should succeed')
        self.assertEqual(self.profileDefault.envGet(key), value)
        self.assertIn(
            '{0}="{1}"\nexport {0}'.format(
                key, value), str(
                self.profileDefault))

        self.lg.info('Get the environment variable, should succeed')
        self.assertEqual(self.profileDefault.env[key], value)
        self.assertEqual(self.profileDefault.envGet(key), value)

    def test02_env_get(self):
        """ JS-051

        **Test Scenario:**
        #. Choose random environment variable.
        #. Get the environment variable, should succeed.
        """
        env_vars = self.profileDefault.env
        random_key = random.choice(list(env_vars.keys()))
        self.assertEqual(
            self.profileDefault.envGet(random_key),
            self.profileDefault.env[random_key])

    def test03_env_exists(self):
        """ JS-052

        **Test Scenario:**
        #. Choose random environment variable.
        #. Check if the environment variable exists, should return true.
        #. Check if false environment variable exists, should return false.
        """
        self.lg.info('Choose random environment variable')
        env_vars = self.profileDefault.env
        random_key = random.choice(list(env_vars.keys()))

        self.lg.info(
            ' Check if the environment variable exists, should return true')
        self.assertTrue(self.profileDefault.envExists(random_key))

        self.lg.info(
            'Check if false environment variable exists, should return false')
        self.assertFalse(self.profileDefault.envExists(self.random_string()))

    def test04_env_delete(self):
        """ JS-053

        **Test Scenario:**
        #. Set new environment variable.
        #. Delete environment variable, should succeed.
        #. Delete non-existing environment variable, shoild fail.
        """
        self.lg.info('Set new environment variables')
        key = self.random_string()
        value = self.random_string()
        self.profileDefault.envSet(key, value)

        self.lg.info('Delete environment variable, should succeed')
        self.profileDefault.envDelete(key)

        self.lg.info(
            'Check that the environment variable is removed from profileDefault, should succeed')
        self.assertNotIn(
            '{0}="{1}"\nexport {0}'.format(
                key, value), str(
                self.profileDefault))

        with self.assertRaises(KeyError):
            self.profileDefault.envGet(key)

        self.lg.info('Delete non-existing environment variable, shoild fail')
        with self.assertRaises(KeyError):
            self.profileDefault.envDelete(self.random_string())

    def test05_env_delete_all(self):
        """ JS-054

        **Test Scenario:**
        #. Set two new environment variable with the same name.
        #. Delete all environment variable, should succeed.
        #. Delete all non-existing environment variable, shoild fail.
        """
        pass

    def test06_add_path(self):
        """ JS-055

        **Test Scenario:**
        #. Add new path, should succeed.
        #. Check that the new path is added to paths list, should succeed.
        """
        self.lg.info('Add new path')
        path = self.random_string()
        self.profileDefault.addPath(path)

        self.lg.info(
            'Check that the new path is added to paths list, should succeed')
        self.assertIn(path, self.profileDefault.paths)

    def test07_delete_path(self):
        """ JS-056

        **Test Scenario:**
        #. Add new path, should succeed.
        #. Delete the new path, should succeed.
        """
        self.lg.info('Add new path, should succeed')
        path = self.random_string()
        self.profileDefault.addPath(path)

        self.lg.info('Delete the new path, should succeed')
        self.profileDefault.pathDelete(path)
        self.assertNotIn(path, self.profileDefault.paths)
