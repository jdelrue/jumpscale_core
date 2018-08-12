import os

if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:

    from .core.JSBase import JSBase
    from .tools.loader.JSLoader import JSLoader
    from .logging.LoggerFactory import LoggerFactory

    def add_dynamic_instance(parent, child, module, kls):
        #print ("adding", parent, child, module, kls)
        if not parent:
            parent = j
        else:
            parent = getattr(j, parent)
        if kls:
            parent._add_instance(child, "Jumpscale." + module, kls, basej=j)
            #print ("added", parent, child)
        else:
            walkfrom = j
            for subname in module.split('.'):
                walkfrom = getattr(walkfrom, subname)
            setattr(parent, child, walkfrom)

    # LoggerFactory isn't instantiated from JSBase so there has to
    # be a little bit of a dance to get it established and pointing
    # to the right global j.  JSBase now contains a property "j"
    # which is actually a singleton (global)
    bj = JSBase()

    j = bj.j._create_jsbase_instance('Jumpscale')
    j.j = j # sets up the global singleton

    DLoggerFactory = bj._jsbase(j, 'LoggerFactory', [LoggerFactory])
    l = DLoggerFactory()
    l.enabled = False
    l.filter = []  # default filter which captures all is *
    j.logging = l

    bases = {'j.core': 'Core',
             'j.tools': 'Tools',
             'j.sal': 'Sal',
             'j.data': 'Data',
    }

    aliases = [
        ('application', 'core.application'),
        ('data', 'data.cache'),
        ('core.state', 'tools.executorLocal.state'),
        ('core.dirs', 'dirs'),
    ]

    modules = [
        ('j.core',
            { 'dirs': ('Jumpscale/core/Dirs.py',
                    'Dirs', []),
            }),
        ('j.data',
            {'types': ('Jumpscale/data/types/Types.py', 'Types', []),
             'text': ('Jumpscale/data/text/Text.py', 'Text', []),
             'datacache': ('Jumpscale/data/cache/Cache.py', 'Cache', []),
            }),
        ('j.sal',
            { 'fs': ('Jumpscale/fs/SystemFS.py', 'SystemFS', []),
              'process': ('Jumpscale/sal/process/SystemProcess.py',
                            'SystemProcess', [])
            }),
        ('j.core',
            { 'application': ('Jumpscale/core/Application.py',
                    'Application', []),
              'platformtype': ('Jumpscale/core/PlatformTypes.py',
                    'PlatformTypes', []),
            }),
        ('j.tools',
            { 'executorLocal': ('Jumpscale/tools/executor/ExecutorLocal.py',
                    'ExecutorLocal', []),
            })
        ]
    for (parent, child, module, kls) in [
        ('', 'core', 'core', 'Core'),
        ('', 'tools', 'tools', 'Tools'),
        ('', 'sal', 'sal', 'Sal'),
        ('', 'data', 'data', 'Data'),
        ('data', 'types', 'data.types.Types', 'Types'),
        ('data', 'text', 'data.text.Text', 'Text'),
        ('sal', 'fs', 'fs.SystemFS', 'SystemFS'),
        ('core', 'application', 'core.Application', 'Application'),
        ('data', 'datacache', 'data.cache.Cache', 'Cache'),
        ('tools', 'executorLocal', 'tools.executor.ExecutorLocal',
                                    'ExecutorLocal'),
        ('', 'dirs', 'core.Dirs', 'Dirs'),
        ('core', 'platformtype', 'core.PlatformTypes', 'PlatformTypes'),
        ('sal', 'process', 'sal.process.SystemProcess', 'SystemProcess'),
        ('', 'application', 'core.application', None),
        ('', 'cache', 'data.cache', None),
        ('core', 'state', 'tools.executorLocal.state', None),
        ('core', 'dirs', 'dirs', None),
        ]:
        pass
        add_dynamic_instance(parent, child, module, kls)

    DJSLoader = j._jsbase(j, 'JSLoader', [JSLoader])
    dl = DJSLoader()
    #j = dl._dynamic_generate(j, modules, bases, aliases) 
    j = dl.dynamic_generate(basej=j) 
    j.logging.init()  # will reconfigure the logging to use the config file
    j.tools.executorLocal.env_check_init()

