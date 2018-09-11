from Jumpscale import j # J due to recursive import in ConfigManager
import os

TEMPLATE = """
fullname = ""
email = ""
login_name = ""
"""

#FormBuilderBaseClass = j.tools.formbuilder.baseclass_get()

JSConfigBase = j.tools.configmanager.JSBaseClassConfig


class MyConfig(JSConfigBase):
    """
    """

    def __init__(self, data=None):
        if not hasattr(self, '__jslocation__'):
            self.__jslocation__ = "j.tools.myconfig"
        if data is None:
            data = {}
        JSConfigBase.__init__(self, instance="main", data=data,
                              template=TEMPLATE, interactive=True)
