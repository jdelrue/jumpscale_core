import sys
import string
import inspect
import imp
import Jumpscale.errorhandling.JSExceptions as JSExceptions
from .ErrorConditionObject import ErrorConditionObject
import colored_traceback
from Jumpscale import j


# def embed():
#     return "embed" in sys.__dict__


colored_traceback.add_hook(always=True)


# class BaseException(Exception):
#     def __init__(self, message="", eco=None):
#         print ("OUR BASE EXCEPTION")
#         self.message = message
#         self.eco = eco

#     def __str__(self):
#         if self.eco!=None:
#             return str(j.errorhandler.getErrorConditionObject(self.eco))
#         return "Unexpected Error Happened"

#     __repr__ = __str__

JSBASE = j.application.jsbase_get_class()


class HaltException(Exception, JSBASE):
    def __init__(self):
        JSBASE.__init__(self)


class ErrorHandler(JSBASE):

    def __init__(self, storeErrorConditionsLocal=True):
        if not hasattr(self, '__jslocation__'):
            self.__jslocation__ = "j.core.errorhandler"
        JSBASE.__init__(self)
        self._blacklist = None
        self.lastAction = ""
        self.setExceptHook()
        self.lastEco = None
        self.escalateToRedis = False
        self._escalateToRedisFunction = None
        self._scriptsInRedis = False
        self.exceptions = JSExceptions
        j.exceptions = JSExceptions

    def _registerScrips(self):
        if self._scriptsInRedis is False:
            luapath = "%s/errorhandling/eco.lua" % j.dirs.JSLIBDIR
            lua = j.sal.fs.fileGetContents(luapath)
            self._escalateToRedisFunction = j.core.db.register_script(lua)
            self._scriptsInRedis = True

    def _send2Redis(self, eco):
        if self.escalateToRedis:
            self._registerScrips()
            data = eco.json
            res = self._escalateToRedisFunction(
                keys=["queues:eco", "eco:incr", "eco:occurrences", "eco:objects", "eco:last"], args=[eco.key, data])
            res = self.j.data.serializers.json.loads(res)
            return res
        else:
            return None

    @property
    def blacklist(self):
        if self._blacklist is None:
            key = 'eco.blacklist'
            if j.application.config.jumpscale.get('application').get(key):
                self._blacklist = j.application.config.jumpscale.get('application').getList(key)
            else:
                self._blacklist = list()
        return self._blacklist

    def strip_to_ascii(text):
        return string.join([char for char in str(text) if (
            (ord(char) > 31 and ord(char) < 127) or ord(char) == 10)], "")

    def setExceptHook(self):
        sys.excepthook = self.excepthook
        self.inException = False

    def getLevelName(self, level):
        return LEVELMAP.get(level, 'UNKNOWN')

    def getErrorConditionObject(self, ddict={}, msg="", msgpub="", category="",
                                level=1, type="UNKNOWN", tb=None, tags=""):
        """
        @data is dict with fields of errorcondition obj
        returns only ErrorConditionObject which should be used in jumpscale to define an errorcondition (or potential error condition)

        """
        errorconditionObject = ErrorConditionObject(
            ddict=ddict, msg=msg, msgpub=msgpub, level=level, category=category, type=type, tb=tb, tags=tags)
        return errorconditionObject

    def processPythonExceptionObject(self, exceptionObject, tb=None, message=None):
        """
        how to use

        try:
            ##do something
        except Exception,e:
            j.errorhandler.processPythonExceptionObject(e)

        @param exceptionObject is errorobject thrown by python when there is an exception
        @param ttype : is the description of the error, can be None
        @param tb : can be a python data object for traceback, can be None

        @return ecoObj

        the errorcondition is then also processed e.g. send to local logserver and/or stored locally in errordb
        """
        eco = self.parsePythonExceptionObject(
            exceptionObject=exceptionObject, tb=tb, message=message)
        eco.process()
        return eco

    def parsePythonExceptionObject(self, exceptionObject, tb=None, message=None):
        """
        how to use

        try:
            ##do something
        except Exception,e:
            eco=j.errorhandler.parsePythonExceptionObject(e)

        eco is jumpscale internal format for an error
        next step could be to process the error objecect (eco) e.g. by eco.process()

        @param exceptionObject is errorobject thrown by python when there is an exception
        @param ttype : is the description of the error, can be None
        @param tb : can be a python data object for traceback, can be None

        @return a ErrorConditionObject object as used by jumpscale (should be the only type of object we pass around)


        """

        # this allows to do raise eco
        # was BaseException  , dont understand (despiegk)
        if isinstance(exceptionObject, ErrorConditionObject):
            # return self.getErrorConditionObject(exceptionObject.eco)
            return exceptionObject

        if not isinstance(exceptionObject, BaseException):
            self.logger.debug(
                "did not receive an Exceptio object for python exception, this is serious bug.")
            raise ValueError("exceptionObject was:\n%s not instance of BaseException" % exceptionObject)

        if tb is None:
            ttype, exc_value, tb = sys.exc_info()

        if hasattr(exceptionObject, "codetrace"):
            codetrace = exceptionObject.codetrace
        else:
            codetrace = True

        if hasattr(exceptionObject, "eco"):
            eco = exceptionObject.eco
        else:
            eco = None

        if hasattr(exceptionObject, "level"):
            level = exceptionObject.level
        else:
            level = 1

        if hasattr(exceptionObject, "msgpub"):
            msgpub = exceptionObject.msgpub
        else:
            msgpub = ""


        if hasattr(exceptionObject, "type"):
            type = exceptionObject.type
        else:
            type = "UNKNOWN"

        if message is None:
            if hasattr(exceptionObject, "message"):
                message = exceptionObject.message
                if self.j.data.types.list.check(message):
                    message = message[0]  # @hack to let all work again
            else:
                message = str(exceptionObject)

        if message.find("((") != -1:
            tags = self.j.data.regex.findOne("\(\(.*\)\)", message)
            message.replace(tags, "")
        else:
            tags = ""

        if hasattr(exceptionObject, "tags"):
            tags = exceptionObject.tags + " %s" % tags

        if eco is None:
            eco = self.getErrorConditionObject(
                msg=message, msgpub=msgpub, level=level, tb=tb, tags=tags, type=type)

        if codetrace:
            # so for unknown exceptions not done through raise j.exceptions we
            # will do stacktrace
            eco.tracebackSet(tb, exceptionObject)


        eco.exceptionclassname = exceptionObject.__class__.__name__

        return eco

    def reRaiseECO(self, eco):
        if eco.exceptionmodule:
            mod = imp.load_package(eco.exceptionmodule, eco.exceptionmodule)
        else:
            import builtins as mod
        Klass = getattr(mod, eco.exceptionclassname, RuntimeError)
        exc = Klass(eco.errormessage)
        for key, value in list(self.j.data.serializers.json.loads(eco.exceptioninfo).items()):
            setattr(exc, key, value)
        raise exc

    def excepthook(self, ttype, exceptionObject, tb):
        """ every fatal error in jumpscale or by python itself will result in an exception
        in this function the exception is caught.
        This routine will create an errorobject & escalate to the infoserver
        @ttype : is the description of the error
        @tb : can be a python data object or a Event
        """

        # print ("jumpscale EXCEPTIONHOOK")
        if self.inException:
            self.logger.error(
                "ERROR IN EXCEPTION HANDLING ROUTINES, which causes recursive errorhandling behavior.")
            self.logger.error(exceptionObject)
            sys.exit(1)
            return

        self.inException = True

        eco = self.parsePythonExceptionObject(exceptionObject, tb=tb)

        eco.process()

        self.inException = False

        # if eco.traceback != "":
        #     print("\n**** TRACEBACK ***")
        #     eco.printTraceback()
        self.logger.error(eco)
        sys.exit(1)

    def checkErrorIgnore(self, eco):
        if j.application.debug:
            ignorelist = []
        else:
            ignorelist = ["KeyboardInterrupt"]
        for item in ignorelist:
            if eco.errormessage.find(item) != -1:
                return True
        if j.application.appname in self.blacklist:
            return True
        return False

    def getFrames(self, tb=None):

        def _getitem_from_frame(f_locals, key, default=None):
            """
            f_locals is not guaranteed to have .get(), but it will always
            support __getitem__. Even if it doesnt, we return ``default``.
            """
            try:
                return f_locals[key]
            except Exception:
                return default

        if tb is None:
            ttype, msg, tb = sys.exc_info()

        if tb is None:
            frames = [(item[0], item[2]) for item in inspect.stack()]
        else:
            frames = []
            while tb:  # copied from sentry raven lib (BSD license)
                # support for __traceback_hide__ which is used by a few libraries
                # to hide internal frames.
                f_locals = getattr(tb.tb_frame, 'f_locals', {})
                if not _getitem_from_frame(f_locals, '__traceback_hide__'):
                    frames.append(
                        (tb.tb_frame, getattr(tb, 'tb_lineno', None)))
                tb = tb.tb_next
            frames.reverse()

        result = []
        ignore = ["ipython", "errorcondition", "loghandler", "errorhandling"]
        for frame, linenr in frames:
            name = frame.f_code.co_filename
            # print "RRR:%s %s"%(name,linenr)
            name = name.lower()
            toignore = False
            for check in ignore:
                if name.find(check) != -1:
                    toignore = True
            if not toignore:
                result.append((frame, linenr))

        return result

    def getErrorTraceKIS(self, tb=None):
        out = []
        nr = 1
        filename0 = "unknown"
        linenr0 = 0
        func0 = "unknown"
        frs = self.getFrames(tb=tb)
        frs.reverse()
        for f, linenr in frs:
            try:
                code, linenr2 = inspect.findsource(f)
            except Exception:
                continue
            start = max(linenr - 10, 0)
            stop = min(linenr + 4, len(code))
            code2 = "".join(code[start:stop])
            finfo = inspect.getframeinfo(f)
            linenr3 = linenr - start - 1
            out.append((finfo.filename, finfo.function, linenr3, code2, linenr))
            if nr == 1:
                filename0 = finfo.filename
                linenr0 = linenr
                func0 = finfo.function

        return out, filename0, linenr0, func0

    def escalateBugToDeveloper(self, errorConditionObject, tb=None):

        j.logger.enabled = False  # no need to further log, there is error

        tracefile = ""

        def findEditorLinux():
            apps = ["sublime_text", "geany", "gedit", "kate"]
            for app in apps:
                try:
                    if j.system.unix.checkApplicationInstalled(app):
                        editor = app
                        return editor
                except BaseException:
                    pass
            return "less"

        if False and j.application.interactive:

            editor = None
            if j.core.platformtype.myplatform.isLinux:
                #j.tools.console.echo("THIS ONLY WORKS WHEN GEDIT IS INSTALLED")
                editor = findEditorLinux()
            elif j.core.platformtype.myplatform.isWindows:
                editorPath = j.sal.fs.joinPaths(
                    j.dirs.JSBASEDIR, "apps", "wscite", "scite.exe")
                if j.sal.fs.exists(editorPath):
                    editor = editorPath
            tracefile = errorConditionObject.log2filesystem()
            # print "EDITOR FOUND:%s" % editor
            if editor:
                # print errorConditionObject.errormessagepublic
                if tb is None:
                    try:
                        res = j.tools.console.askString(
                            "\nAn error has occurred. Do you want do you want to do? (s=stop, c=continue, t=getTrace)")
                    except BaseException:                        # print "ERROR IN ASKSTRING TO SEE IF WE HAVE TO USE
                        # EDITOR"
                        res = "s"
                else:
                    try:
                        res = j.tools.console.askString(
                            "\nAn error has occurred. Do you want do you want to do? (s=stop, c=continue, t=getTrace, d=debug)")
                    except BaseException:                        # print "ERROR IN ASKSTRING TO SEE IF WE HAVE TO USE
                        # EDITOR"
                        res = "s"
                if res == "t":
                    cmd = "%s '%s'" % (editor, tracefile)
                    # print "EDITORCMD: %s" %cmd
                    if editor == "less":
                        j.sal.process.executeWithoutPipe(cmd, die=False)
                    else:
                        result, out, err = j.sal.process.execute(
                            cmd, die=False, showout=False)

                j.logger.clear()
                if res == "c":
                    return
                elif res == "d":
                    j.tools.console.echo(
                        "Starting pdb, exit by entering the command 'q'")
                    import pdb
                    pdb.post_mortem(tb)
                elif res == "s":
                    # print errorConditionObject
                    j.application.stop(1)
            else:
                # print errorConditionObject
                res = j.tools.console.askString(
                    "\nAn error has occurred. Do you want do you want to do? (s=stop, c=continue, d=debug)")
                j.logger.clear()
                if res == "c":
                    return
                elif res == "d":
                    j.tools.console.echo(
                        "Starting pdb, exit by entering the command 'q'")
                    import pdb
                    pdb.post_mortem()
                elif res == "s":
                    # print eobject
                    j.application.stop(1)

        else:
            # print "ERROR"
            # tracefile=eobject.log2filesystem()
            # print errorConditionObject
            #j.tools.console.echo( "Tracefile in %s" % tracefile)
            j.application.stop(1)

    def halt(self, msg, eco):
        if eco is not None:
            eco = eco.__dict__
        raise HaltException(msg, eco)

    def raiseWarning(self, message, msgpub="", tags="", level=4):
        """
        @param message is the error message which describes the state
        @param msgpub is message we want to show to endcustomers (can include a solution)
        """
        eco = j.errorhandler.getErrorConditionObject(
            ddict={}, msg=message, msgpub=msgpub, category='', level=level, type='WARNING')

        eco.process()
