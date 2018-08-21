
## a big cleanup just happened, oh my ...

- references to version of jumpscale are removed (no longer 9)
    - means all commands are now js_shell, js_init, ...
    - from jumpscale import j (no longer js9)
- bash tools removed
- docker support removed -> we now do everything in 0-OS (eat our own dogfood)
- less repositories to deal with (core,lib,prefab) 
- all 0-robot templates are now in 1 repo
  

## still to fix

lots of things which were on this readme

need to redo:
```markdown

[![Join the chat at https://gitter.im/Jumpscale/jumpscale_core](https://badges.gitter.im/Jumpscale/jumpscale_core.svg)](https://gitter.im/Jumpscale/jumpscale_core?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) ![travis](https://travis-ci.org/Jumpscale/core.svg?branch=master)


```

## 12aug2018 dynamic bootstrapping and removal of "from Jumpscale import j"

* the installation of jumpscale.py into /usr/lib was violating LSB FSH
  and was temporarily installed into /usr/local/lib instead.
  anyone who has this older jumpscale.py **MUST** remove it from
  /usr/lib/python3/dist-packages, by hand.
* JSBase now has a singleton called global_j, with a property in the
  JSBase class that allows access to it.
* Any class that is derived from JSBase can therefore access the global
  "j" as "self'j" instead.
* The legacy "from Jumpscale import j" as well as "from jumpscale import j"
  are temporarily still supported, although strongly not recommended:
  however there are still classes that do not inherit from JSBase which will
  have to temporarily use the global import until they are converted.
* JSBase now inherits from something called "BaseGetter", which has the
  very specific task of over-riding \_\_getattribute\_\_ in order to provide
  "on-demand" properties which are lazily-created.  Normally, a lazyprop
  decorator would be created, and dropped into the class, however it was
  too challenging to do that, so \_\_getattribute\_\_ was over-ridden instead.
  the BaseGetter.\_\_subgetters\_\_ dictionary stores the information needed
  to create the class instance on-demand, and calls ModuleSetup.getter
  to do it
* ModuleSetup.getter is a particularly unusual function in that it
  will (eventually) import the module SPECIFICALLY from a listed
  file location, NOT from the usual sys.path file locations.
  For now it just uses importlib.import_module.  After loading the
  module it does NOT just go ahead and instantiate the requested
  class instance, it checks to see if the class instance has
  JSBase anywhere in its base classes.  If it does not then
  *one is added*.  This is carried out in JSBase._jsbase
* JSBase._jsbase is an extremely powerful function that DYNAMICALLY
  creates a new class which multiply-interits / derives from JSBase,
  making sure that args and kwargs are properly passed through.
  It uses the extremely unusual and little-known THREE argument
  version of the standard "type" function to do it.  A special
  \_\_init\_\_ method is patched in which manually examines the
  base classes and takes care of properly calling the JSBase.\_\_init\_\_
  as well as any other multiply-inherited base classes.
* With that infrastructure in place it became possible to use the
  lazy-evaluation capabilities to break circular dependencies
  that would otherwise be impossible to work around on a dynamic
  bootstrap.
* JSLoader.bootstrap_j works from a triple list of base classes,
  child module instances and aliases (baseList, moduleList, aliases)
  that are set up using BaseGetter_add_instance and JSBase._jsbase
  to lazy-load the minimum required modules to get to the
  config files.
* Once the config files can be read, the old JSLoader.generate
  code kicks in (split now into JSLoader.gather_modules), walking
  the [plugins] directories listed in the jumpscale.toml config
  file.  The walker-process has been modified to also give a
  dictionary of any modules (root modules) in files named "\_\_init\_\_.py"
  that have a \_\_jslocation\_\_ in them.
* From the information obtained, the BaseGetter._add_instance
  and JSBase._jsbase process can be repeated, this time dropping
  in the ENTIRE series of modules into a new "j" instance,
  which is itself dynamically created, but externally, and
  must be passed in to the bootstrap_j function.
* The reason for needing to pass that in is because there are
  still recursive imports "from Jumpscale import j" that get
  used *during the bootstrap process*, that cannot yet be
  removed.  To solve this, Jumpscale.j has to exist and then
  be passed in to the JSLoader.bootstrap_j function.  It is
  a total miracle that python is able to cope with this at all.
* With the lazy-loading in place, and the global singleton
  "j" being kept in JSBase, the actual bootstrap process is
  quite straightforward.  The only awkward bit is establishing
  the LoggingFactory, which has a two-way co-dependency that
  is harder to break.  Some form of default "self-built-in"
  logging system into JSBase that outputs to stdout/stderr
  would probably do the trick (issue #66).
* With that all working, "from jumpscale import j" can now
  be replaced TEMPORARILY with "from Jumpscale import j"
  but even that should now be completely REMOVED as only
  self.j should ever be used.
* Classes - all classes - should now NEVER inherit from JSBase
  except unless they have an absolute, absolute damn good reason
  (and there are genuinely very few of those).  Over time these
  should be removed.
* If ever a new class instance is needed
* Many of the class \_\_init\_\_ methods have critical inter-dependencies
  that really should not be there.  Also, they often refer to "j"
  (now self.j) which they really should not do, as that sets up a
  critical dependency chain.  To help break the cycle,
  a "late initialisation" system has been added to JSBase.  It is
  used by calling self.add_late_init(self.load, "loadarg1", kwarg=5)
  and, on lazy-instantiation, AFTER the \_\_init\_\_ has been set up,
  all the registered late initialisations are called.
  However extreme care has to be taken as this basically changes
  the order of calling of functions.

Lastly: if ever a new class instance is needed, it should NOT
be inherited from JSBase, and it should NOT be instantiated
without first going through JSBase._jsbase, as follows:

    DynamicCC = self._jsbase(self.j, 'CacheCategory', [CacheCategory])
    self._cache[id] = DynamicCC( id=id, expiration=expiration, reset=reset)

This basically ensures that everything can remain "clean" of
"from Jumpscale import j", yet still have everything be aware of
Jumpscale... just without having to explicitly code it that way
(across hundreds of files).  It also means that if ever a new
technique is needed, it can be handled easily through modifying
*one single function*... not patching the code in literally hundreds
of places.


## 19aug2018 Dynamic self-bootstrap continued

A large number of details are in commit message 0852c1430, they are
partially documented here.  strace is being used to check progress:

$ strace -o log.txt -ff js_shell
$ grep -E "^stat|^open" log.txt.* | grep -i jumpscale | wc

* A circular dependency between j.core.dirs (Jumpscale/core/Dirs.py)
  and j.tools.executorLocal.state (Jumpscale/tools/executor/ExecutorBase.py)
  was identified in the Dirs.reload() function, which in turn was being
  called specifically from the Dirs __init__ constructor.
  Dirs.JSAPPDIR and Dirs.TEMPLATEDIR were therefore HOPELESSLY out-of-date
  and would have required the application to EXIT COMPLETELY should these
  two variables (which were also stored in the os ENVIRON) ever be changed.
  They have been changed to properties that **DYNAMICALLY**, on access,
  return values that are relative to VARDIR.  They can be over-ridden.
  The removal of the dependence on VARDIR helps break the circular
  dependency between Dirs.py and ExecutorBase.py
* An additional dependency on HOSTDIR was also successfully removed
  by no longer calling JSLoader.prepare_config, JSLoader._generate
  or anything else that was being used to write into the HOSTDIR
  (except locations as specified by ExecutorBase.py)
* When there is no config file (at all), it is assumed that because the
  JSLoader is currently being executed, it is okay to put in a not-exactly-fake
  single plugin entry based on the current working directory.
  In this way, starting up from a completely empty non-existent config file
  will successfully allow access to Jumpscale core files in a reasonable
  and consistent fashion.  (Note: not having the plugin directory be EXACTLY
  that from which the file WITHIN that plugin directory is located is neither
  reasonable nor sane, and a sanity check needs to be added to that effect)
* Overloading of __dir__ (called when dir(j.core) is done, which includes
  in IPython) has been accompanied by an overload of __getattribute__
  that will now carry out a specific search for only that j.[insertnamehere].
  This is carried out through the combined use of BaseGetter, JSBase and
  JSLoader.
* Overloading __dir__ means that "fake" (lazy) properties can *appear* to
  be listed in a j.[insertobjname] and even a j.[parent].[insertchildname].
  This is done in BaseGetter.__dir__ by storing a "fake" (lazy) property
  loader (ModuleSetup) as described above (12aug2018).
* The new capability involves a global j.__dynamic_ready__ boolean
  as well as a per-object __dynamic_ready__ which, if both are set,
  sets off a chain of (near-dangerously-recursive) searches for the
  property that has been requested (and does not actually exist... yet).
  The dangerous recursion is broken by setting __dynamic_ready__
  (see JSBase._check_child_mod_cache).
* Accessing a (non-existent) property results in (AT PRESENT) a
  walk of each of the plugins directories, specifically looking for objects
  that match that name. THIS REQUIRES THAT THE DIRECTORY HIERARCHY MATCH
  THE NAME.  For example, accessing of j.tools.dns will result in a
  search for the following:
    /opt/code/github/threefoldtech/core9/Jumpscale/tools/dns/DNSTools.py
    /opt/code/github/threefoldtech/lib9/JumpscaleLib/tools/dns/DNSTools.py
    ...
  where DNSTools.py has a class DNSTools in which "j.tools.dnstools"
  exists.  HOWEVER... this is a classic example: j.tools.dnstools
  (prior to commit 2a27cbe7) was in a subdirectory that mis-matched with
  its j object name.

So now, where requesting a listing "dir (j.tools)" results in a
filesystem walk of plugin directories looking for anything *inside*
a directory called "tools", a __getattribute__ will result in a very
specific search for a very specific (single) module in each of the
plugin locations.

This will subsequently be modified to no longer even need to walk
the filesystem (at all), by storing the dependency information actually inside
the parent (JSClassName.__jsdeps__), merging those across multiple
plugins, and issuing a very very specific importlib.util.module_from_spec()
call that *SPECIFICALLY* and *EXCLUSIVELY* loads *SPECIFICALLY* that
python module *DIRECTLY* and *NOTHING* else.  This in complete contrast to
the current system which relies on asking the standard python import system to
locate the module, which results in a massive hit on absolutely every
plugin directory of six to seven stat operations per module (that is
excluding searches for parent modules), ".pyc", ".pyo", ".so"...
... "__pycache__/*.pyo" and so on.

## 21aug2018

There is absolutely no automated testing methodology in place.

This is unacceptable for a large project written in a weakly-typed language.

Therefore, a unit test has been added that dynamically walks the entire
jumpscale object tree, looking for all functions in all objects starting
with the word "test".

If simply accessing the test fails (due to a parent object further down the
tree or a dependent object initialisation causing an exception), an
"error" test is dynamically added that will report the exception during
the actual test.

If there are no exceptions caused just by accessing the object, the
test function is added to the TestJSDynamicWalkerTestSearch class
so that it will be called later.

Tests that are to be skipped can be added, as long as a bugreport
is also filed and the bugreport link listed in the unit test.

see tests/jumpscale_test/test09_js_dynamic_walker.py for details.
