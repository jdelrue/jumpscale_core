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
    # which is actually a singleton (global), and LoggerFactory is
    # the ONLY class that's not fully aware of it... for now.
    bj = JSBase()

    l = LoggerFactory()
    l.enabled = False
    l.filter = []  # default filter which captures all is *
    j = bj.j._create_jsbase_instance('Jumpscale')
    j.j = j # sets up the global singleton
    j.logging = l
    l.j = j # ... which isn't aware of the JSBase j singleton sigh...

    DLoggerFactory = bj._jsbase(j, 'LoggerFactory', [LoggerFactory])
    l = DLoggerFactory()
    l.enabled = False
    l.filter = []  # default filter which captures all is *
    j.logging = l

    for (parent, child, module, kls) in [
        ('', 'core', 'core', 'Core'),
        ('', 'tools', 'tools', 'Tools'),
        ('', 'sal', 'sal', 'Sal'),
        ('', 'data', 'data', 'Data'),
        ('data', 'types', 'data.types.Types', 'Types'),
        ('data', 'text', 'data.text.Text', 'Text'),
        ('', 'sal', 'sal', 'Sal'),
        ('sal', 'fs', 'fs.SystemFS', 'SystemFS'),
        ('core', 'application', 'core.Application', 'Application'),
        ('', 'application', 'core.application', None),
        ('data', 'datacache', 'data.cache.Cache', 'Cache'),
        ('', 'cache', 'data.cache', None),
        ('tools', 'executorLocal', 'tools.executor.ExecutorLocal',
                                    'ExecutorLocal'),
        ('core', 'state', 'tools.executorLocal.state', None),
        ('', 'dirs', 'core.Dirs', 'Dirs'),
        ('core', 'dirs', 'dirs', None),
        ('core', 'platformtype', 'core.PlatformTypes', 'PlatformTypes'),
        ('sal', 'process', 'sal.process.SystemProcess', 'SystemProcess'),
        ('tools', 'jsloader', 'tools.loader.JSLoader', 'JSLoader'),
        ]:
        add_dynamic_instance(parent, child, module, kls)

    DJSLoader = j._jsbase(j, 'JSLoader', [JSLoader])
    dl = DJSLoader()
    j = dl.dynamic_generate(basej=j) 
    j.logging.init()  # will reconfigure the logging to use the config file
    j.tools.executorLocal.env_check_init()

