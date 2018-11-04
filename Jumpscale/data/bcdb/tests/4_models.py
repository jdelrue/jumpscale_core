from Jumpscale import j


def main(self):
    """
    to run:

    js_shell 'j.data.bcdb.test(name="models",start=True)'

    work with toml files and see if models get generated properly

    """

    #make sure we remove the maybe already previously generated model file
    
    j.shell()

    zdb_cl = j.clients.zdb.testdb_server_start_client_get(reset=True)
    db = j.data.bcdb.get(name="test",zdbclient=zdb_cl)
    db.reset_index()

    db.models_add("%s/tests"%self._path,overwrite=True)

    m = db.model_get('jumpscale.bcdb.test.house')

    o = m.new()
    o.cost = "10 USD"

    m.set(o)

    data = m.get(o.id)

    assert data.cost_usd == 10

    assert o.cost_usd == 10

    assert m.index.select().first().cost == 10.0  #is always in usd

    print ("TEST3 DONE, but is still minimal")


    return ("OK")

