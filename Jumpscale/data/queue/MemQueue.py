
from Jumpscale import j

import time

JSBASE = j.application.JSBaseClass
class MemQueueFactory(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
    def get(self):
        """
        """
        return MemQueue()


class MemQueue(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)
        self.data=[]
    
    def put(self,data):
        self.data.append(data)

    def __str__(self):
        return self.data

    __repr__ = __str__
