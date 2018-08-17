class Data(object):
    __jslocation__ = 'j.data'
    __jsdeps__ = {
       'nacl': ('Jumpscale.data.nacl.NACLFactory', 'NACLFactory'),
       'datacache': ('Jumpscale.data.cache.Cache', 'Cache'),
       'types': ('Jumpscale.data.types.Types', 'Types'),
       'text': ('Jumpscale.data.text.Text', 'Text'),
       'serializers': ('Jumpscale.data.serializers.SerializersFactory',
                                'SerializersFactory'),
       'idgenerator': ('Jumpscale.data.idgenerator.IDGenerator', 'IDGenerator'),
                }
