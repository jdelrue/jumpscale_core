from Jumpscale import j

JSBASE = j.application.jsbase_get_class()
class EventHandler(JSBASE):

    def __init__(self):
        if not hasattr(self, '__jslocation__'):
            self.__jslocation__ = "j.core.events"
        JSBASE.__init__(self)

    def bug_critical(self, msg, source=""):
        """
        will die
        @param e is python error object when doing except
        """
        print("change your code to no longer use j.events...., but raise self.j.exceptions...")
        raise self.j.exceptions.JSBUG(msg, source=source)

    def opserror_critical(self, msg):
        """
        will die
        """
        print("change your code to no longer use j.events...., but raise self.j.exceptions...")
        raise self.j.exceptions.OPERATIONS(msg)

    def opserror_warning(self, msg, category=""):
        """
        will NOT die
        """
        self.j.errorhandler.raiseWarning(
            message=msg, msgpub=msgpub, tags='category:%s' % category, level=level)

    def inputerror_critical(self, msg, category="", msgpub=""):
        """
        will die
        """
        print("change your code to no longer use j.events...., but raise self.j.exceptions...")
        raise self.j.exceptions.Input(msg, tags='category:%s' %
                                 category, msgpub=msgpub)

    def inputerror_warning(self, msg, category="", msgpub="", level=5):
        """
        """
        self.j.errorhandler.raiseWarning(
            message=msg, msgpub=msgpub, tags='category:%s' % category, level=level)
