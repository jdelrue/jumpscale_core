class Tools(object):
    __jslocation__ = 'j.tools'
    __jsdeps__ = {
        'executor': 'ExecutorFactory',
        'executorLocal': ('Jumpscale.tools.executor.ExecutorLocal',
                          'ExecutorLocal'),
        'loader': ('Jumpscale.tools.loader.JSLoader', 'JSLoader'),
        'configmanager': ('Jumpscale.tools.configmanager.ConfigManager',
                            'ConfigFactory'),
        'formbuilder': ('Jumpscale.tools.formbuilder.FormBuilder',
                            'FormBuilderFactory'),
    }
