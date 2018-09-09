from Jumpscale import j
JSBASE = j.application.jsbase_get_class()



class PerfTestTools(JSBASE):

    def __init__(self, node):
        JSBASE.__init__(self)
        self.node = node

    def sequentialReadWrite(self, size="1000M", nrfiles=3):
        """
        """
        for disk in self.node.disks:
            self.logger.debug("SEQUENTIAL READ/WRITE %s %s" % (self.node, disk))

            path = "%s/testfile" % disk.mountpath
            filepaths = ""
            for i in range(nrfiles + 1):
                filepaths += "-F '%s%s' " % (path, (i))

            cmd = "iozone -i 0 -i 1 -R -s %s -I -k -l 5 -r 256k -t %s -T %s" % (size, nrfiles, filepaths)
            disk.execute(cmd)

    def randomReadWrite(self, size="100M", nrfiles=6, blocksize="8k"):
        """
        """
        for disk in self.node.disks:
            self.logger.debug("RANDOM READ/WRITE %s %s" % (self.node, disk))

            path = "%s/testfile" % disk.mountpath
            filepaths = ""
            for i in range(nrfiles + 1):
                filepaths += "-F '%s%s' " % (path, (i))

            cmd = "iozone -i 0 -i 1 -R -s %s -I -k -l 5 -r %s -t %s -T %s" % (size, blocksize, nrfiles, filepaths)
            disk.execute(cmd)
