FROM ubuntu:18.04

ARG jumpscale_branch

ENV JUMPSCALEBRANCH=$jumpscale_branch

RUN apt update && apt install -y curl ssh git python3-distutils build-essential python3-dev && mkdir /root/.ssh
RUN curl -sk https://bootstrap.pypa.io/get-pip.py > /tmp/get-pip.py && python3 /tmp/get-pip.py && rm -f /tmp/get-pip.py
RUN curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh && bash /tmp/install_jumpscale.sh
RUN ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa && js_config init -s -p /opt/cfg/myconfig -k /root/.ssh/id_rsa
CMD ["js_shell"]
