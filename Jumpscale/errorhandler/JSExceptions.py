import pssh.exceptions
import copy
import unicodedata
from Jumpscale import j
import sys

LEVELMAP = {1: 'CRITICAL', 2: 'WARNING', 3: 'INFO', 4: 'DEBUG'}

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
    #__nojslocation__ = 'j.errorhandling.exceptions'
    def __init__(self):
        self._add_late_init(self.register_exceptions)

    def register_exceptions(self):
        exceptions = [_HaltException, _RuntimeError, _Input,
            _NotImplemented, _BUG, _JSBUG, _OPERATIONS,
            _IOError, _NotFound, _Timeout,
            _SSHTimeout,
            ]
        for e in exceptions:
            ename = e.__name__[1:]
            ekls = self._jsbase(ename, ["Jumpscale.errorhandling.%s" % e])
            globals()[ename] = ekls
            setattr(self, ename, ekls)



class BaseJSException(Exception, JSBASE):

    def __init__(self, message="", level=1, cat="", msgpub="",
                 # XXX ISSUE #81 - WARNING: it is ESSENTIAL
                 # that these parameters REMAIN HERE until
                 # all code including third parties have had
                 # a chance to upgrade to the new API.
                 # use of any of these parameters will
                 # result in an error being logged.
                 source=None, action=None, eco=None, tags=None):

        if source is not None or \
           action is not None or \
           eco is not None or \
           tags is not None:
            self.logger.error("Exception called with new API arguments. "
                              "Please update code to new exception API")

        JSBASE.__init__(self)
        if not self.j.data.types.int.check(level):
            level=1
        super().__init__(message)
        self.message = message
        self.message_pub = msgpub
        self.level = level
        if level not in LEVELMAP:
            raise RuntimeError("level needs to be 1-4")
        self.cat = cat                      #is a dot notation category, to make simple no more tags
        self.trace_do = False
        self._trace = ""                     #info to find back where it was

    @property
    def trace(self):
        return self._trace

    @property
    def type(self):
        return self.j.data.text.strip_to_ascii_dense(str(self.__class__))


    @property
    def str_1_line(self):
        """
        1 line representation of error

        """
        msg = ""
        if self.level > 1:
            msg += "level:%s " % self.level
        if self.type != "":
            msg += "type:%s " % self.type
        # if self._tags_add != "":
        #     msg += " %s " % self._tags_add
        return msg.strip()


    def __str__(self):
        if self.cat is not "":
            out = "ERROR: %s ((%s)\n" % (self.message, self.cat)
        else:
            out = "ERROR: %s\n" % (self.message)
        if self._trace is not "":
            self.j.errorhandler._trace_print(self._trace)
            return ""
        else:
            return out

    __repr__ = __str__



    def trace_print(self):
        self.j.core.errorhandler._trace_print(self._trace)



class HaltException(BaseJSException):
    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class RuntimeError(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class Input(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class NotImplemented(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class BUG(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class JSBUG(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class OPERATIONS(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = False


class IOError(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True



class NotFound(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True


class Timeout(BaseJSException):

    def __init__(self, message="", level=1, cat="", msgpub="",
                       source=None, action=None, eco=None, tags=None):
        super().__init__(message=message,level=level,cat=cat,msgpub=msgpub,
                        source=source, action=action, eco=eco, tags=tags)
        self.trace_do = True

SSHTimeout = pssh.exceptions.Timeout
