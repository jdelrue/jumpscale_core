# How to create flist using 0-OS container:

First setup your build environment on your 0-OS node:

```shell
$ js_builder configure <ip> # configure js_builder to use your 0-OS node
zero-os node configured

$ js_builder zdb # create  zdb that will hold the data of the flist
finding best disk where to deploy zdb...
deploying zdb on /mnt/zdbs/builder_zdbnjomhl3w 
zdb deployed
reach it publicly at 10.241.226.45:3334
reach it internally at 172.18.0.6:9900

$ js_builder container # start a ubuntu18.04 container used for the building
builder container deployed
to connect to it do: 'ssh root@10.241.226.45 -p 2222' (password: rooter)
can also connect using js_node toolset, recommended: 'js_node ssh -i builder'
```
Write down the ip address and port of the 0-db given by the comand `js_builder zdb`, you will need it when creating the flist


Let's now build something inside our buidler container
```python
# get a prefab client in the builder container
prefab = j.tools.nodemgr.get('builder').prefab

# get a client to the builder container itself
node = j.clients.zos.get('builder')
builder = node.containers.get('builder')


# install mongodb
prefab.db.etcd.install(start=False)

# tell the container to create a new flist using `/opt/bin` as source and writing the flist to /tmp/etcd.flist and sending the data to the 0-db located at 172.20.0.1:9900
flist_location = builder.client.flist.create('/opt/bin','/tmp/etcd.flist', storage='172.18.0.6:9900')
prefab.core.download(flist_location,'/tmp/etcd.flist')
```

The flist has now been downloaded locally

In real life you would now share this flist with other...
For the sake of the demo i'll just assume the flist we created is available on the 0-OS node already


Let's create a new container with the flist we just created
```python
container = node.containers.create('etcd', '/tmp/etcd.flist')
# print help of etcd to make sure the flist is working properly
container.client.system("etcd --help").get()
```