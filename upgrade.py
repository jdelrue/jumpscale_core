
import os
from sys import platform

HOME=os.environ["HOME"]

def e(cmd):
    print(cmd)
    os.system(cmd)

e("rm -rf %s/jumpscale"%HOME)
e("rm -rf %s/opt/jumpscale"%HOME)
e("rm -rf %s/opt/var/log"%HOME)
e("mkdir -p %s/opt/var/log"%HOME)
e("rm -f %s/.mascot.txt"%HOME)
e("rm -rf %s/.cfg"%HOME)
e("rm -rf %s/.code_data_dir"%HOME)
e("rm -f %s/.profile_js"%HOME)
e("rm -f %s/.jsconfig"%HOME)


def sed_delete(path,toremove=[]):
    for item in toremove:
        if platform == "darwin":
            cmd="sed -i '' '/%s/d' %s"%(item,path)
        else:
            cmd="sed -i '/%s/d' %s"%(item,path)
        print(cmd)
        e(cmd)

sed_delete("%s/.profile_js"%HOME,["sshkeyname","profile_js","zlibs.sh","includes","environment variables","serial"])


def pip(items):
    for item in items:
        cmd="pip3 install %s --upgrade"%item
        e(cmd)

# pip(["python-jose","PyNaCl","PyJWT","fakeredis","pudb","serial"])

e("js_init")

e("js_config init")
