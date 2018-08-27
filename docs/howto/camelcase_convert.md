# Converting all code to camel_case with automated tools

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

# Identifying the places where functions are called *from*

This is harder, and involves running the modified trace program.
A second way may also involve dynamically patching the JSBase class
to identify functions (through the overload of __getattribute__
which is already present).

# Modifying the code

This is the third phase, that has yet to be done.  It involves reading
the trace output and matching it with the list of functions that need
to be replaced with camel_case versions.

However, given that this is such a big change it needs to be done
*synchronously* i.e. all work must **STOP** whilst **ALL** functions
are changed across **ALL** libraries.

It may actually be safer to have a transition system, hooking into
__getattribute__, where functions in the camelcase list are identified
at runtime, warnings issued, and a "dynamic" substitute carried out.
This needs some more thought.
