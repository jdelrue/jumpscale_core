"""
Script to test ssh client functionalities
This test assumes that the environment has already an sshkey configured and the
name of the sshkey is id_rsa
"""

#!/usr/bin/python3
import os
from Jumpscale import j


sshkey_name = 'id_rsa'
def test_ssh_connect():
    pub_key = j.sal.fs.readFile('{}/.ssh/{}.pub'.format(os.environ['HOME'], sshkey_name))
    j.sal.fs.writeFile('{}/.ssh/authorized_keys'.format(os.environ['HOME']), pub_key, append=True)
    client = j.clients.ssh.new('localhost', instance='localhost', keyname=sshkey_name)
    client.connect()

    print('Connection via ssh client are OK')
