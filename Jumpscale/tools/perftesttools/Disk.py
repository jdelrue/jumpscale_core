from Jumpscale import j

JSBASE = j.application.jsbase_get_class()


class Disk(JSBASE):

    def __init__(self, devname, node=None, disknr=None, screenname=None):
        JSBASE.__init__(self)
        devname.replace("//", "/")
        self.devname = devname
        self.devnameshort = self.devname.split("/")[2]
        self.mounted = False
        self.mountpath = None
        self.node = node
        self.disknr = disknr
        self.screenname = screenname

    def initDisk(self, fs='xfs'):
        """
        fs: filesystem to use when formating
        """
        self.logger.debug("init %s:%s" % (fs, self))
        res = self.node.execute("lsblk -f | grep %s" % self.devnameshort, dieOnError=False)[1].strip()
        if res == "" or res.find(fs) == -1:
            # did not find formatted disk
            self.node.execute("mkfs.%s -f /dev/%s" % (fs, self.devnameshort))
        self.mount()

        self.logger.debug("init %s:%s check mount" % (fs, self))

        if not self.checkMount():
            raise j.exceptions.RuntimeError("could not mount %s" % self)

        self.logger.debug("init %s:%s done" % (fs, self))

    def initDiskXFS(self):
        self.initDisk(fs='xfs')

    def initDiskBTRFS(self):
        self.initDisk(fs='btrfs')

    def mount(self):
        self.logger.debug("mount:%s mounting %s on %s " % (self, self.devname, self.disknr))
        if self.mountpath is None:
            self.mountpath = '/storage/%s' % self.disknr
        self.node.execute("mkdir -p /storage/%s" % self.disknr)
        self.node.execute("mount %s /storage/%s" % (self.devname, self.disknr), dieOnError=False)

    def checkMount(self):
        result = self.node.execute("mount")
        for line in result.split("\n"):
            if line.find(" on ") != -1 and line.startswith(self.devname) and line.find(self.node.fstype) != -1:
                return True
        return False

    def execute(self, cmd, env={}):
        """
        gets executed in right screen for the disk
        """
        self.node.executeInScreen(self.screenname, cmd, env=env, session="perftest")

    def __str__(self):
        return "disk:%s" % (self.devname)

    def __repr__(self):
        return self.__str__()
