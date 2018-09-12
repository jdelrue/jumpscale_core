""" a highly intrusive live introspection for camel_case transition (issue #105)

    this module contains a necessary way to **SAFELY** transition from
    camelCase to snake_case.  see docs/howto/camelcase_convert.md as it
    is quite involved.  static analysis alone is **NOT SAFE**.

    once (and only once) all conversions have been completed this module may
    be removed as a mix-in from JSBase.py
"""
import os
import inspect
import gc    # needed for camelcase
import trace # needed for camelcase


camel_case_log = {}

def load_camel_case_log():
    global camel_case_log
    if len(camel_case_log) > 0:
        return # loaded already
    try:
        with open("camel_case_log.txt") as f:
            for l in f.readlines():
                l = l.strip()
                (k, v) = l.split("\t")
                camel_case_log[k] = v
    except (OSError, IOError):
        pass # ok, ignore it.  empty.  first time loading

load_camel_case_log()

def save_camel_case_log_entry(k, v):
    global camel_case_log
    with open("camel_case_log.txt", "a+") as f:
        f.write("%s\t%s\n" % (k, v))

# this is taken straight out of the trace.py module
caller_cache = {}
def file_module_function_of(frame):

    global caller_cache

    code = frame.f_code
    filename = code.co_filename
    if filename:
        modulename = trace._modname(filename)
    else:
        modulename = None

    lineno = frame.f_lineno
    funcname = code.co_name
    clsname = None
    if code in caller_cache:
        if caller_cache[code] is not None:
            clsname = caller_cache[code]
    else:
        caller_cache[code] = None
        ## use of gc.get_referrers() was suggested by Michael Hudson
        # all functions which refer to this code object
        funcs = [f for f in gc.get_referrers(code)
                     if inspect.isfunction(f)]
        # require len(func) == 1 to avoid ambiguity caused by calls to
        # new.function(): "In the face of ambiguity, refuse the
        # temptation to guess."
        if len(funcs) == 1:
            dicts = [d for d in gc.get_referrers(funcs[0])
                         if isinstance(d, dict)]
            if len(dicts) == 1:
                classes = [c for c in gc.get_referrers(dicts[0])
                               if hasattr(c, "__bases__")]
                if len(classes) == 1:
                    # ditto for new.classobj()
                    clsname = classes[0].__name__
                    # cache the result - assumption is that new.* is
                    # not called later to disturb this relationship
                    # _caller_cache could be flushed if functions in
                    # the new module get called.
                    caller_cache[code] = clsname
    if clsname is not None:
        funcname = "%s.%s" % (clsname, funcname)

    return filename, lineno, modulename, funcname


#https://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545
def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        tmp = meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0]
        cls = getattr(inspect.getmodule(meth), tmp)
        if isinstance(cls, type):
            return cls
    # handle special descriptor objects
    return getattr(meth, '__objclass__', None)

def log_camel_case_found(obj, frame, attr, attrname):
    global camel_case_log
    (fname, lineno, modulename, funcname) = file_module_function_of(frame)
    while True:
        if funcname == 'JSBase.__getattr__' or \
            funcname == 'BaseGetter.__getattribute__':
            frame = frame.f_back
            (fname, lineno, modulename, funcname) = \
                        file_module_function_of(frame)
            continue
        break
    kls = get_class_that_defined_method(attr)
    report = "%s:%d:%s" % (fname, lineno, modulename)
    # TODO: this is where the warning has to be put.
    #print ("camel case found", report)
    if report in camel_case_log:
        return
    calledmodule = kls.__module__.split('.')[-1]
    called = "%s.%s.%s" % (calledmodule, kls.__name__, attrname)
    camel_case_log[report] = called
    save_camel_case_log_entry(report, called)

def _camel(s):
    return s != s.lower() and s != s.upper()

def camel(s):
    if not _camel(s):
        return False
    # exclude some outliers
    if s.startswith("__") and s.endswith("__"):
        return False
    if "_" not in s:
        return False
    if s.startswith("_") and "_" not in s[1:] and not camel(s[1:]):
        return False
    return True

def to_snake_case(not_snake_case):
    final = ''
    while not_snake_case.startswith("_"):
        final += "_"
        not_snake_case = not_snake_case[1:]
    for i in range(len(not_snake_case)):
        item = not_snake_case[i]
        if i < len(not_snake_case) - 1:
            next_char_will_be_underscored = (not_snake_case[i+1] == "_"  \
                    or not_snake_case[i+1] == " " \
                    or not_snake_case[i+1].isupper())
        if (item == " " or item == "_") and next_char_will_be_underscored:
            continue
        elif (item == " " or item == "_"):
            final += "_"
        elif item.isupper():
            final += "_"+item.lower()
        else:
            final += item
    return final

def camelCase(st):
    output = ''.join(x for x in st.title() if x.isalnum())
    return output[0].lower() + output[1:]


class CamelSnakeConvert:

    def __getattr__(self, attrname):
        """ issue #105 - okaay, so this where camelcase is to be detected,
            and if nonCamelCase is detected, a warning will be put on the
            console, the line number of the caller logged in a file, and
            the alternative (camel_case) function called instead.

            properties are *NOT* included, and are specifically detected
            and excluded by inspect.isdatadescriptor / isgetsetdescriptor

            the rules are:

            * convert CLASS METHODS ONLY (the callee).
              do NOT convert the caller... yet.
            * run a program (any program): warnings will be given,
              and also listed in a log file, along with the line numbers
              of where they were called FROM (callers).
            * run the automated tool <TBD> or just if feeling masochistic,
              edit the CALLERs by hands.

            do not do it the other way round: do NOT edit the callers
            first.  the code below is SPECIFICALLY designed to have
            CALLEEs be modified first.
        """
        # XXX not a good idea to do this.  once committed, REALLY have to
        # stick with it.
        #if not os.environ.get('CAMELCASECHECK'):
        #    return BaseGetter.__getattribute__(self, attrname)

        if not _camel(attrname): # it_was_one_of_these, it's_cool.
            return BaseGetter.__getattribute__(self, attrname)
        # so, it's a camelCaseThing. first try and get it *as* camelCase
        #print ("looking for", attrname)
        try:
            # ok try "snake" version...
            to_snake = to_snake_case(attrname)
            #to_camel = camelCase(attrname)
            #print ("looking for snake %s" % to_snake)
            attr = BaseGetter.__getattribute__(self, to_snake)
            if not inspect.ismethod(attr): # not a method
                return BaseGetter.__getattribute__(self, attrname)
            if isinstance(attr, property): # it's a property
                return BaseGetter.__getattribute__(self, attrname)
        except AttributeError:
            #print ("looking for %s failed, try %s" % (to_camel, attrname))
            return BaseGetter.__getattribute__(self, attrname)
        # ok that worked, so, hmmm, we should log finding the camel_case
        #print ("looking for %s worked" % to_camel)
        frame = inspect.currentframe().f_back # skip this __getattr__!
        log_camel_case_found(self, frame, attr, attrname)
        return attr

