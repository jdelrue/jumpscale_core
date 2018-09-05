[![Build Status](https://travis-ci.org/threefoldtech/jumpscale_core.svg?branch=development)](https://travis-ci.org/threefoldtech/jumpscale_core)

# Jumpscale

Jumpscale is a cloud automation product and a branch from what used to be 
Pylabs. About 9 years ago Pylabs was the basis of a cloud automation product 
which was acquired by SUN Microsystems from Q-Layer. In the mean time we are 
4 versions further and we have rebranded it to Jumpscale.

- [Jumpscale](#jumpscale)
  - [About Jumpscale Core](#about-jumpscale-core)
  - [Installing Jumpscale Core (NEW, need to test!!!)](#installing-jumpscale-core-new-need-to-test)
    - [install](#install)
    - [Install using pip3](#install-using-pip3)
  - [Usage](#usage)
  - [Tutorials](#tutorials)


2018aug: lots of changes have recently being done see [changes.md](changes.md)

## About Jumpscale Core

The core module provides the bare framework into which other modules of Jumpscale plug into.

Of these provided tools are, most notably:

* [Config Manager](docs/config/configmanager.md)
  The config manager is a secure way to manage configuration instances.
  Anything saved to the file system is NACL encrypted and only decrypted on
  the fly when accessed.

- [Executors](docs/Internals/Executors.md)
  Jumpscale comes with its own executors that abstract working locally or
  remotely.  Of these executors:

  * SSH Executor (for remote execution)
  * Local Executor (for local execution)
  * Docker Executor (for executing on dockers)

* [JSLoader](docs/JSLoader/JSLoader.md)
* [Node Manager]()

## Installing Jumpscale Core (NEW, need to test!!!)

_tested on osx, ubuntu 16.04, ubuntu 17.04,
debian/stretch, debian/testing (2018aug)
(will upgrade brew as part of the process on OSX)_

### install

```bash
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/development/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
```

```bash
#to define branch:
export JUMPSCALEBRANCH="development"
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
```

to follow the install

```bash
tail -f /tmp/jumpscale_install.log
```

to test that it worked:

```bash
js_shell
```

to run the test suite:

* apt-get install python3-pytest-cov python3-nose
* pip3 install parameterized (annoying: python-nose-parameterized incompatible)
* python3 setup.py test

Note that it is a really, REALLY good idea to set up a chroot for running
the unit tests, as they tend to mess with things like /etc/passwd, /etc/group,
add stuff to ~/.profile and also have to be run as root

### Install (and upgrade as opposed to blowing everything away)

This option can be used on debian to carry out either an install or
an upgrade of an existing install.  It's not hugely "intelligent": it
simply runs through a laaaarge series of "apt-get installs" along-side an
additional series of git pull and python setup.py running.

When run as an "upgrader" it specifically does not change the git branches
in each jumpscale repository, nor does it "blow away" the pre-existing
repository (it does a "git pull" instead). In this way the exact same
script can be used for ongoing development in whatever branch happens to be
checked out in each, at the time.

Either:

Obtain the dev-install-or-upgrade.sh
script:

```
.../src$ curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/dev-install-or-upgrade.sh?$RANDOM > ./dev-install-or-upgrade.sh
.../src$ sudo bash
.../src# ./dev-install-or-upgrade.sh

```

Or:

Making sure that you are root in the directory BELOW jumpscale\_core
(where all source code is), run the script.

```
.../src/jumpscale_core$ sudo bash
.../src/jumpscale_core# cd ..
.../src# ./jumpscale_core/dev-install-or-upgrade.sh
```

Note that if ever the actual install script is changed (new dependencies
added), obviously "git pull" in jumpscale\_core obviously would have to
be carried out by hand, first (or the script run twice).

### Install using pip3

```
mkdir -p /opt/code/github/threefoldtech/jumpscale_core
pip3 install -e git+https://github.com/threefoldtech/jumpscale_core@development#egg=core --src /opt/code/github/threefoldtech/jumpscale_core
```

## Usage

* The jsshell
  in your terminal, type `js_shell`

- In Python

  ```bash
  python3 -c 'from jumpscale import j;print(j.application.getMemoryUsage())'
  ```

  the default mem usage < 23 MB and lazy loading of the modules.

## Tutorials
How to run a sandbox of jumpscale and python
[Check Documentation](docs/howto/sandbox_python_zeroos_container.md)
<!TODO>
