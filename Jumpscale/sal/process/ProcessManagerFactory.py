"""
Process Manager
---------------

This class helps you to run a python method in a separate process and
keep control over it.

For example, here is a method:

def MyMethod(hello):
    ....
    return [something]

You can execute this method in a separate process invoking the process manager 
like this. Please note, arguments need to be passed as dictionary.

    p = j.core.processmanager.startProcess(MyMethod, {"hello": 42})

To keep stuff clean, you need to wait the end of a process
or clear the Process Manager queue when you are done:

    p.wait()
    -- or --
    j.core.processmanager.clear()

To keep your Process object up-to-date with the child process, you need
to explicitly syncronise with 'sync' method (or call a wait or close method):

    p.sync()
    print(p.stdout)

When invoking a sync, you can grab changes from stdout/stderr _since last sync
request_.  The stdout and stderr variable contains the full buffer:

    p.sync()
    print(p.new_stdout)    # will gives you stdout
    p.sync()
    print(p.new_stdout)    # will gives you only new buffer since last sync
    print(p.stdout)        # contains the full stdout since process start
"""

from jumpscale import j

import os
import sys
import time
import traceback
import fcntl
import copy
from io import StringIO
# don't do logging, slows down

import multiprocessing
import datetime

JSBASE = j.application.jsbase_get_class()


class StdDuplicate(JSBASE):

    def __init__(self, original):
        JSBASE.__init__(self)
        self.redirect = original
        self.buffer = StringIO()

    def write(self, message):
        self.redirect.write(message)
        self.buffer.write(message)

    def getBuffer(self):
        return self.buffer.getvalue()

    def restore(self):
        return self.redirect


class Process(JSBASE):

    def __init__(self, name="", method=None, timeout=0, args={}):
        JSBASE.__init__(self)
        self.name = name
        self.method = method
        self.args = args

        self.value = None
        self.error = None
        self.stdout = ""
        self.stderr = ""
        self.outpipe = None
        self.state = "init"

        self.new_stdout = ""
        self.new_stderr = ""
        self.started_at = datetime.datetime.now()
        self.timeout = timeout

        self._stdout = {'read': None, 'write': None, 'fd': None}
        self._stderr = {'read': None, 'write': None, 'fd': None}

    def _flush(self):
        sys.stdout.flush()
        sys.stderr.flush()  # should be not necessary, stderr is unbuffered by default

    def _close(self):
        sys.stdout.close()
        sys.stderr.close()

    def _clean(self):
        self._flush()
        self._close()

    def _setResult(self, value):
        self.outpipe.write(j.data.serializers.json.dumps(value) + "\n")
        self.outpipe.flush()

    def _setSuccess(self, retval):
        self._state = "success"
        self._setResult({"status": self._state, "return": retval})

    def _setPanic(self):
        self._state = "panic"
        self._setResult({"status": self._state, "return": -1})

    def _setException(self, exception):
        self._state = "exception"
        self._setResult(
            {"status": self._state, "return": -1, "eco": exception})

    def startSync(self):
        """
        Run the process in the same process
        """
        if self.method is None:
            msg = "Cannot start process, method not set."
            raise j.exceptions.Input(
                message=msg, level=1, source="", tags="", msgpub="")

        # saving output
        oldout = sys.stdout
        olderr = sys.stderr

        rpipe, wpipe = os.pipe()
        self.outpipe = os.fdopen(wpipe, 'w')
        self.inpipe = os.fdopen(rpipe, 'r')

        sys.stdout = StdDuplicate(sys.stdout)
        sys.stderr = StdDuplicate(sys.stderr)

        # clearing pid, not used
        self.pid = None

        try:
            self._state = "running"
            self.started_at = datetime.datetime.now()
            res = self.method(**self.args)
            self._setSuccess(res)

        except Exception as e:
            eco = j.errorhandler.processPythonExceptionObject(e)
            self._setException(eco.toJson())

        finally:
            os.close(wpipe)

            temp = self.inpipe.read()
            data = j.data.serializers.json.loads(temp)

            self._update(data)
            self.stdout = sys.stdout.getBuffer()
            self.stderr = sys.stderr.getBuffer()

            # new will be the full buffer, there is no sync
            self.new_stdout = self.stdout
            self.new_stderr = self.stderr

            sys.stdout = sys.stdout.restore()
            sys.stderr = sys.stderr.restore()

    def start(self):
        """
        Spawn the method in a new process
        """
        if self.method is None:
            msg = "Cannot start process, method not set."
            raise j.exceptions.Input(
                message=msg, level=1, source="", tags="", msgpub="")
        self.started_at = datetime.datetime.now()
        rpipe, wpipe = os.pipe()
        self._stdout['read'], self._stdout['write'] = os.pipe()
        self._stderr['read'], self._stderr['write'] = os.pipe()

        pid = os.fork()
        if pid == -1:
            raise RuntimeError("Failed to fork()")

        res = None

        if pid == 0:
            # Child -- do the copy, print log to pipe and exit
            try:
                os.close(rpipe)
                os.dup2(self._stdout['write'], sys.stdout.fileno())
                os.dup2(self._stderr['write'], sys.stderr.fileno())
                self.outpipe = os.fdopen(wpipe, 'w')

                # print("ARGS:%s" % args)
                # j.core.processmanager.cache_clears()
                self._state = "running"
                res = self.method(**self.args)

            except Exception as e:
                eco = j.errorhandler.processPythonExceptionObject(e)

                self._setException(eco.toJson())
                self._clean()
                os._exit(1)

            finally:
                self._setSuccess(res)
                self._clean()
                os._exit(0)

            # should never arrive here
            self._setPanic()
            os._exit(1)

        else:  # parent
            os.close(wpipe)
            os.close(self._stdout['write'])
            os.close(self._stderr['write'])
            self.pid = pid

            # setting pipes in non-block, to catch "running" later
            self.outpipe = os.fdopen(rpipe)
            fcntl.fcntl(self.outpipe, fcntl.F_SETFL, os.O_NONBLOCK)

            self._stdout['fd'] = os.fdopen(self._stdout['read'])
            fcntl.fcntl(self._stdout['fd'], fcntl.F_SETFL, os.O_NONBLOCK)

            self._stderr['fd'] = os.fdopen(self._stderr['read'])
            fcntl.fcntl(self._stderr['fd'], fcntl.F_SETFL, os.O_NONBLOCK)

    def _readAvailable(self, fd):
        temp = ""
        for block in iter(lambda: fd.read(8), ""):
            temp += block

        return temp

    def isDone(self):
        return (self.state != "running" and self.state != "init")

    def sync(self):
        if self.pid is None:
            return self.state

        # nothing to do more if the process is done
        if self.isDone():
            return self.state

        temp = self._readAvailable(self.outpipe)
        self._syncStd()

        # if the pipe is empty, the process is still running
        if temp == "":
            data = {"status": "running"}

        # otherwise, process is ended and we know the result
        else:
            data = j.data.serializers.json.loads(temp)

        # update local class with data
        self._update(data)

        return data['status']

    def _syncStd(self):
        self.new_stdout = self._readAvailable(self._stdout['fd'])
        self.new_stderr = self._readAvailable(self._stderr['fd'])

        self.stdout += self.new_stdout
        self.stderr += self.new_stderr

    def _update(self, data):
        self.state = data['status']

        if data['status'] == 'running':
            return

        self.value = data['return']

        if data['status'] == 'exception':
            self.error = data['eco']

    def wait(self):
        # wait until the process is finished
        if self.pid is None:
            return

        try:
            data = os.waitpid(self.pid, 0)
            if self.sync() != "running":
                self.pid = None

        except Exception as e:
            # print("waitpid: ", e)
            pass

    def __repr__(self):
        out = "Process name: %s, status: %s, return: %s" % (
            self.name, self.state, self.value)

        if self.state != "running":
            out += "\n== Stdout ==\n%s" % self.stdout
            out += "\n== Stderr ==\n%s" % self.stderr

        if self.state == "exception":
            out += "\nError:\n%s" % self.error

        return out

    def close(self):
        self.sync()
        self.outpipe.close()

        # clear child if process is done
        if self.isDone():
            self.wait()

        # kill child if still running
        if self.state == "running":
            j.sal.process.kill(self.pid)
            self._syncStd()
            self.wait()
            self.state = "killed"

        self.pid = None

    __str__ = __repr__


class ProcessManagerFactory(JSBASE):

    def __init__(self):
        self.__jslocation__ = "j.sal.processmanager"
        JSBASE.__init__(self)
        self._lastnr = 0
        self.processes = {}
        self.timeout = 5400
        # self.log.addHandler(j.logger._LoggerFactory__fileRotateHandler('processmanager'))

    def cache_clears(self):
        """
        call this in subprocess if you want to make sure that no sockets will be reused
        """
        j.clients.ssh.cache = {}
        j.clients.redis._redis = {}
        j.clients.redis._redisq = {}
        j.clients.postgres.clients = {}

        # j.core.db = Redis(unix_socket_path='/tmp/redis.sock')

    def getQueue(self, size=1000):
        """
        can get this & give to startProcess in args (see test)
        """
        return multiprocessing.Queue(size)

    def getProcess(
            self,
            method=None,
            args={},
            name="",
            autoclear=True,
            autowait=True,
            timeout=0):
        if name == "":
            name = "process_%s" % self._lastnr
            self._lastnr += 1

        if len(self.processes) > 100 and autoclear:
            self.clear()

        if len(self.processes) > 100:
            print("no clear")

            if autowait:
                if not autoclear:
                    raise j.exceptions.Input(
                        message="cannot wait if autoclear=False", level=1,
                        source="", tags="", msgpub="")
                while True:
                    print("too many subprocesses, am waiting")
                    time.sleep(1)
                    self.clear()
                    time.sleep(1)
                    if len(self.processes) < 100:
                        break
            else:
                raise j.exceptions.Input(
                    message="cannot launch more than 100 sub processes",
                    level=1, source="", tags="", msgpub="")

        p = Process(name, method, timeout, args)
        self.processes[p.name] = p
        return p

    def startProcess(
            self,
            method,
            args={},
            name="",
            autoclear=True,
            autowait=True,
            sync=False,
            timeout=0):
        p = self.getProcess(
            method=method,
            args=args,
            name=name,
            autoclear=autoclear,
            autowait=autowait,
            timeout=timeout)

        if sync:
            p.startSync()

        else:
            p.start()

        return p

    def clear(self, error=True):
        # print("clearing process list")
        keys = [item for item in self.processes.keys()]
        cleared = 0

        # print(len(keys))
        for key in keys:
            p = self.processes[key]
            status = p.sync()

            if (status == "error" and error) or status == "success":
                p.close()
                self.processes.pop(p.name)
                cleared += 1

            else:
                # check for timedout processes and clean.
                now = datetime.datetime.now()
                time_diff = now - p.started_at
                # check if the process has a specific time out.
                if p.timeout:
                    if time_diff.total_seconds() > p.timeout:
                        self.logger.warning(
                            "closing process %s, process timeout exceeded")
                        p.close()
                        self.processes.pop(p.name)
                        cleared += 1
                else:
                    # check if the process exceeded the default timeout.
                    if time_diff.total_seconds() > self.timeout:
                        self.logger.warning(
                            "closing process %s, default timeout exceeded")
                        p.close()
                        self.processes.pop(p.name)
                        cleared += 1

        remaining = [item for item in self.processes.keys()]
        if remaining:
            self.logger.info('Remaining processes after clear')
        for key in remaining:
            status = self.processes[key].sync()
            self.logger.info('Remaining: process %s : %s' % (key, status))
        return cleared

    def testSync(self):
        """
        Simple test, spaw, processes and wait for them
        """
        def amethod(x=None, till=1):
            counter = 0
            print("OK:%s" % x)
            while True:
                counter += 1
                sys.stderr.write("Counter: %d\n" % counter)
                time.sleep(0.1)

                if counter == till:
                    return x

        r = {}
        nr = 10

        print(" * Testing simple method (sync) x%d" % nr)

        for i in range(nr):
            print("Running process %d" % i)
            r[i] = self.startProcess(amethod, {"x": i, "till": 1}, sync=True)

        for i in range(nr):
            print(r[i])

        print(" * Simple method (sync) done.")

        """
        Simple error managemebt.
        """
        print(" * Testing error")

        def anerror(x=None, till=1):
            print("a line - normal")
            print("a line2 - normal")
            j.logger.log("testlog")
            raise RuntimeError("raised, generic python error")

        p = self.startProcess(anerror, {"x": i, "till": 1}, sync=True)
        p.wait()

        # next should print the error & the log
        print(p)

        print(" * Error done.")

    def test(self):
        """
        Simple test, spaw, processes and wait for them
        """
        def amethod(x=None, till=1):
            counter = 0
            print("OK:%s" % x)
            while True:
                counter += 1
                sys.stderr.write("Counter: %d\n" % counter)
                time.sleep(0.1)

                if counter == till:
                    return x

        r = {}
        nr = 10

        print(" * Testing simple method x%d" % nr)

        for i in range(nr):
            r[i] = self.startProcess(amethod, {"x": i, "till": 1})

        for i in range(nr):
            r[i].wait()
            print(r[i])

        print(" * Simple method done.")

        """
        Simple error managemebt.
        """
        print(" * Testing error")

        def anerror(x=None, till=1):
            print("a line - normal")
            print("a line2 - normal")
            j.logger.log("testlog")
            raise RuntimeError("raised, generic python error")

        p = self.startProcess(anerror, {"x": i, "till": 1})
        p.wait()

        # next should print the error & the log
        print(p)

        print(" * Error done.")

        """
        Test a process which waits for data from a queue and stop on specific value
        """
        print(" * Testing queue")

        def queuetest(queue):
            counter = 0
            print("Queue Inner test")
            while True:
                if not queue.empty():
                    last = queue.get()
                    counter += 1
                    print("From queue: %s" % last)
                    if last == "stop":
                        return last

                    time.sleep(0.1)

                else:
                    return "empty"

        q = self.getQueue()
        q.put("test1")
        q.put("test2")
        q.put("test3")
        q.put("test4")
        q.put("test5")
        q.put("stop")   # remove me to test the queue²

        p = self.startProcess(queuetest, {"queue": q})

        # fill the queue here

        p.wait()
        print(p)

        print(" * Queue done.")

        """
        Simple slow process, and fetch asynchronously stdout and stderr
        """

        print(" * Testing slow process")

        def slowprocess(till):
            print("Init slow process")
            x = 0
            while x < till:
                print("Waiting %d" % x)
                time.sleep(1)
                x += 1

            return 0

        p = self.startProcess(slowprocess, {'till': 10})
        while p.sync() == "running":
            if p.new_stdout:
                print("stdout >> %s" % p.new_stdout)

            if p.new_stderr:
                print("stderr >> %s" % p.new_stderr)

            time.sleep(2)

        p.wait()
        print(p)

        print(" * Slow process done.")

        """
        Spawn a process and kill it before it ends
        """
        print(" * Testing prematured close")

        def prematured(timewait):
            print("Waiting %.2f seconds" % timewait)
            time.sleep(timewait)
            print("Timewait elapsed")
            return 0

        p = self.startProcess(prematured, {'timewait': 5})
        time.sleep(1)
        p.close()
        print(p)

        print(" * Prematured test done.")

    def perftest(self):

        # can run more than 1000 process per sec

        def amethod(x=None, till=1):
            print("I'm process %d" % x)
            return x

        r = {}
        nr = 1500
        start = time.time()
        print("Starting benchmark, launching %d processes" % nr)

        for i in range(nr):
            r[i] = self.startProcess(amethod, {"x": i, "till": 1})

        for i in range(nr):
            r[i].wait()

        print(r[100])
        cl = self.clear()
        print("Process cleared at the end: %d" % cl)

        diff = time.time() - start
        pps = nr / diff

        print(
            "Number of processes per seconds: %s (%d process in %d seconds)" %
            (pps, nr, diff))
