import os
import unittest
import random
import platform
import sys
from .testcases_base import TestcasesBase, squash_dictionaries
from jumpscale import j
from parameterized import parameterized


class EXECUTER(TestcasesBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.executer = j.tools.executor.local_get()

    def test01_read_file(self):
        """ JS-061
        **Test Scenario:**
        #. Create new file [f1].
        #. Write data to file [f1].
        #. Read file [f1] data.
        """
        self.lg.info('Create new file [f1]')
        string = self.random_string()
        filename = self.random_string()
        filepath = '/tmp/{}'.format(filename)

        self.lg.info('Write data to file [f1]')
        os.system('echo {} > {}'.format(string, filepath))

        self.lg.info('Read file [f1] data')
        file_content = self.executer.file_read(filepath)
        self.assertEqual(file_content.strip(), string)
        os.system('rm -f {}'.format(filepath))

    def test02_write_file(self):
        """ JS-062
        **Test Scenario:**
        #. Create new file [f1].
        #. Write data to file [f1].
        #. Read file [f1], and check its data.
        """
        string = self.random_string()
        filename = self.random_string()
        filepath = '/tmp/{}'.format(filename)

        self.executer.file_write(filepath, string)
        file_content = self.executer.file_read(filepath)
        self.assertEqual(string, file_content)
        os.system('rm -f {}'.format(filepath))

    @parameterized.expand(['upload', 'download'])
    def test03_upload_download(self, method):
        """ JS-063
        **Test Scenario:**
        #.
        """
        source_dir = '/tmp/{}'.format(self.random_string())
        dest_dir = '/tmp/{}'.format(self.random_string())

        os.system('mkdir {}'.format(source_dir))
        os.system('mkdir {}'.format(dest_dir))

        source_files = [self.random_string() for _ in range(3)]

        os.system('cd {}; touch {}'.format(source_dir, ' '.join(source_files)))

        if method == 'upload':
            self.executer.upload(source_dir, dest_dir)
        elif method == 'download':
            self.executer.download(source_dir, dest_dir)

        files = os.listdir(dest_dir)
        self.assertEqual(set(source_files), set(files))
        os.system('rm -rf {}'.format(' '.join([source_dir, dest_dir])))

    def test04_exists(self):
        """ JS-064
        **Test Scenario:**
        #. Check if valid path is exists, should return true.
        #. Check if invalid path is exists, should return false.
        """
        path = '/root'
        self.assertTrue(self.executer.exists(path))

        path = self.random_string()
        self.assertFalse(self.executer.exists(path))

    def test05_platform_type(self):
        """ JS-065
        **Test Scenario:**
        #. Check system architecture.
        """
        architecture = platform.architecture()[0]
        if architecture == '64bit':
            self.assertTrue(self.executer.platformtype.is64bit)
            self.assertFalse(self.executer.platformtype.is32bit)

        elif architecture == '32bit':
            self.assertTrue(self.executer.platformtype.is32bit)
            self.assertFalse(self.executer.platformtype.is64bit)

    def test06_env(self):
        """ JS-066
        **Test Scenario:**
        #. Compare executer.env with os environment variables,
           should be the same.  However one creates bytes and
           the other creates strings, so convert them before
           comparing
        """
        v1, v2 = squash_dictionaries(os.environ._data, self.executer.env)

        self.assertEqual(v1, v2)
