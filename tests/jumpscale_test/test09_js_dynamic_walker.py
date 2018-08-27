import types
from .testcases_base import TestcasesBase
from collections import Mapping, Set, Sequence

def listin(list1, list2):
    isin = []
    notin = []
    for i in list1:
        if i in list2:
            isin.append(i)
        else:
            notin.append(i)
    return isin, notin

def compare(tree, j, obj1, obj2, depth, actionfn=None,
            includeonly=None, exclude=None, errorfn=None):

    if exclude is None:
        exclude = []
    if actionfn:
        actionfn(tree, j, obj1, obj2, depth)

    if depth == 0:
        return
    if errorfn:
        try:
            contents1 = dir(obj1)
            contents1 = list(filter(lambda x: not x.startswith("__"),
                                contents1))
            contents1.sort()
        except Exception as e:
            errorfn(tree, j, obj1, obj2, depth, e)
            return
    contents1 = dir(obj1)
    contents1 = list(filter(lambda x: not x.startswith("__"), contents1))
    contents1.sort()
    contents2 = dir(obj2)
    contents2 = list(filter(lambda x: not x.startswith("__"), contents2))
    contents2.sort()

    isin, notin = listin(contents1, contents2)
    isin1, notin1 = listin(contents2, contents1)

    if notin:
        print ("not in 1", tree, obj1, obj2)
        print ("not in", tree, notin)
        print ("isin", tree, isin)

    if notin1:
        print ("not in 2", tree, obj1, obj2)
        print ("not in", tree, notin1)
        print ("isin", tree, isin)

    for subname in isin:
        fullname = "%s.%s" % (tree, subname)
        if includeonly and fullname not in includeonly:
            continue
        if fullname in exclude:
            continue
        if errorfn:
            try:
                subobj1 = getattr(obj1, subname)
                subobj2 = getattr(obj2, subname)
            except Exception as e:
                errorfn(tree, j, obj1, obj2, depth, e)
                continue
        else:
            subobj1 = getattr(obj1, subname)
            subobj2 = getattr(obj2, subname)
        compare(fullname, j,
                subobj1, subobj2, depth-1, actionfn, includeonly,
                exclude, errorfn)

class TestJSDynamicWalker(TestcasesBase):

    def test001_dynamic_vs_static(self):
        """ JS-001

            Creates a dynamic walker and a static one and does a compare
        """
        from Jumpscale import j
        #j.tools.loader.generate()
        #dj = j.tools.loader.dynamic_generate(basej=j)

        compare('j', j, j, j, 2)

# import here to get a recursive walk on the tree.  it is NOT used
# to do the actual test: see def _testfn() which does a "self.j.jget"
# on the *name* of the object, in the TestcasesBase j instance that's
# been set up in an isolated config
from Jumpscale import j
dynamic_test_count = 0

class TestJSDynamicWalkerTestSearch(TestcasesBase):
    pass

def _errortest(tree, j, obj1, obj2, depth, e):
    global dynamic_test_count
    dynamic_test_count += 1
    def _testfn(*args, **kwargs):
        print ("error walking object %s" % tree)
        raise e
    name = tree.replace(".", "_")
    setattr(TestJSDynamicWalkerTestSearch,
            "test%4d_%s_error" % (dynamic_test_count, name),
            _testfn)

def _listtests(tree, j, obj1, obj2, depth):
    """ adds a function named after the tree (j.xxx.xxx) if its
        last component ends in "test{something}"
    """
    if not tree.split('.')[-1].startswith('test'):
        return
    print ("listtests", tree, tree.split('.')[-1])
    if not callable(obj1):
        return
    global dynamic_test_count
    dynamic_test_count += 1
    def _testfn(self, *args, **kwargs):
        newobj = self.j.jget(tree)
        print ("tree", newobj, tree)
        newobj()
    name = tree.replace(".", "_")
    _testfn = types.MethodType(_testfn, j)
    setattr(TestJSDynamicWalkerTestSearch,
            "test%04d_%s" % (dynamic_test_count, name),
            _testfn)

skipproperties = [
        # add tests which are to be skipped due to being dangerous
        # (destructive) or are being skipped because they have
        # a bugreport associated with them.  add the link to the
        # bugreport as a comment here.

        'j.tools.testengine.testFile', # not a unit test
        'j.tools.formbuilder.test_interactive', # an interactive test

        # https://github.com/threefoldtech/jumpscale_core/issues/79
        'j.clients.tarantool.testmodels', # destroys files
        'j.clients.tarantool.test', # destroys files
        'j.clients.tarantool.test_find', # destroys files

        # https://github.com/threefoldtech/jumpscale_core/issues/84
        'j.tools.team_manager.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/85
        'j.data.markdown.test2',

        # https://github.com/threefoldtech/jumpscale_core/issues/86
        'j.tools.configmanager.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/87
        'j.tools.markdowndocs.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/88
        'j.tools.nodemgr.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/89
        'j.tools.numtools.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/92
        'j.tools.raml.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/93
        'j.tools.prefab.test',

        # https://github.com/threefoldtech/jumpscale_core/issues/94
        'j.tools.alerthandler.test',

        # https://github.com/threefoldtech/jumpscale_lib/issues/94
        'j.data.indexdb.test',

        # https://github.com/threefoldtech/jumpscale_lib/issues/100
        'j.tools.jinja2.test',

        # https://github.com/threefoldtech/jumpscale_lib/issues/100
        'j.tools.jinja2.test',

        # https://github.com/threefoldtech/jumpscale_lib/issues/101
        'j.tools.develop.test_js_quick',

        # https://github.com/threefoldtech/jumpscale_lib/issues/102
        'j.servers.zdb.test',

    ]

# use this for testing of a restricted set of tests
onlyproperties = [
    #'j.clients.zdb.test',
    ]

compare('j', j, j, j, 3, _listtests, includeonly=onlyproperties,
        exclude=skipproperties,
        errorfn=_errortest)

