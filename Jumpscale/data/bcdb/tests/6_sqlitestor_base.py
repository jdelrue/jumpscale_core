from Jumpscale import j


def main(self):
    """
    to run:

    js_shell 'j.data.bcdb.test(name="sqlitestor_base")'

    use a bcdb which is using sqlite

    """


    bcdb,model = self._load_test_model(reset=True,sqlitestor=True)

    mpath = self._dirpath+"/tests/models"
    assert j.sal.fs.exists(mpath)

    #make sure we remove the maybe already previously generated model file
    for item in j.sal.fs.listFilesInDir(mpath, filter="*.py"):
        j.sal.fs.remove(item)


    bcdb.models_add(mpath)


    m = bcdb.model_get('jumpscale.bcdb.test.house')
    assert m.get_all() == []

    assert m.bcdb.zdbclient == None

    o = m.new()
    o.cost = "10 USD"
    o.save()
    m.cache_reset()
    data = m.get(o.id)
    assert data.cost_usd == 10
    assert o.cost_usd == 10

    m.cache_reset()
    o.cost = "11 USD"
    o.save()
    data = m.get(o.id)
    #is with cash
    assert data.cost_usd == 11
    m.cache_reset()
    assert m.obj_cache == {}  #cache needs to be empty
    data = m.get(o.id)
    assert data.cost_usd == 11
    assert m.obj_cache != {} #now there needs to be something in

    m.cache_reset()
    o = m.new()
    o.cost = "12 USD"
    o.save()
    assert m.obj_cache != {} #now there needs to be something in

    assert o.id == 2

    m.get(1)._ddict == {'name': '',
         'active': False,
         'cost': b'\x00\x97\x0b\x00\x00\x00',
         'room': [],
         'id': 2}

    m.get(2)._ddict == {'name': '',
         'active': False,
         'cost': b'\x00\x97\x0c\x00\x00\x00',
         'room': [],
         'id': 2}



    assert m.index.select().first().cost == 11.0  #is always in usd

    print ("TEST FOR MODELS DONE in SQLITE")

    return ("OK")

