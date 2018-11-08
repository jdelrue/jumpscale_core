from gevent import monkey
monkey.patch_all()

import os
from jumpscale import j
from gevent import pool

SECRET = '123456789012345678901234'
SIZE = 1024*500


def worker(name):
    nacl = j.data.nacl.get(sshkeyname='id_rsa')
    clear = os.urandom(SIZE)
    encrypted = nacl.encryptSymmetric(clear)
    decrypted = nacl.decryptSymmetric(encrypted)
    assert clear == decrypted


def test_concurrence():
    N = 2000
    p = pool.Pool()
    expected_secrets = ["greenlet_%d" % i for i in range(N)]
    p.map(worker, expected_secrets)
    p.join()
