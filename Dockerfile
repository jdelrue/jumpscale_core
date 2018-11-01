FROM ubuntu:18.10

ARG jumpscale_branch

ENV JUMPSCALEBRANCH=$jumpscale_branch
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt update && apt install -y curl sudo python3.7 && mkdir /root/.ssh && ln -s /usr/bin/python3.7 /usr/bin/python3
RUN curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/$JUMPSCALEBRANCH/install.sh?$RANDOM > /tmp/install_jumpscale.sh && bash /tmp/install_jumpscale.sh
RUN ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa && js_config init -s -p /opt/cfg/myconfig -k /root/.ssh/id_rsa


CMD ["js_shell"]
