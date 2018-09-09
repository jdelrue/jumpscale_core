# Dynamic Loading and Reducing Filesystem load on imports

Python imports are extremely powerful, flexible... and consequently
would have a massive impact on a distributed filesystem.  Reducing
open and stat operating system calls is therefore a pretty high priority.

To see for yourself how much even one import can cause massive amounts
of filesystem access, install any python module and import it, running
strace to check.  nose is used as an example:

    strace -o log.txt python -c 'import nose'

a grep "nose" log.txt shows 124 occurrences, starting with these:

    stat("/usr/lib/python3/dist-packages/nose/__init__.cpython-36m-x86_64-linux-gnu.so", 0x7ffcb9e19ee0) = -1 ENOENT (No such file or directory)
    stat("/usr/lib/python3/dist-packages/nose/__init__.abi3.so", 0x7ffcb9e19ee0) = -1 ENOENT (No such file or directory)
    stat("/usr/lib/python3/dist-packages/nose/__init__.so", 0x7ffcb9e19ee0) = -1 ENOENT (No such file or directory)
    stat("/usr/lib/python3/dist-packages/nose/__init__.py", {st_mode=S_IFREG|0644, st_size=404, ...}) = 0
    stat("/usr/lib/python3/dist-packages/nose/__init__.py", {st_mode=S_IFREG|0644, st_size=404, ...}) = 0
    openat(AT_FDCWD, "/usr/lib/python3/dist-packages/nose/__pycache__/__init__.cpython-36.pyc", O_RDONLY|O_CLOEXEC) = 3
    stat("/usr/lib/python3/dist-packages/nose", {st_mode=S_IFDIR|0755, st_size=4096, ...}) = 0
    stat("/usr/lib/python3/dist-packages/nose", {st_mode=S_IFDIR|0755, st_size=4096, ...}) = 0
    stat("/usr/lib/python3/dist-packages/nose", {st_mode=S_IFDIR|0755, st_size=4096, ...}) = 0
    openat(AT_FDCWD, "/usr/lib/python3/dist-packages/nose", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 3

What is happening here is that python can potentially have a pre-compiled
c-based module (optimised for cpython)... and it goes downhill rapidly
from there.  *This occurs on every single import*.

With jumpscale plugins, a single import "Jumpscale.core.Application" can
potentially hit the (distributed) filesystem well over *24 times* before the
right module is actually found.

A secondary issue that needs to be fixed is the way that applications are
written.  There is a critical recursive dependency caused by the following
pattern:

    from Jumpscale import j
    from .JSBase import JSBase

    class Application:

        def jsbase_get_class(self):
            return JSBase

where it is documented that applications should use the following pattern:

    from Jumpscale import j
    JSBASE = j.application.jsbase_get_class()

    class myclass(JSBASE):
        __jslocation__ = 'j.somewhere.myinstance' # REQUIRED
        def __init__(self):
            JSBASE.__init__(self)
            ...

This sets up a global dependency on, well... a global variable!  That
means that imports can get extremely complex: this in turn causes severe
programming headaches too complex and numerous to describe here.  Also,
whilst this example looks simple, when multiple inheritance is involved
(which requires imports that in turn potentially hit the filesystem with
dozens of stats), the consequences are much more severe and the complexity
even higher.

# Dynamic Loading

In the dynamic loader paradigm, classes and modules are never imported
directly.  The paradigm above is replaced with the following:

    class Application:

        __jslocation__ = "j.core.application" # REQUIRED

        @property
        def JSBase(self):
            return type(self).mro()[1]

        def jsbase_get_class(self):
            return self.JSBase

and class instantiation replaced with this:

    DSomeClass = self._jsbase( ('SomeClass', 'Jumpscale.subpath.SomeModule'))
    instance = DSomeClass(self, path, otherargs)

Note three things here: firstly, JSBase is now a property, and specifically
it is *not* imported: it is taken *from* the Application class
"method resolution order" (i.e. one of its base classes).  This reduces
file-system hits through not having to import JSBase.

Secondly: to instantiate a class, a function (which is in JSBase)
called "\_jsbase" is called.  However, note that class Application
does not appear to derive from JSBase (and nothing else does either!)

This is because JSBase.\_jsbase actually creates an *entirely new*
(dynamic) class, using a little-known three-argument property of
the python "type" function that is capable of creating full classes
on-demand, and its only real absolute top priority and task is to
*transparently add JSBase to the list of classes to derive from*.

Thirdly: for this to work, the entire "j" object tree *must* remain within
the dynamic framework / pattern.  The very first (and only) JSBase object ever
created has to be set up manually (and this is done in the bootstrap:
it is *not* to be done by developers), and from that point onwards
*all* classes and instances can and must use self.\_jsbase for this
pattern to work.

Fourthly: the declaration of an \_\_jslocation\_\_ is an absolutely
essential and critical requirement.  Without this, the JSLoader system
will fail to recognise the existence of the module.  The dynamic loader
system will do its best to cope if it is missing, however it should
in no way be relied on (for reasons best left out of this document).
It is always, always best to declare the jslocation, and to do so
at the *class* level, *not* as an instance in the class constructor.

The other very very important aspect of this process, behind the
scenes, is that because of this third point, the entire import system
can now be "hooked" to *specifically* load *only* from the most efficient
and known filesystem location *specifically* for that requested module
(and class).

Also, note that, again, in the following example, there are *no imports*:

    class Core: # does not import from JSBase

        __jslocation__ = 'j.core' # AGAIN THIS IS REQUIRED

        def __init__(self):
        self._db = None
        self._state = None

        @property
        def db(self):
        if not self._db:
            self._db = self.j.clients.redis.core_get() # self.j not j...
        return self._db

        @property
        def state(self):
        if self._state is None:
            return self.j.tools.executorLocal.state # self.j not j
        return self._state

"from Jumpscale import j" is not present.  "JSBase" is not present.
"j.clients.redis" has been replaced with "self.j.clients.redis".
In other words, the entire class is stand-alone *completely independent
of any external imports*.  This is highly desirable as it means that
the code is clean, abstracted, and does not cause unnecessary
file-system "hits".

It is important to note that "from Jumpscale import j" will still work.
Also, the old pattern (importing manually from JSBase) will also still work,
however it is critically important that the JSBase.\_\_init\_\_(self) be
moved to the top of the \_\_init\_\_ function, otherwise things break.

    from Jumpscale import j
    JSBASE = j.application.jsbase_get_class()

    class KeyValueStoreBase(JSBASE):

        def __init__(self, namespace, name="", serializers=[],
             	 	   masterdb=None, cache=None, changelog=None):

	# JSBASE.__init__ absolutely must be moved to here

        self.namespace = namespace
        self.name = name
        self.serializers = serializers or list()
        self.unserializers = list(reversed(self.serializers))
        self.changelog = changelog
        self.masterdb = masterdb
        self._schema = b""
        self.owner = ""  # std empty
        self.inMem = False

        JSBASE.__init__(self) # this absolutely must be moved

# Slightly more advanced dynamic loading

The above will create an instance for immediate use.  The import
of the module, and the instantiation of the object, takes place
immediately that JSBase._jsbase is called.  This may not be
desirable, and the bootstrap system in particular relies heavily
on "lazy loading" through overloading \_\_dir\_\_ and \_\_getattribute\_\_
to make absolutely sure that it *appears* that everything is
present and correct, when in fact only when things are actually
accessed does the filesystem get a "hit" with an actual import.

Two functions exist called BaseGetter.\_add\_instance and
BaseGetter.\_\_add_kls which do *not* do immediate importing.
These will add a (dynamically created) instance of a class or
an *actual* class to a parent object, on-demand.

This is (partly) a work-in-progress: therefore the name of the
module (in full) must be created, and the name of the actual
python file (its full, absolute path) must also be created:
see module and mfullpath parameters, below, respectively.

    class SerializersFactory:

        __jslocation__ = "j.data.serializers"

        serialisers = [
            ['int', 'SerializerInt'],
            ['base64', 'SerializerBase64'],
            ...
            ...
            ['snappy', 'SerializerSnappy'],
            ['toml', 'SerializerTOML'],
        ]

        def __init__(self):

            fullpath = os.path.dirname(self.__jsfullpath__)
            for s in self.serialisers:
                [attr, kls, packtype] = s
                module = 'Jumpscale.data.serializers.%s' % kls # same name
                mod = self._add_instance(attr, module, kls)

Whilst this will be reworked to do relative imports (automatically
taking the name of the module path from the *parent* object
self.\_\_jsfullpath\_\_
later, it is quite straightforward and basically adds lazy-instances
named after the field "attr" to the current SerializersFactory instance
(self.snappy which will appear as j.data.serializers.snappy or better
self.j.data.serializers.snappy), of a class named "kls", imported from
the module named "Jumpscale.data.serializers.<INSERT SAME CLASS NAME kls>".
Functionally it is equivalent to:

    from <Module> import <class>

However bear in mind that these are **NOT** actual instances, they are
*lazy* instances inserted into the SerializersFactory BaseGetter
"hidden" dictionary, which, *only* if that *specific* attribute named
"attr" is accessed, will the instance (or the class, if \_add\_kls
is used instead), actually get created.

Functionality-wise this code works.  It is just not very pretty.  Hence
this documentation, as it is also indicative of the direction that is
being taken.
