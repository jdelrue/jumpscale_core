# Converting all code to snake_case with automated tools

Python is a dynamic weakly-typed language.  Therefore it is completely
unsafe and near impossible to do static conversion of function names
without causing damage, and at the same time, with over 450 identified
functions to change it would be almost impossible to do in a reasonable
timeframe (and without introducing errors).

Replacing strings arbitrarily is also unsafe: again because python is
weakly-typed it is impossible to know if any one string happens to be
used by a 3rd party module or if it is actually a function that is
to be changed.

The only safe way to find out the types of the objects is to actually
run the code.  That in turn means that "tracing" has to be carried out.
However, the standard python "trace" module does not show line numbers,
so a modified version has been placed into the js_convert repository
that does:

    git clone https://github.com/threefoldtech/js_convert.git

# Identifying the functions to be replaced

To actually identify the functions that need replacing, a tool has
been written based on lib2to3, called "lib3to3", which parses the python
program looking for patterns of the following type:

    class Classname(....)

        def functionName(....) <----

only functions in a class in a module that are of the type functionNameCapitals
will be tagged and outputted into a file called camelcase_fns.txt, in the
format "Module.Class.Function", one per line.

As this is, at the time of writing, a prototype tool, modify the
actual code in lib3to3.py, to change action_camel_case to False in order
to get the list of functions.  Then, run it as:

    $ lib3to3 /home/jumpscale_core/

A file camelcase_fns.txt will either be created or appended to (it will
*NOT* be deleted, ever), such that the tool may be run on multiple
subdirectories consecutively in order to collate multiple results.

# Fixing callees

This is the second phase.  Once the functions to be transformed have
been identified, **REVIEW THEM** and select only the ones that are
to be modified, by editing camelcase_fns.txt.

Then, modify the lib3to3 source to put the following lines in:

    config_info.action_camel_case = True
    config_info.check_camel_case = False
    fixname = 'camelcaseinkls'

Run lib3to3 again to actually have it change (only) the function names
listed in camelcase_fns.txt

# Identifying the places where functions are called *from*

This is harder, and involves dynamically patching the JSBase class
to identify functions (through the overload of __getattr__).

## "Live" introspection

Ok so after evaluating the alternative (dynamic substitute) it was decided
to add a JSBase.__getattr__ which does live detection of whether a
function is being called as snake_case or camelCase.  The live detection
allows the callee to be converted to camelCase, and if the CALLER
happens to accidentally use snake_case, log that fact, and return the
**CAMELCASED** version of the function **TRANSPARENTLY**.

This allows applications to keep on working and to transition safely
over to camelCase, without a total drastic shutdown of all development.
# Modifying the code

## Running the live detector

This is very straightforward: simply run a program (interactive or
non-interactive, it does not matter which), and a file named
"camel_case_log.txt" will be created (or appended to: it will *NOT*
be deleted, ever), containing information in the following format:

    abscallepath:linenum:module <TAB> CalledModule:CalledClass:called_function

The trace output contains the name of the file and the line number from
where a snake_case function was called *FROM*.  This is the critical
information that is extremely difficult to get hold of in a static
analysis system of a dynamic programming language like python.  The module
is included just for visual convenience, strictly speaking.

The CalledModule, CalledClass and called_function match up precisely with
the information gathered from the static analysis carried out in the
previous phase.  This is (will be) how the *callers* will be correctly
modified (without accidentally changing completely the wrong e.g. third
party function).

**PLEASE NOTE** - this is not entirely fool-proof.  Python can only identify
LINE numbers at runtime, it cannot identify WHERE in the line the call is
made from.  So if there are multiple functions with the exact same name,
one is in a Jumpscale module and one is in a 3rd party library, on the
SAME line number, **BOTH** will end up being converted.

# Fixing callers

This is the fourth phase.  It involves reading the trace output and matching
it with the list of functions that need to be replaced with camelCase versions.

Taking the trace-log output from camel_case_log.txt and placing it in
the same directory as lib3to3.py, return to the lib3to3.py source and
ensure that the following settings are in place:

    config_info.action_camel_case = True
    config_info.check_camel_case = True
    fixname = 'camelcasecallers'

Then, re-run the tool.  It will use lib2to3 to go through every single line,
searching for a match on any recorded use of a snake_case function call
that had been detected by the live trace system.

Note that the detection matches not on the full path, but on the "Jumpscale"
library path.  So **only** files which are of the form Jumpscale/core/State.py
or DigitalMeLib/xxxx/yyy.py will be converted.

On encountering a line with a function call that is known to be snake_case,
a basic sanity check is performed (NOTE, this is NOT a sophisticated check),
as to whether the function name matches (and only the function name).
No filtering is carried out.

If the function name matches, it is converted in-place to camelCase.
