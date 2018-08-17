class Sal(object):
    """ System Abstraction Layer

        An API for accessing the LOCAL system.
    """
    __jslocation__ = 'j.sal'
    __jsdeps__ = {'fs' : ('Jumpscale.fs.SystemFS', 'SystemFS'),
                  'process': ('Jumpscale.sal.process.SystemProcess',
                              'SystemProcess'),
        }

