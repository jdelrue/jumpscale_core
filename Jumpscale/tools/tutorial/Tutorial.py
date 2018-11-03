
from Jumpscale import j
JSBASE = j.application.JSBaseClass


class Tutorial(JSBASE):
    """
    """

    def __init__(self):
        self.__jslocation__ = "j.tools.tutorial"
        JSBASE.__init__(self)


    def cache(self):
        """
        js_shell 'j.tools.tutorial.cache()'

        :return: result the name given

        """
        assert self._example_run("tutorials/cache/example",name="aname") == "aname"
