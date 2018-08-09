import os, shutil
from random import randint
from .testcases_base import TestcasesBase
from jumpscale import j
from parameterized import parameterized


class TestJSALFS(TestcasesBase):
    def setUp(self):
        super().setUp()
        self.file_name = ''

    def tearDown(self):
        if self.file_name:
            os.remove(self.file_name)
        super().tearDown()

    def test001_changeDir(self):
        """ JS-001

        **Test Scenario:**
        #. Get the current dir
        #. Change the current dir, should succeed
        """
        current_dir = os.getcwd()
        if current_dir == "/root":
            self.assertEqual(j.sal.fs.changeDir('/etc'), '/etc')
        else:
            self.assertEqual(j.sal.fs.changeDir('/root'), '/root')
        os.chdir(current_dir)

    def test002_changeDir_longpath(self):
        """ JS-002

        **Test Scenario:**
        #. Create a long path
        #. Change the current dir to this long path, should succeed
        """
        current_dir = os.getcwd()
        long_path = '/root/test'
        for i in range(0, randint(1, 10)):
            long_path += '/test00%d' % i

        os.makedirs(long_path)
        self.assertEqual(j.sal.fs.changeDir(long_path), long_path)
        shutil.rmtree('/root/test')
        os.chdir(current_dir)

    def test003_changeDir_file(self):
        """ JS-003

        **Test Scenario:**
        #. Create a file
        #. Change the current dir to this file, should fail
        #. Delete file.
        """
        file_name = "newfile%d.txt" % randint(1, 10000)
        os.mknod(file_name)
        current_dir = os.getcwd() + ' /' + file_name

        with self.assertRaises(ValueError):
            j.sal.fs.changeDir(current_dir)

        os.remove(file_name)

    def test004_changeDir_wrongDir(self):
        """ JS-004

        **Test Scenario:**
        #. Change the current dir to not existing dir, Should fail.
        """
        with self.assertRaises(ValueError):
            j.sal.fs.changeDir('/tmp/%d' % randint(1, 1000))

    def test005_changeFileNames(self):
        """ JS-005

        **Test Scenario:**
        #. Create new file.
        #. Change file name, should succeed.
        #. Delete the file.
        """
        self.file_name = self.random_string()
        new_file_name = self.random_string()
        os.mknod(self.file_name)
        current_dir = os.getcwd()
        j.sal.fs.changeFileNames(self.file_name, new_file_name, current_dir)
        self.file_name = new_file_name
        self.assertTrue(os.path.isfile(new_file_name))

    def test006_changeFileNames_empty(self):
        """ JS-006

        **Test Scenario:**
        #. Change file name with empty input, should fail.
        """
        current_dir = os.getcwd()
        with self.assertRaises(ValueError):
            j.sal.fs.changeFileNames('', '', current_dir)

    def test007_changeFileNames_sameDirName(self):
        """ JS-007

        **Test Scenario:**
        #. Create new file with the dir name
        #. Change file name, should succeed.
        """
        current_dir = os.getcwd()
        self.file_name = current_dir.split('/')[-1]
        new_file_name = self.random_string()
        os.mknod(self.file_name)
        j.sal.fs.changeFileNames(self.file_name, new_file_name, current_dir)
        self.file_name = new_file_name
        self.assertTrue(os.path.isfile(new_file_name))

    @parameterized.expand(['/test/xTremX','@3%6123', 'Запомните'])
    def test008_checkDirParam(self, dir_name):
        """ JS-037

        **Test Scenario:**
        #. checkDirParam with dir_name in [english word, special char, non-english]
        """
        data = j.sal.fs.checkDirParam(dir_name)
        self.assertIn(dir_name, data)

    def test009_chmod(self):
        """ JS-042

        **Test Scenario:**
        #. Create new file
        #. change file mod to 777, should succeed.
        #. change file mod to wrong value, should fail.
        #. Delete file
        """
        self.file_name = self.random_string()
        os.mknod(self.file_name)
        current_dir = os.getcwd() + '/' + self.file_name
        j.sal.fs.chmod(current_dir, 0o777)
        st = os.stat(path=current_dir)
        self.assertEqual(oct(st.st_mode)[-3:], '777')

    def test009_chmod_wrong_value(self):
        """ JS-043

        **Test Scenario:**
        #. Create new file
        #. change file mod to 444444, should fail.
        #. change file mod to wrong value, should fail.
        #. Delete file
        """
        self.file_name = self.random_string()
        os.mknod(self.file_name)
        current_dir = os.getcwd() + '/' + self.file_name
        st_old = os.stat(path=current_dir)
        old_mod = oct(st_old.st_mode)[-3:]
        j.sal.fs.chmod(current_dir, 0o4444)
        st = os.stat(path=current_dir)
        self.assertEqual(oct(st.st_mode)[-3:], old_mod)
