from Jumpscale import j


def main(self):
    """
    to run:

    js_shell 'j.data.bcdb.test(name="acls",start=True)'

    test around acls

    """

    S = """
    @url = despiegk.test5.acl
    name = "" 
    an_id = 0
    """

    zdbclient_admin = j.servers.zdb.client_admin_get()
    zdbclient = zdbclient_admin.namespace_new("test",secret="1234")
    zdbclient.flush() #empty
    bcdb = j.data.bcdb.get(name="test",zdbclient=zdbclient)
    m=bcdb.model_get_from_schema(S) #model has now been added to the DB

    self.logger.info("POPULATE DATA")

    for i in range(10):
        u=bcdb.user.new()
        u.name="ikke_%s"%i
        u.email="user%s@me.com"%i
        u.dm_id = "user%s.ibiza"%i
        u.save()

    for i in range(10):
        g=bcdb.group.new()
        g.name="gr_%s"%i
        g.email="group%s@me.com"%i
        g.dm_id = "group%s.ibiza"%i
        g.group_members = [x for x in range(i+1)]
        g.user_members = [x for x in range(i+1)]
        g.save()

    self.logger.info("ALL DATA INSERTED (DONE)")

    self.logger.info("walk over all data")
    l = bcdb.get_all()

    self.logger.info("walked over all data (DONE)")

    assert len(l)==20
    u0=l[0]
    g0=l[10]


    self.logger.info("ACL TESTS PART1")

    a=bcdb.acl.new()
    user = a.users.new()
    user.rights="wrwd"
    user.uid = 1
    group = a.groups.new()
    group.rights="wwd"
    group.uid = 2
    group = a.groups.new()
    group.rights="e"
    group.uid = 3


    a=a.save()

    assert a.hash == '5719df13fa127f1c46544250abba0d61'

    assert len(bcdb.get_all())==21

    index = bcdb.acl.index

    a_id2 = index.select().where(index.hash == a.hash).first().id

    assert a.id==a_id2
    assert a.readonly == True

    #new model new

    a= m.new()
    a.name = "aname"

    change = a.acl.rights_set(userids=[1],groupids=[2,3],rights="rw")
    assert change == True

    assert a.acl.readonly==False
    a.save()
    assert a.acl.readonly

    assert len(bcdb.acl.get_all())==2
    assert a.acl.hash == 'fa53cc2c53702aef90db0026b4e023f4'

    self.logger.debug("MODIFY RIGHTS")
    a.acl.rights_set(userids=[1],rights="r")
    a.save()
    assert a.acl.readonly
    acl_old_id=a.acl.id+0

    assert len(bcdb.acl.get_all())==3 #there needs to be a new acl

    assert a.acl.hash == '240481437f4c67f40c2683883b755ac3'


    assert a.acl.rights_check(1,"r") == True
    assert a.acl.rights_check(1,"d") == False

    a.acl.rights_set([1],[],"rw")
    assert a.acl.rights_check(1,"r") == True
    assert a.acl.rights_check(1,"w") == True
    assert a.acl.rights_check(1,"rw") == True
    assert a.acl.rights_check(1,"rwd") == False
    assert a.acl.rights_check(1,"d") == False
    a.save()

    #NEED TO DO TESTS WITH GROUPS

    self.logger.info("ACL TESTS ALL DONE")

