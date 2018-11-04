from Jumpscale import j

order = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
JSBASE = j.application.JSBaseClass


class Sizes(JSBASE):
    _BASE = 1000.

    def __init__(self):
        self.__jslocation__ = "j.data_units.sizes"
        JSBASE.__init__(self)

    def toSize(self, value, input='', output='K'):
        """
        Convert value in other measurement
        """
        input = order.index(input)
        output = order.index(output)
        factor = input - output
        return value * (self._BASE ** factor)

    def converToBestUnit(self, value, input=''):
        divider = len(str(int(self._BASE))) - 1
        output = (len(str(value)) - 2) / divider
        output += order.index(input)
        if output > len(order):
            output = len(order) - 1
        elif output < 0:
            output = 0
        output = order[int(output)]
        return self.toSize(value, input, output), output


class Bytes(Sizes):
    _BASE = 1024.

    def __init__(self):
        self.__jslocation__ = "j.data_units.bytes"
        Sizes.__init__(self)
