
# install

```bash
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/development_960/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
```

```bash
#to define branch:
export JUMPSCALEBRANCH="development_960"
curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh;bash /tmp/install_jumpscale.sh
```

to follow the install

```bash
tail -f /tmp/install_jumpscale.sh
```

to test that it worked:

```bash
js_shell
```

### Install using pip3 (needs to be tested)

```
mkdir -p /opt/code/github/threefoldtech/jumpscale_core
pip3 install -e git+https://github.com/threefoldtech/jumpscale_core@development#egg=core --src /opt/code/github/threefoldtech/jumpscale_core
```
