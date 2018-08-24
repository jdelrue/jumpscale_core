# JSLoader

Please note: this document has been partly superceded by 
[Dynamic Jumscale Loading](../Internals/dynamicloading.md)

"j.tools.jsloader.generate()" has now been replaced with
"j.tools.jsloader.generate\_json()", which can also take an
extra argument to generate *only* the JSON file for a specific
plugin.  This is best exclusively used in the setup.py script.
The concept mirrors that of the standard python ".pth" scheme,
found in each location of sys.path

## Introduction

**j** namespace was made to provide jumpscale modules with no need to import anything or to know how does these modules comunicate,
It also make it much easyer to add new module from your own repo  
what JSLoader provides is a service to collect all modules and plugins needed and make it available through **j**

### Example

```python
j.secondary_namespace.module...
```

### How to

To add new module to be loaded by the JSLoader:

* create your module
* add \_\_jslocation** field to your factory like ```self.**jslocation\_\_ = "j.clients.newclient"```
* add your new module to Jumpscale configurations:
  you can do this manually by adding your new module to jumpscale.toml file located in `<host_dir>/cfg/jumpscale.toml` in plugins section
  **or** you can do this using js_shell like this
  ```python
  plugins = j.core.state.configGet('plugins')
  plugins["pluginName"] = "plugin/path"
  j.core.state.configSet('plugins',plugins)
  ```
  **Note:** plugin name should contain "_Jumpscale_"
* run `js_init` or from jumpscale call `j.tools.JSloader.generate()`

### Add new secondary namespace

to add new secondary namespace like `j.secondary_namespace` you will need to add new field to Jumpsacle9 class in `core/Jumpscale/__init__.py`

### Restrictions

* Module path should contain "_jumpscale_"
* Class file name can't start with '\_', lower case letter, 'jsloader' or
  'actioncontroller'
