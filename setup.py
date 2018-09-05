import os

# extremely useful for investigating where things might go wrong
# (e.g. in unit tests)
if os.environ.get("PYSTUCK", None):
    import gevent.monkey
    gevent.monkey.patch_all()
    import pystuck
    pystuck.run_server()

from setuptools import setup, find_packages
#from distutils.core import setup <- needed for dynamic bootstrap (TODO)
from distutils.sysconfig import get_python_lib
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop


def _post_install(libname, libpath):
    from Jumpscale import j  # here its still the boostrap Jumpscale

    # remove leftovers
    if not "PBASE" in os.environ:
        #should only be done when not in build dir
        for item in j.sal.fs.find("/usr/local/bin/", fileregex="js_*"):
            j.sal.fs.remove("/usr/local/bin/%s" % item)

    # re-generates the Jumpscale core plugin json (similar to .pth)
    j.tools.jsloader.generate_json('Jumpscale')


class install(_install):

    def run(self):
        _install.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            libname)
        self.execute(_post_install, (libname, libpath),
                     msg="Running post install task")


class develop(_develop):

    def run(self):
        _develop.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            libname)
        self.execute(_post_install, (libname, libpath),
                     msg="Running post install task")


long_description = ""
try:
    from pypandoc import convert
    long_description = convert('README.md', 'rst')
except ImportError:
    long_description = ""

# minimum list of packages needed to get Jumpscale.__init__.py
# operational for dynamic bootstrap, which isn't working yet...
packages = ['Jumpscale',
            'Jumpscale.core',
            'Jumpscale.data',
            'Jumpscale.data.types',
            'Jumpscale.data.text',
            'Jumpscale.tools',
            'Jumpscale.tools.jsloader',
            'Jumpscale.tools.configmanager',
            'Jumpscale.fs',
            'Jumpscale.sal',
            'Jumpscale.sal.process',
            'Jumpscale.errorhandling',
            'Jumpscale.tools.executor',
            'Jumpscale.data.cache',
            'Jumpscale.logging']
packages = find_packages() # .... so just install everything for now

setup(
    name='Jumpscale',
    version='9.4.0-rc4',
    description='Automation framework for cloud workloads',
    long_description=long_description,
    url='https://github.com/threefoldtech/jumpscale_core',
    author='ThreeFoldTech',
    author_email='info@threefold.tech',
    license='Apache',
    packages=packages,
    py_modules=['jumpscale'],

    # IF YOU CHANGE ANYTHING HERE, LET DESPIEGK NOW (DO NOT INSTALL ANYTHING
    # WHICH NEEDS TO COMPILE)
    install_requires=[
        'GitPython>=2.1.1',
        'click>=6.6',
        'colored_traceback',
        'colorlog>=2.10.0',
        'httplib2>=0.9.2',
        'ipython>=5.1.0',
        'libtmux>=0.7.1',
        'netaddr>=0.7.18',
        'path.py>=10.3.1',
        'pystache>=0.5.4',
        'python-dateutil>=2.5.3',
        'pytoml>=0.1.2',
        'toml',
        'redis>=2.10.5',
        'requests>=2.12.0',
        'future>=0.15.0',
        'watchdog',
        'msgpack-python',
        'npyscreen',
        'pyyaml',
        'pyserial>=3.0'
        'docker>=3',
        'fakeredis',
        'ssh2-python',
        'parallel_ssh>=1.4.0',
        'psutil>=5.0.1',
        'Unidecode>=0.04.19',

    ],
    cmdclass={
        'install': install,
        'develop': develop,
        'developement': develop
    },
    scripts=[
        'cmds/js_shell',
        'cmds/js_code',
        'cmds/js_docker',
        'cmds/js_doc',
    ],
)
