# BOOTSTRAP CODE

import os
import time
import argparse
from importlib import util

if __name__ == '__main__':
    if "JUMPSCALEBRANCH" in os.environ:
        branch = os.environ["JUMPSCALEBRANCH"]
    else:
        branch = "master"

    if "TMPDIR" not in os.environ:
        os.environ["TMPDIR"] = "/tmp"
        # raise RuntimeError("TMPDIR should be there")

    tmpdir = os.environ["TMPDIR"]

    print("bootstrap installtools in dir %s and use branch:'%s'" %
          (tmpdir, branch))

    # GET THE MAIN INSTALL TOOLS SCRIPT

    pathcheck = "%s/InstallTools.py" % os.path.abspath(os.curdir)
    if os.path.exists(pathcheck):
        path = pathcheck
    else:
        path = "%s/InstallTools.py" % tmpdir

    if not os.path.exists(path):
        raise RuntimeError("Cannot find:%s" % path)

    os.chdir(tmpdir)

    spec = util.spec_from_file_location("InstallTools", path)

    InstallTools = spec.loader.load_module()

    do = InstallTools.do

    # look at methods in https://github.com/threefoldtech/jumpscale_/jumpscale_core/blob/master/install/InstallTools.py to see what can be used
    # there are some easy methods to allow git manipulation, copy of files,
    # execution of items

    # there are many more functions available in jumpscale

    # FROM now on there is a do. variable which has many features, please
    # investigate

    print("install jumpscale")
    do.installer.prepare()
    do.installer.installJS()

    from Jumpscale import j
