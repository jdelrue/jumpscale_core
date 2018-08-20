import os

if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:

    from .core.JSBase import JSBase
    from .tools.loader.JSLoader import bootstrap_j

    bj = JSBase() # start with a dummy 
    j = bj.j._create_jsbase_instance('Jumpscale')
    j = bootstrap_j(j)
