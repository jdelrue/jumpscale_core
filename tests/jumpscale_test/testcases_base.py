import time
import signal
import uuid
import random
import logging
from datetime import timedelta
from unittest import TestCase
from nose.tools import TimeExpired
import uuid


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
        return str(uuid.uuid4()).replace('-', '')[:length]
