from .testcases_base import TestcasesBase
import os
import random
import pytoml
import unittest
import uuid
from jumpscale import j


class TestJCONFIG(TestcasesBase):

    @classmethod
    def get_config(cls):
        with open(cls.config_path, 'r') as f:
            content = pytoml.loads(f.read().strip())
        return content

    @classmethod
    def reset_config(cls):
        with open(cls.config_path, 'w') as f:
            f.write(pytoml.dumps(cls.config_file_content).strip())

    @classmethod
    def update_config(cls, data):
        content = dict(cls.config_file_content)
        content.update(data)
        with open(cls.config_path, 'w') as f:
            f.write(pytoml.dumps(content).strip())
        return content

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = j.core.state
        cls.config_path = cls.client.configJSPath
        cls.config_file_content = cls.get_config()

    def setUp(self):
        super().setUp()
        self.lg.info('Add test configration (setUp)')
        test_config = {
            'key_1': 'value_1',
            'key_2': 'value_2',
            'dict_1': {
                'd_key_1': 'd_value_1',
                'd_key_2': True,
                'd_key_3': False
            }
        }
        self.client._configJS = self.update_config(test_config)

    def tearDown(self):
        self.lg.info('Remove test configration (tearDown)')
        self.reset_config()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        cls.reset_config()
        super().tearDownClass()

    def test001_config_get(self):
        """ JS-016
        **Test Scenario:**
        #. Get value of an existing key.
        #. Get the value of a non-existing key.
        #. Get the value of a non-existing key with default value and set is false.
        #. Get the value of non existing key with default value and set is true.
        """
        self.lg.info('Get value of an existing key')
        value = self.client.configGet('key_1')
        self.assertEqual(value, 'value_1')

        self.lg.info('Get the value of a non-existing key')
        with self.assertRaises(j.exceptions.Input) as e:
            self.client.configGet('new_key')

        self.lg.info(
            'Get the value of a non-existing key with default value and set is false')
        value = self.client.configGet('new_key', defval='new_value')
        self.assertEqual(value, 'new_value')

        with self.assertRaises(j.exceptions.Input) as e:
            self.client.configGet('new_value')

        self.lg.info(
            'Get the value of non existing key with default value and set is true')
        value = self.client.configGet('new_key', defval='new_value', set=True)
        self.assertEqual(value, 'new_value')
        self.assertEqual(self.client.configGet('new_key'), 'new_value')

    def test002_config_get_form_dict(self):
        """ JS-017
        **Test Scenario:**
        #. Get the value of an existing key from existing dict.
        #. Get the value of a non-existing key from non-existing dict.
        #. Get the value of an non-existing key from existing dict with default value.
        """
        self.lg.info('Get the value of an existing key from existing dict')
        value = self.client.configGetFromDict('dict_1', 'd_key_1')
        self.assertEqual(value, 'd_value_1')

        self.lg.info(
            'Get the value of a non-existing key from non-existing dict')
        with self.assertRaises(RuntimeError) as e:
            self.client.configGetFromDict('new_dict', 'new_dict_key')

        self.assertEqual(self.client.configGet('new_dict'), {})

        self.lg.info(
            'Get the value of an non-existing key from existing dict with default value')
        value = self.client.configGetFromDict(
            'new_dict', 'new_dict_key', default='new_dict_value')
        self.assertEqual(value, 'new_dict_value')

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/157')
    def test003_config_get_form_dict_bool(self):
        """ JS-018
        **Test Scenario:**
        #. Get the value of an existing key from existing dict.
        #. Get the value of a non-existing key from non-existing dict.
        #. Get the value of an non-existing key from existing dict with default value.
        """
        self.lg.info('Get the value of an existing key from existing dict')
        value = self.client.configGetFromDictBool('dict_1', 'd_key_2')
        self.assertEqual(value, 'd_value_1')
        self.assertTrue(isinstance(value, bool))

        self.lg.info(
            'Get the value of a non-existing key from non-existing dict')
        with self.assertRaises(RuntimeError) as e:
            self.client.configGetFromDictBool('new_dict', 'new_dict_key')

        self.assertEqual(self.client.config.get('new_dict'), {})

        self.lg.info(
            'Get the value of an non-existing key from existing dict with default value')
        value = self.client.configGetFromDictBool(
            'new_dict', 'new_dict_key', default=1)
        self.assertEqual(value, 'new_dict_value')
        self.assertTrue(isinstance(value, bool))

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/67')
    def test004_config_set(self):
        """ JS-019
        **Test Scenario:**
        #. Set new key, value with save equal to true.
        #. Set new key, value with save equal to false.
        #. Set existing key with new value.
        #. Set existing key with the same value.
        """
        self.lg.info('Set new key, value with save equal to true')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        self.assertTrue(self.client.configSet(key, value))
        self.assertEqual(self.get_config().get(key), value)

        self.lg.info('Set new key, value with save equal to false')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        self.assertTrue(self.client.configSet(key, value, save=False))
        self.assertFalse(self.get_config().get(key))

        self.lg.info('Set existing key with new value')
        self.assertTrue(self.client.configSet('key_1', 'new_value_1'))
        self.assertEqual(self.get_config().get('key_1'), 'new_value_1')

        self.lg.info('Set existing key with the same value')
        self.assertFalse(self.client.configSet('key_1', 'new_value_1'))
        self.assertEqual(self.get_config().get('key_1'), 'new_value_1')

    def test005_config_set_in_dict(self):
        """ JS-020
        **Test Scenario:**
        #. Set new dict, key and value.
        #. Set existing dict with new key and value.
        #. Set existing key of dict with new value.
        """
        self.lg.info('Set new dict, key and value')
        self.client.configSetInDict('new_dict', 'new_key', 'new_value')
        self.assertEqual(self.get_config()['new_dict']['new_key'], 'new_value')

        self.lg.info('Set existing dict with new key and value')
        self.client.configSetInDict('dict_1', 'new_key', 'new_value')
        self.assertEqual(self.get_config()['dict_1']['new_key'], 'new_value')

        self.lg.info('Set existing key of dict with new value')
        self.client.configSetInDict('dict_1', 'd_key_1', 'new_value')
        self.assertEqual(self.get_config()['dict_1']['d_key_1'], 'new_value')

    def test006_config_set_in_dict_bool(self):
        """ JS-021
        **Test Scenario:**
        #. Set new dict, key and value.
        #. Set existing dict with new key and value.
        #. Set existing key of dict with new value.
        """
        self.lg.info('Set new dict, key and value')
        self.client.configSetInDictBool('new_dict_1', 'new_key', True)
        self.client.configSetInDictBool('new_dict_2', 'new_key', False)
        self.assertEqual(self.get_config()['new_dict_1']['new_key'], '1')
        self.assertEqual(self.get_config()['new_dict_2']['new_key'], '0')

        self.lg.info('Set existing dict with new key and value')
        self.client.configSetInDictBool('dict_1', 'new_key_1', True)
        self.client.configSetInDictBool('dict_1', 'new_key_2', False)
        self.assertEqual(self.get_config()['dict_1']['new_key_1'], '1')
        self.assertEqual(self.get_config()['dict_1']['new_key_2'], '0')

        self.lg.info('Set existing key of dict with new value')
        self.client.configSetInDictBool('dict_1', 'd_key_1', True)
        self.client.configSetInDictBool('dict_1', 'd_key_2', False)
        self.assertEqual(self.get_config()['dict_1']['d_key_1'], '1')
        self.assertEqual(self.get_config()['dict_1']['d_key_2'], '0')

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/67')
    def test007_config_save(self):
        """ JS-022
        **Test Scenario:**
        #. Set new key without saving.
        #. Save config.
        #. check that new key, value were added to the config file.
        """
        self.lg.info('Set new key without saving')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        self.assertTrue(self.client.configSet(key, value, save=False))
        self.assertFalse(self.get_config().get(key))

        self.lg.info('Save config')
        self.client.configSave()

        self.lg.info('check that new key, value were added to the config file')
        self.assertEqual(self.get_config().get(key), value)

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/159')
    def test08_config_update(self):
        """ JS-023
        **Test Scenario:**
        #. update config with new key.
        #. Update existing key and overwrite.
        """
        self.lg.info('update config with new key')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        ddict = {key: value}
        self.client.configUpdate(ddict)
        self.assertEqual(self.get_config()[key], value)

        self.lg.info('Update existing key and overwrite')
        ddict = {'key_1': 'new_value_1'}
        self.client.configUpdate(ddict, overwrite=True)
        self.assertEqual(self.get_config()['key_1'], 'new_value_1')

    def test009_state_reset(self):
        """ JS-024
        **Test Scenario:**
        #. Reset config.
        #. Check that config file is empty.
        """
        self.lg.info('Reset config')
        self.client.reset()

        self.lg.info('Check that config file is empty')
        self.assertEqual(self.get_config(), {})
