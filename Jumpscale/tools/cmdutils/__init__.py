from Jumpscale import j

import argparse
import sys


class ArgumentParser(argparse.ArgumentParser):

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        if j.application.state == "RUNNING":
            j.application.stop(status)
        else:
            sys.exit(status)


def processLogin(parser):

    parser.add_argument("-l", '--login', help='login for grid, if not specified defaults to root')
    parser.add_argument("-p", '--passwd', help='passwd for grid')
    parser.add_argument(
        "-a", '--addr', help='ip addr of master, if not specified will be the one as specified in local config')

    opts = parser.parse_args()

    if opts.login is None:
        opts.login = "root"

    # if opts.passwd==None and opts.login=="root":
    #     if j.application.config.exists("grid.master.superadminpasswd"):
    #         opts.passwd=j.application.config.get("grid.master.superadminpasswd")
    #     else:
    #         opts.passwd=j.tools.console.askString("please provide superadmin passwd for the grid.")

    # if opts.addr==None:
    #     opts.addr=j.application.config.get("grid.master.ip")

    return opts


def getProcess(parser=None):
    parser = parser or ArgumentParser()
    parser.add_argument('-d', '--domain', help='Process domain name')
    parser.add_argument('-n', '--name', help='Process name')
    return parser.parse_args()
