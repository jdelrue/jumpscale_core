import os

if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:

    from .core.JSBase import JSBase
    from .tools.loader.JSLoader import bootstrap_j

    # TODO.  trying to establish how to pass these in to JSLoader,
    # as the code in bootstrap_j is near-identical to that used
    # in dynamic_generate.
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

    bj = JSBase() # start with a dummy 
    j = bj.j._create_jsbase_instance('Jumpscale')
    j = bootstrap_j(j)
