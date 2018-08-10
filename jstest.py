from collections import Mapping, Set, Sequence 
from Jumpscale import j

j.tools.jsloader.generate()
dj = j.tools.jsloader.dynamic_generate()

from jumpscale import j as jgen

def listin(list1, list2):
    isin = []
    notin = []
    for i in list1:
        if i in list2:
            isin.append(i)
        else:
            notin.append(i)
    return isin, notin

def compare(tree, obj1, obj2, depth):
    if depth == 0:
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
        subobj1 = getattr(obj1, subname)
        subobj2 = getattr(obj2, subname)
        compare("%s.%s" % (tree, subname), subobj1, subobj2, depth-1)

compare('j', jgen, dj, 2)

print (dir(dj.clients))
print (dir(jgen.clients))
