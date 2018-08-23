from jumpscale import j

from .Node import Node


JSConfigBase = j.tools.configmanager.base_class_configs


class Nodes(JSConfigBase):

    def __init__(self):
        if not hasattr(self, '__jslocation__'):
            self.__jslocation__ = "j.tools.nodemgr"
        JSConfigBase.__init__(self, Node)
        self._tree = None

    @property
    def tree(self):
        if self._tree is None:
            res = self.getall()
            self._tree = j.data.treemanager.get()
            for item in res:
                self._add2tree(item)
        return self._tree

    def set(self, name, sshclient="", zosclient="", cat="", description="",
            selected=False, active=True, secretconfig="", pubconfig="", clienttype="ovc"):
        """[summary]

        clienttype:  "ovh", "packetnet", "ovc", "physical", "docker", "container", "zos"
        @PARAM sshclient is the instance name to the sshclient 

        """

        assert j.data.types.string.check(sshclient)
        assert j.data.types.string.check(zosclient)

        secretconfig = j.data.serializers.json.dumps(secretconfig)
        pubconfig = j.data.serializers.json.dumps(pubconfig)

        data = {}
        data["name"] = name
        data["sshclient"] = sshclient
        data["zosclient"] = zosclient
        data["clienttype"] = clienttype
        data["active"] = active
        data["selected"] = selected
        data["secretconfig_"] = secretconfig
        data["pubconfig"] = pubconfig
        data["category"] = cat
        data["description"] = description
        node = self.get(instance=name, data=data, create=True, interactive=False)
        node.config.save()

        # if self.exists(name):
        #     treeitem = self.tree.findByName(name, die=False)
        #     if treeitem is not None:
        #         tpath = treeitem.path
        #         self.tree.items.pop(tpath)

        # self._add2tree(node)

        return node

    def _add2tree(self, n):

        if n.category == "":
            path = "all.%s" % n.name
        else:
            path = "%s.%s" % (n.category, n.name)

        self._tree.set(path=path, data="%s|%s|%s" % (n.name, n.addr, n.port),
                       description=n.description, cat=n.category, selected=n.selected)

    def test(self):
        """
        js_shell 'j.tools.nodemgr.test()'
        """

        self.delete(prefix="myhost")
        self.logger.debug("DELETE DONE")

        startnr = len(self.getall())
        assert self.count() == startnr

        assert self.exists("myhost1") is False

        i = 9

        self.set("myhost%s" % i, "127.0.0.%s" % i, cat="testcat")

        # from IPython import embed;embed(colors='Linux')

        for i in range(10):
            self.set("myhost%s" % i, "127.0.0.%s" % i, cat="testcat")

        assert self.exists("myhost1") == True

        assert len(self.getall()) == 10 + startnr

        for i in range(5):
            self.set("myhostcat2_%s" % i, "127.0.0.%s" % i, cat="cat2")

        n = self.get("myhost9")
        d2 = {'active': True,
              'sshclient': '127.0.0.9',
              'category': 'testcat',
              'clienttype': 'ovc',
              'description': '',
              'name': 'myhost9',
              'secretconfig_': '',
              'zosclient': '',
              'pubconfig': '""',
              'installed': False,
              'selected': False}

        # from IPython import embed;embed(colors='Linux')
        assert n.config.data == d2
        j.data.serializers.toml.fancydumps(
            n.config.data) == j.data.serializers.toml.fancydumps(d2)

        self.logger.debug(self)

        n.selected = True
        assert n.selected == n.config.data["selected"]
        n.selected = False
        n.config.data = {"selected": False}
        assert n.selected == n.config.data["selected"]
        assert n.selected == False
        assert n.config.data["selected"] == False
        n.selected = True
        assert n.config.data["selected"] == True

        # now tests about updating data
        d2["port"] = 2222
        n2 = self.get(instance='myhost9', data=d2, create=True, die=True)
        assert n2.config.data["port"] == 2222

        assert len(self.list(prefix="myhost")) == 15
        assert len(self.list()) == 15 + startnr

        # cleanup
        self.delete(prefix="myhost")

        assert len(self.getall()) == startnr

        # print("TEST for nodes ok")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        # return ("%s"%self.tree)
        out = ""
        for item in self.getall():
            out += str(item) + "\n"
        return out
