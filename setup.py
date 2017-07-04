from setuptools import setup
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop
import os


def _post_install(libname, libpath):
    from JumpScale9 import j  # here its still the boostrap JumpScale9

    # add this plugin to the config
    c = j.core.state.configGet('plugins', defval={})
    c[libname] = libpath
    j.core.state.configSet('plugins', c)

    # SHOULD NOT DO THIS, std python install needs to work
    # j.tools.jsloader.generateJumpscalePlugins()
    # j.tools.jsloader.copyPyLibs()

    # if j.tools.jsloader.gigDir is not None:
    #     install_requires = [
    #         'psutil',
    #         # 'numpy',
    #         # 'pyblake2',
    #         'watchdog',
    #         # 'cython',
    #         # 'asyncssh>=1.10.1'
    #     ]
    #     print("* installing additional pip's, this will take some minutes.")
    #     for item in install_requires:
    #         j.do.execute("pip3 install %s 2>&1 > /tmp/install.log" % item)

    j.tools.jsloader.generateJumpscalePlugins()


class install(_install):

    def run(self):
        _install.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), libname)
        self.execute(_post_install, (libname, libpath), msg="Running post install task")


class develop(_develop):

    def run(self):
        _develop.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), libname)
        self.execute(_post_install, (libname, libpath), msg="Running post install task")


setup(
    name='JumpScale9',
    version='9.0.3',
    description='Automation framework for cloud workloads',
    url='https://github.com/Jumpscale/core9',
    author='GreenItGlobe',
    author_email='info@gig.tech',
    license='Apache',
    packages=['JumpScale9'],
    install_requires=[
        'GitPython>=2.1.3',
        'click>=6.7',
        'colored_traceback',
        'colorlog>=2.10.0',
        'httplib2>=0.10.3',
        'ipython>=6.0.0',
        'libtmux>=0.7.1',
        'netaddr>=0.7.19',
        'path.py>=10.3.1',
        'pystache>=0.5.4',
        'python-dateutil>=2.6.0',
        'pytoml>=0.1.12',
        'redis>=2.10.5',
        'requests>=2.13.0',
        'future>=0.16.0',
        'msgpack-python',
        'psutil',
        'watchdog',
    ],
    cmdclass={
        'install': install,
        'develop': develop,
        'developement': develop
    },
    scripts=[
        'cmds/js9',
        'cmds/js9_code',
        'cmds/js9_docker',
        'cmds/js9_docs',
    ],
)
