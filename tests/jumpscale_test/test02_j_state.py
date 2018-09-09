from .testcases_base import TestcasesBase
import os
import random
import pytoml
import unittest
import uuid


class TestJSTATE(TestcasesBase):

    def get_state(self):
        try:
            with open(self.state_path, 'r') as f:
                content = pytoml.load(f)
        except FileNotFoundError:
            content = {}

        return content

    def reset_state(self):
        with open(self.state_path, 'w') as f:
            f.write(pytoml.dumps(self.state_file_content))

    def update_state(self, data):
        content = dict(self.state_file_content)
        content.update(data)
        with open(self.state_path, 'w') as f:
            f.write(pytoml.dumps(content))
        return content

    def setUp(self):
        super().setUp()
        self.client = self._j.core.state
        self.state_path = self.client.configStatePath
        self.state_file_content = self.get_state()

        self.lg.info('Add test state (setUp)')
        test_state = {
            'key_1': 'value_1',
            'key_2': 'value_2',
            'dict_1': {
                'd_key_1': 'd_value_1',
                'd_key_2': True,
                'd_key_3': False
            }
        }
        self.client._configState = self.update_state(test_state)

    def tearDown(self):
        self.lg.info('Remove test state (tearDown)')
        self.reset_state()
        super().tearDown()

    def test001_state_get(self):
        """ JS-008
        **Test Scenario:**
        #. Get value of an existing key.
        #. Get the value of a non-existing key.
        #. Get the value of a non-existing key with default value and set is false.
        #. Get the value of non existing key with default value and set is true.
        """
        self.lg.info('Get value of an existing key')
        value = self.client.stateGet('key_1')
        self.assertEqual(value, 'value_1')

        self.lg.info('Get the value of a non-existing key')
        with self.assertRaises(self._j.exceptions.Input) as e:
            self.client.stateGet('new_key')

        self.lg.info(
            'Get the value of a non-existing key with default value and set is false')
        value = self.client.stateGet('new_key', defval='new_value')
        self.assertEqual(value, 'new_value')

        with self.assertRaises(self._j.exceptions.Input) as e:
            self.client.stateGet('new_value')

        self.lg.info(
            'Get the value of non existing key with default value and set is true')
        value = self.client.stateGet('new_key', defval='new_value', set=True)
        self.assertEqual(value, 'new_value')
        self.assertEqual(self.client.stateGet('new_key'), 'new_value')

    def test002_state_get_form_dict(self):
        """ JS-009
        **Test Scenario:**
        #. Get the value of an existing key from existing dict.
        #. Get the value of a non-existing key from non-existing dict.
        #. Get the value of an non-existing key from existing dict with default value.
        """
        self.lg.info('Get the value of an existing key from existing dict')
        value = self.client.stateGetFromDict('dict_1', 'd_key_1')
        self.assertEqual(value, 'd_value_1')

        self.lg.info(
            'Get the value of a non-existing key from non-existing dict')
        with self.assertRaises(RuntimeError) as e:
            self.client.stateGetFromDict('new_dict', 'new_dict_key')

        self.assertEqual(self.client.stateGet('new_dict'), {})

        self.lg.info(
            'Get the value of an non-existing key from existing dict with default value')
        value = self.client.stateGetFromDict(
            'new_dict', 'new_dict_key', default='new_dict_value')
        self.assertEqual(value, 'new_dict_value')

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/157')
    def test003_state_get_form_dict_bool(self):
        """ JS-010
        **Test Scenario:**
        #. Get the value of an existing key from existing dict.
        #. Get the value of a non-existing key from non-existing dict.
        #. Get the value of an non-existing key from existing dict with default value.
        """
        self.lg.info('Get the value of an existing key from existing dict')
        value = self.client.stateGetFromDictBool('dict_1', 'd_key_2')
        self.assertEqual(value, 'd_value_1')
        self.assertTrue(isinstance(value, bool))

        self.lg.info(
            'Get the value of a non-existing key from non-existing dict')
        with self.assertRaises(RuntimeError) as e:
            self.client.stateGetFromDictBool('new_dict', 'new_dict_key')

        self.assertEqual(self.client.stateGet('new_dict'), {})

        self.lg.info(
            'Get the value of an non-existing key from existing dict with default value')
        value = self.client.stateGetFromDictBool(
            'new_dict', 'new_dict_key', default=1)
        self.assertEqual(value, 'new_dict_value')
        self.assertTrue(isinstance(value, bool))

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/67')
    def test004_state_set(self):
        """ JS-011
        **Test Scenario:**
        #. Set new key, value with save equal to true.
        #. Set new key, value with save equal to false.
        #. Set existing key with new value.
        #. Set existing key with the same value.
        """
        self.lg.info('Set new key, value with save equal to true')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        self.assertTrue(self.client.stateSet(key, value))
        self.assertEqual(self.get_state().get(key), value)

        self.lg.info('Set new key, value with save equal to false')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        self.assertTrue(self.client.stateSet(key, value, save=False))
        self.assertFalse(self.get_state().get(key))

        self.lg.info('Set existing key with new value')
        self.assertTrue(self.client.stateSet('key_1', 'new_value_1'))
        self.assertEqual(self.get_state().get('key_1'), 'new_value_1')

        self.lg.info('Set existing key with the same value')
        self.assertFalse(self.client.stateSet('key_1', 'new_value_1'))
        self.assertEqual(self.get_state().get('key_1'), 'new_value_1')

    def test005_state_set_in_dict(self):
        """ JS-012
        **Test Scenario:**
        #. Set new dict, key and value.
        #. Set existing dict with new key and value.
        #. Set existing key of dict with new value.
        """
        self.lg.info('Set new dict, key and value')
        self.client.stateSetInDict('new_dict', 'new_key', 'new_value')
        self.assertEqual(self.get_state()['new_dict']['new_key'], 'new_value')

        self.lg.info('Set existing dict with new key and value')
        self.client.stateSetInDict('dict_1', 'new_key', 'new_value')
        self.assertEqual(self.get_state()['dict_1']['new_key'], 'new_value')

        self.lg.info('Set existing key of dict with new value')
        self.client.stateSetInDict('dict_1', 'd_key_1', 'new_value')
        self.assertEqual(self.get_state()['dict_1']['d_key_1'], 'new_value')

    def test006_state_set_in_dict_bool(self):
        """ JS-013
        **Test Scenario:**
        #. Set new dict, key and value.
        #. Set existing dict with new key and value.
        #. Set existing key of dict with new value.
        """
        self.lg.info('Set new dict, key and value')
        self.client.stateSetInDictBool('new_dict_1', 'new_key', True)
        self.client.stateSetInDictBool('new_dict_2', 'new_key', False)
        self.assertEqual(self.get_state()['new_dict_1']['new_key'], '1')
        self.assertEqual(self.get_state()['new_dict_2']['new_key'], '0')

        self.lg.info('Set existing dict with new key and value')
        self.client.stateSetInDictBool('dict_1', 'new_key_1', True)
        self.client.stateSetInDictBool('dict_1', 'new_key_2', False)
        self.assertEqual(self.get_state()['dict_1']['new_key_1'], '1')
        self.assertEqual(self.get_state()['dict_1']['new_key_2'], '0')

        self.lg.info('Set existing key of dict with new value')
        self.client.stateSetInDictBool('dict_1', 'd_key_1', True)
        self.client.stateSetInDictBool('dict_1', 'd_key_2', False)
        self.assertEqual(self.get_state()['dict_1']['d_key_1'], '1')
        self.assertEqual(self.get_state()['dict_1']['d_key_2'], '0')

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/67')
    def test007_state_save(self):
        """ JS-014
        **Test Scenario:**
        #. Set new key without saving.
        #. Save state.
        #. check that new key, value were added to the state file.
        """
        self.lg.info('Set new key without saving')
        key = str(uuid.uuid4()).replace('-', '')[:10]
        value = str(uuid.uuid4()).replace('-', '')[:10]
        self.assertTrue(self.client.stateSet(key, value, save=False))
        self.assertFalse(self.get_state().get(key))

        self.lg.info('Save state')
        self.client.configSave()

        self.lg.info('check that new key, value were added to the state file')
        self.assertEqual(self.get_state().get(key), value)

    @unittest.skip(
        'https://github.com/threefoldtech/jumpscale_core/issues/33')
    def test008_state_reset(self):
        """ JS-015
        **Test Scenario:**
        #. Reset state.
        #. Check that state file is empty.
        """
        self.lg.info('Reset state')
        self.client.reset()

        self.lg.info('Check that state file is empty')
        self.assertEqual(self.get_state(), {})
