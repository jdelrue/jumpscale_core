import os

if os.environ.get('JUMPSCALEMODE') == 'TESTING':
    from unittest.mock import MagicMock

    j = MagicMock()

else:

    from .core.JSBase import JSBase, global_j
    from .tools.jsloader.JSLoader import bootstrap_j

    # slightly hacky (invisible) way to add a -c/--config option
    # which (because of add_help=False and del on the help action)
    # doesn't cause an exit (right here) if ANOTHER argparse happens
    # to be called (later) with more arguments.

    # hacking things in here avoids the need to have to add "-c" to
    # absolutely every single one of the core9/cmd/js_* commands.
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-c', '--config', default=None,
                        help="Config Directory Name")
    del parser._registries['action']['help'] # remove help action (stops exit)
    options, args = parser.parse_known_args()

    if global_j is None:
        j = bootstrap_j(config_dir=options.config)
        j.logging.init() # initialise logging here to stop recursive import
        #j.data.serializer = j.data.serializers # YUK! SPEW, HURL....
    else:
        j = global_j
