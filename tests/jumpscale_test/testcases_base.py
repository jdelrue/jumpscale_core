import time
import signal
import uuid
import random
import logging
from datetime import timedelta
from unittest import TestCase
from nose.tools import TimeExpired
import uuid
import os
import tempfile
import shutil
import atexit

# XXX bit of a problem with jumpscale, some of the tests are
# destructive (issue #33).  to avoid that, a temporary directory is created
# here, and the HOSTCFGDIR environment variable set.  it's done here
# GLOBALLY because jumpscale is, annoyingly, a global variable and a global
# import *sigh*...

tempdirpth = tempfile.mkdtemp()
tempcfg = os.path.join(tempdirpth, "cfg")
os.environ['HOSTDIR'] = tempdirpth
os.environ['HOSTCFGDIR'] = os.path.join(tempdirpth, "cfg")
os.environ['HOSTCFGDIR'] = tempcfg
os.mkdir(tempcfg)

def cleanup():
    shutil.rmtree(tempdirpth)

atexit.register(cleanup)

def squash_dictionaries(d1, d2):
    from io import StringIO
    def writedict(f, d):
        keys = list(d.keys())
        keys.sort()
        for k in keys:
            if isinstance(k, bytes):
                f.write("%s: %s\n" % (k.decode('utf-8'),
                                     d[k].decode('utf-8')))
            else:
                f.write("%s: %s\n" % (str(k), str(d[k])))
    envd = StringIO()
    writedict(envd, d1)
    exd = StringIO()
    writedict(exd, d2)

    return envd.getvalue(), exd.getvalue()


class TestcasesBase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lg = self.logger()

    def setUp(self):
        self._testID = self._testMethodName
        self._startTime = time.time()
        self.lg.info(
            '====== Testcase [{}] is started ======'.format(
                self._testID))

        def timeout_handler(signum, frame):
            raise TimeExpired(
                'Timeout expired before end of test %s' %
                self._testID)

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(540)

    def tearDown(self):
        self._endTime = time.time()
        self._duration = int(self._endTime - self._startTime)
        self.lg.info(
            'Testcase [{}] is ended, Duration: {} seconds'.format(
                self._testID, self._duration))

    def logger(self):
        logger = logging.getLogger('Jumpscale')
        if not logger.handlers:
            fileHandler = logging.FileHandler('testsuite.log', mode='w')
            formatter = logging.Formatter(
                ' %(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
            fileHandler.setFormatter(formatter)
            logger.addHandler(fileHandler)

        return logger

    def random_string(self, length=10):
        return "random"+str(uuid.uuid4()).replace('-', '')[:length]
