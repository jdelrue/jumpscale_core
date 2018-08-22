#!/bin/sh

# for debian developer use: can be run WITHOUT having to completely destroy
# an existing installation.  will carry out upgrades (including of
# dependencies).
#
# dependencies needed for running the unit tests (python3 setup.py test)
# are also brought in
#
# so this script basically pre-installs as much as possible so that
# pip, which is... um... a good way to bypass distro-released python
# packages shall we say... doesn't get a word in edgeways unless
# absolutely, absolutely necessary.  and even then it's dodgy.
#
# the only dodgy one which absolutely had to be brought in was
# pycapnp, which had to be forced into using a specific version
# of libcapnp... which *should* still have worked... but doesn't
# build.  yay.
#
# the script can be re-run without needing to "blow away" pre-existing
# dependencies and work.  git repositories that were previously downloaded
# successfully will have a "git pull" done in them, instead.


# hack to stop jumpscale_lib from force-installing electrum
monkey_patch_path_for_overloading_pip3() {
	mkdir -p hack_bin
	PATH=`pwd`/hack_bin:$PATH
	export $PATH
	cat <<EOF >>hack_bin/pip3
#!/bin/sh
echo pip3 dummy, stops jumpscale_lib from running forced install of electrum
EOF
	chmod a+x hack_bin/pip3
}

# checks out / pulls a specific version of a git branch
# runs python install
python_git_repo_v() {
 
    echo "installing" into $2, $1
    curr_dir=`pwd`
    if [ ! -d $2 ]; then
        git clone $1
    else
        cd $2
        git pull
        cd $curr_dir
    fi
    cd $2
    git checkout $3
    python3 setup.py install
    cd $curr_dir
}

# checks out / pulls the default version of a git branch
# runs python install
python_git_repo() {
 
    echo "installing" into $2, $1
    curr_dir=`pwd`
    if [ ! -d $2 ]; then
        git clone $1
    else
        cd $2
        git pull
        cd $curr_dir
    fi
    cd $2
    python3 setup.py install $3
    cd $curr_dir
}

# checks out / pulls the default version of a git branch
# runs python develop
python_git_dev() {
 
    echo "installing" into $2, $1
    curr_dir=`pwd`
    if [ ! -d $2 ]; then
        git clone $1
    else
        cd $2
        git pull
        cd $curr_dir
    fi
    cd $2
    python3 setup.py develop $3
    cd $curr_dir
}

mk_hack_symlink () {
    # jaezuss, this is truly dreadful, the way that installs fail if the
    # symlinks don't exist...

    TFT=/opt/code/github/threefoldtech
    mkdir -p $TFT
    if [ ! -L "$TFT/$1" ]; then
        ln -s `pwd`/$1 $TFT
    fi
}

# looots of python package dependencies...
apt-get update
apt-get install -y build-essential git python3
apt-get install -y python3-setuptools
apt-get install -y python3-colorlog
apt-get install -y python3-psutil
apt-get install -y python3-pytoml
apt-get install -y python3-pystache
apt-get install -y lsb_release
apt-get install -y sudo
apt-get install -y python3-redis python3-fakeredis
apt-get install -y build-essential
apt-get install -y python3-dev
apt-get install -y libssh-dev
apt-get install -y libssh2-dev
apt-get install -y libsssh2-1-dev
apt-get install -y libssh2-1-dev
apt-get install -y python-libssh2
apt-get install -y python3-paramiko
apt-get install -y python-libssh2
apt-get install -y python3-gevent
apt-get install -y python3-pygments
apt-get install -y python3-libtmux
apt-get install -y python3-rsa
apt-get install -y python3-future
apt-get install -y python3-click
apt-get install -y python3-flask
apt-get install -y python3-prometheus-client
apt-get install -y python3-netifaces
apt-get install -y python3-jsonschema
apt-get install -y python3-yaml
apt-get install -y python3-requests
apt-get install -y python3-msgpack
apt-get install -y python3-git
apt-get install -y python3-netaddr
apt-get install -y python3-github
apt-get install -y cython3
apt-get install -y libcapnp-dev
apt-get install -y python3-unidecode
apt-get install -y lsb-release
#apt-get install -y pssh

# for testing (running unit tests)
apt-get install -y python3-serial
apt-get install -y python3-msgpack
apt-get install -y python3-watchdog
apt-get install -y python3-future
apt-get install -y python3-pytoml
apt-get install -y python3-toml
apt-get install -y python3-dateutil
apt-get install -y python3-ipython
apt-get install -y python3-httplib2
apt-get install -y python3-jedi
apt-get install -y python3-pytest
apt-get install -y python3-blosc
apt-get install -y python3-snappy
apt-get install -y python3-asyncssh
apt-get install -y python3-numpy
apt-get install -y python3-docker
apt-get install -y python3-parameterized
apt-get install -y python3-influxdb
apt-get install -y python3-kubernetes
apt-get install -y python3-pymongo
apt-get install -y python3-pypandoc
apt-get install -y python3-psycopg2
apt-get install -y python3-html2text
apt-get install -y python3-libvirt
apt-get install -y python3-aioredis
apt-get install -y python3-flask-login
apt-get install -y python3-flask-sqlalchemy
apt-get install -y python3-brotli
apt-get install -y python3-peewee
apt-get install -y python3-nacl
apt-get install -y librocksdb-dev
apt-get install -y libsnappy-dev
apt-get install -y libbz2-dev
apt-get install -y liblz4-dev
apt-get install -y tarantool
apt-get install -y libsecp256k1-0


python_git_repo https://github.com/g8os/g8stor-client-pypi.git \
						g8stor-client-pypi
python_git_repo https://github.com/eoranged/rq-dashboard.git rq-dashboard
python_git_repo https://github.com/heroku-python/flask-sockets.git flask-sockets
python_git_repo https://github.com/jgelens/gevent-websocket.git gevent-websocket
python_git_repo https://github.com/kragniz/python-etcd3.git python-etcd3
python_git_repo https://github.com/tehmaze/ipcalc.git ipcalc
python_git_repo https://github.com/dchest/pyblake2.git pyblake2
python_git_repo https://github.com/warner/python-ed25519.git python-ed25519
python_git_repo https://github.com/sendgrid/sendgrid-python.git sendgrid-python
python_git_repo https://github.com/ovh/python-ovh.git python-ovh
python_git_repo https://github.com/intercom/python-intercom.git python-intercom
python_git_repo https://github.com/twmht/python-rocksdb.git python-rocksdb
python_git_repo https://github.com/patx/pickledb.git pickledb
python_git_repo https://github.com/fancycode/pylzma.git pylzma
python_git_repo https://github.com/tarantool/tarantool-python.git \
					tarantool-python


python_git_repo https://github.com/packethost/packet-python.git \
					packet-python

# lots of python packages that aren't packaged in debian...
python_git_repo https://github.com/capnproto/pycapnp.git pycapnp \
                                        --force-bundled-libcapnp

python_git_repo https://github.com/ParallelSSH/parallel-ssh parallel-ssh
python_git_repo https://github.com/staticshock/colored-traceback.py \
                                               colored-traceback.py

python_git_repo https://github.com/tinyerp/erppeek.git erppeek
python_git_repo https://github.com/npcole/npyscreen.git npyscreen
python_git_repo https://github.com/jaraco/path.py.git path.py
python_git_repo https://github.com/mpdavis/python-jose.git python-jose
python_git_repo https://github.com/trezor/python-mnemonic.git python-mnemonic
python_git_repo https://github.com/lagerfeuer/cryptocompare.git \
						cryptocompare

# honestly genuinely cannot be bothered to get all the dependencies for this
python_git_repo https://github.com/google/google-api-python-client.git \
						google-api-python-client

# electrum 3.2.2 is a critical dependency of jumpscale_lib ??? moo???
apt-get install -y python3-qrcode
apt-get install -y python3-pyaes
apt-get install -y python3-protobuf
apt-get install -y python3-google-apputils
apt-get install -y python3-oauth2client
apt-get install -y python3-jsonrpclib-pelix
apt-get install -y python3-dnspython
apt-get install -y python3-ecdsa
apt-get install -y python3-pbkdf2
apt-get install -y python3-socks
apt-get install -y python3-requests
apt-get install -y protobuf-compiler
python_git_repo_v https://github.com/spesmilo/electrum.git electrum 3.2.2

# yeee godddds....
cd electrum
protoc --proto_path=lib/ --python_out=lib/ electrum/paymentrequest.proto
python3 setup.py install
cd ..

# TODO....
#ays9/.git/config:	url = https://github.com/jumpscale/ays9
#core9/.git/config:	url = https://github.com/threefoldtech/jumpscale_core
#home/.git/config:	url = https://github.com/jumpscale/home
#jumpscale_core/.git/config:	url = https://github.com/threefoldtech/jumpscale_core
#portal9/.git/config:	url = https://github.com/jumpscale/portal9

# install zerotier TODO, threefoldtech variant of this?
python_git_dev https://github.com/zero-os/zerotier_client.git zerotier_client
python_git_dev https://github.com/threefoldtech/0-hub.git 0-hub/client

# these allow jumpscale_core to "pick up" locations that need to be walked
# in order to create the jumpscale.py file, which is then installed
# (now using distutils setup).
mk_hack_symlink jumpscale_lib
mk_hack_symlink jumpscale_prefab
mk_hack_symlink jumpscale_core

# grab the three main jumpscale repos...
python_git_dev https://github.com/threefoldtech/jumpscale_core jumpscale_core
python_git_dev https://github.com/threefoldtech/jumpscale_lib jumpscale_lib
python_git_dev https://github.com/threefoldtech/jumpscale_prefab \
                                                    jumpscale_prefab

# now... at last... finally...
mk_hack_symlink 0-robot
python_git_dev https://github.com/threefoldtech/0-robot 0-robot
