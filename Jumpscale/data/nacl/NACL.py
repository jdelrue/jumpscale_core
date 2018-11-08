from jumpscale import j
from nacl.public import PrivateKey, SealedBox
import nacl.signing
import nacl.secret
import nacl.utils
import nacl.hash
import nacl.encoding
import hashlib
# from .AgentWithKeyname import AgentWithName
import binascii
from nacl.exceptions import BadSignatureError
from gevent.exceptions import ConcurrentObjectUseError
import time

JSBASE = j.application.jsbase_get_class()


class NACL(JSBASE):

    def __init__(self, name, secret="", sshkeyname=""):
        """
        is secret == "" then will use the ssh-agent to generate a secret
        """
        JSBASE.__init__(self)
        if sshkeyname:
            self.logger.debug("sshkeyname for nacl:%s" % sshkeyname)
            pass
        elif j.tools.configmanager.keyname:
            self.logger.debug("get config from git repo, keyname='%s'" % j.tools.configmanager.keyname)
            sshkeyname = j.tools.configmanager.keyname
        else:
            sshkeyname = j.core.state.configGetFromDict("myconfig", "sshkeyname")
            self.logger.debug("get config from system, keyname:'%s'" % sshkeyname)

        self.sshkeyname = sshkeyname

        if isinstance(secret, str):
            secret = secret.encode()

        self.name = name

        self.path = j.tools.configmanager.path
        self.logger.debug("NACL uses path:'%s'" % self.path)

        # get/create the secret seed
        self.path_secretseed = "%s/%s.seed" % (self.path, self.name)

        if not j.sal.fs.exists(self.path_secretseed):
            secretseed = self.hash32(nacl.utils.random(
                nacl.secret.SecretBox.KEY_SIZE))
            self.file_write_hex(self.path_secretseed, secretseed)
        else:
            secretseed = self.file_read_hex(self.path_secretseed)

        # this creates a unique encryption box
        # the secret needs 3 components: the passphrase(secret), the
        # secretseed means the repo & a loaded ssh-agent with your ssh key
        secret2 = self.hash32(secretseed + secret +
                              self.sign_with_ssh_key(secretseed + secret))
        # self._box is a temp encryption box which only exists while this
        # process runs
        # create temp box encrypt/decr (this to not keep secret in mem)
        self._box = nacl.secret.SecretBox(
            nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE))
        self.secret = self._box.encrypt(
            secret2, nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE))
        secret = ""
        secret2 = ""
        secretseed = ""

        self.path_privatekey = "%s/%s.priv" % (self.path, self.name)
        if not j.sal.fs.exists(self.path_privatekey):
            self._keys_generate()
        self._privkey = ""
        self._pubkey = ""
        self._signingkey = ""
        self._signingkey_pub = ""

        # self.path_words = "%s/%s.words" % (self.path, self.name)

        # self.path_privatekey_sign = "%s/%s_sign.priv" % (self.path, self.name)
        # if not j.sal.fs.exists(self.path_privatekey_sign):
        #     self._keys_generate_sign()

    @property
    def privkey(self):
        if self._privkey == "":
            self._privkey = self.file_read_hex(self.path_privatekey)
        key = self.decryptSymmetric(self._privkey)
        privkey = PrivateKey(key)
        self._pubkey = privkey.public_key
        return privkey

    @property
    def words(self):
        """
        js_shell 'print(j.data.nacl.default.words)'
        """
        return j.data.encryption.mnemonic.to_mnemonic(self.privkey.encode())
        # if not j.sal.fs.exists(self.path_words):
        #     self.logger.info("GENERATED words")
        #     words = j.data.encryption.mnemonic_generate()
        #     words = self.encryptSymmetric(words)
        #     self.file_write_hex(self.path_words,words)
        # words = self.file_read_hex(self.path_words)
        # words = self.decryptSymmetric(words)
        # return words.decode()

    @property
    def pubkey(self):
        if self._pubkey == "":
            return self.privkey.public_key
        return self._pubkey

    @property
    def signingkey(self):
        if self._signingkey == "":
            self._signingkey = nacl.signing.SigningKey(self.privkey.encode())
        return self._signingkey

    @property
    def signingkey_pub(self):
        if self._signingkey_pub == "":
            self._signingkey_pub = self.signingkey.verify_key
        return self._signingkey_pub

    def _getSecret(self):
        # this to make sure we don't have our secret key open in memory
        res = self._box.decrypt(self.secret)
        if res == b"":
            raise RuntimeError("serious bug, cannot get secret key")
        return res

    def tobytes(self, data):
        if not j.data.types.bytes.check(data):
            data = data.encode()  # will encode utf8
        return data

    def hash32(self, data):
        m = hashlib.sha256()
        m.update(self.tobytes(data))
        return m.digest()

    def hash8(self, data):
        # shortcut, maybe better to use murmur hash
        m = hashlib.sha256()
        m.update(self.tobytes(data))
        return m.digest()[0:8]

    def encryptSymmetric(self, data, secret="", hex=False, salt=""):
        if secret == "":
            box = nacl.secret.SecretBox(self._getSecret())
        else:
            box = nacl.secret.SecretBox(self.hash32(secret))
        if salt == "":
            salt = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        else:
            salt = j.data.hash.md5_string(salt)[0:24].encode()
        res = box.encrypt(self.tobytes(data), salt)
        box = None
        if hex:
            res = self.bin_to_hex(res).decode()
        return res

    def decryptSymmetric(self, data, secret=b"", hex=False):
        if secret == b"":
            box = nacl.secret.SecretBox(self._getSecret())
        else:
            box = nacl.secret.SecretBox(self.hash32(secret))
        if hex:
            data = self.hex_to_bin(data)
        res = box.decrypt(self.tobytes(data))
        box = None
        return res

    def encrypt(self, data, hex=False):
        """
        Encrypt data using the public key
            :param data: data to be encrypted, should be of type binary
            @return: encrypted data
        """
        data = self.tobytes(data)
        sealed_box = SealedBox(self.pubkey)
        res = sealed_box.encrypt(data)
        if hex:
            res = self.bin_to_hex(res)
        return res

    def decrypt(self, data, hex=False):
        """
        Decrypt incoming data using the private key
            :param data: encrypted data provided
            @return decrypted data
        """
        unseal_box = SealedBox(self.privkey)
        if hex:
            data = self.hex_to_bin(data)
        return unseal_box.decrypt(data)

    def _keys_generate(self):
        """
        Generate private key (strong) & store in chosen path & will load in this class
        """
        key = PrivateKey.generate()
        key2 = key.encode()  # generates a bytes representation of the key
        key3 = self.encryptSymmetric(key2)
        path = self.path_privatekey

        self.file_write_hex(path, key3)

        # build in verification
        key4 = self.file_read_hex(path)
        assert key3 == key4

    def sign(self, data):
        """
        sign using your private key using Ed25519 algorithm
        the result will be 64 bytes
        """
        res = self.signingkey.sign(data)
        return res[:-len(data)]

    def verify(self, data, signature, pubkey=""):
        """
        data is the original data we have to verify with signature
        signature is Ed25519 64 bytes signature
        pubkey is the signature public key, is not specified will use your own  (the pubkey is 32 bytes)

        """
        if pubkey == "":
            pubkey = self.signingkey_pub
        else:
            pubkey = nacl.signing.VerifyKey(pubkey)
        try:
            pubkey.verify(data, signature)
        except BadSignatureError:
            return False

        return True

    def sign_with_ssh_key(self, data):
        """
        will return 32 byte signature which uses the sshagent loaded on your system
        this can be used to verify data against your own sshagent to make sure data has not been tampered with

        this signature is then stored with e.g. data and you can verify against your own ssh-agent if the data was not tampered with

        """
        hash = hashlib.sha1(data).digest()
        while True:
            try:
                signeddata = j.data.nacl.agent.sign_ssh_data(hash)
                return self.hash32(signeddata)
            except ConcurrentObjectUseError:
                time.sleep(0.1)
                continue

    def file_write_hex(self, path, content):
        content = binascii.hexlify(content)
        j.sal.fs.writeFile(path, content)

    def file_read_hex(self, path):
        content = j.sal.fs.readFile(path)
        content = binascii.unhexlify(content)
        return content

    def bin_to_hex(self, content):
        return binascii.hexlify(content)

    def hex_to_bin(self, content):
        content = binascii.unhexlify(content)
        return content
