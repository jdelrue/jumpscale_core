from Jumpscale import j
import pssh.exceptions

JSBASE = j.application.jsbase_get_class()

class ExceptionsFactory(object):
    """ create a series of dynamic JSBase-patched Exceptions
        that are then added to both the module (via globals())
        and also to the ExceptionsFactory (using setattr),
        which in turn allows them to be accessed via
        j.errorhandling.exceptions.

        TODO: work out how to drop them into the j.exceptions namespace,
        without having to move this module
    """
    def __init__(self):
        #self.__nojslocation__ = 'j.errorhandling.exceptions'
        self.add_late_init(self.register_exceptions)

    def register_exceptions(self):
        exceptions = [_HaltException, _RuntimeError, _Input,
            _NotImplemented, _BUG, _JSBUG, _OPERATIONS,
            _IOError, _AYSNotFound, _NotFound, _Timeout,
            _SSHTimeout,
            ]
        for e in exceptions:
            ename = e.__name__[1:]
            ekls = self._jsbase(self.j, ename, [e])
            globals()[ename] = ekls
            setattr(self, ename, ekls)


class BaseJSException(Exception, JSBase):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        JSBase.__init__(self)
        if self.j.data.types.string.check(level):
            level = 1
            tags = "cat:%s" % level
        super().__init__(message)
        self.j.errorhandler.setExceptHook()
        self.message = message
        self.level = level
        self.source = source
        self.type = ""
        self.actionkey = actionkey
        self.eco = eco
        self.codetrace = True
        self._tags_add = tags
        self.msgpub = msgpub

    @property
    def tags(self):
        msg = ""
        if self.level != 1:
            msg += "level:%s " % self.level
        if self.source != "":
            msg += "source:%s " % self.source
        if self.type != "":
            msg += "type:%s " % self.type
        if self.actionkey != "":
            msg += "actionkey:%s " % self.actionkey
        if self._tags_add != "":
            msg += " %s " % self._tags_add
        return msg.strip()

    @property
    def msg(self):
        return "%s ((%s))" % (self.message, self.tags)

    def __str__(self):
        return "ERROR: %s" % self.msg

    __repr__ = __str__


class HaltException(BaseJSException):
    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "halt.error"


class RuntimeError(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "runtime.error"
        self.codetrace = True


class Input(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "input.error"
        self.codetrace = True


class NotImplemented(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "notimplemented"
        self.codetrace = True


class BUG(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "bug.js"
        self.codetrace = True


class JSBUG(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "bug.js"
        self.codetrace = True


class OPERATIONS(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "operations"
        self.codetrace = True


class IOError(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "ioerror"
        self.codetrace = False


class AYSNotFound(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "ays.notfound"
        self.codetrace = False


class NotFound(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "notfound"
        self.codetrace = False


class Timeout(BaseJSException):

    def __init__(self, message="", level=1, source="", actionkey="", eco=None, tags="", msgpub=""):
        super().__init__(message, level, source, actionkey, eco, tags, msgpub)
        self.type = "timeout"
        self.codetrace = False

SSHTimeout = pssh.exceptions.Timeout
