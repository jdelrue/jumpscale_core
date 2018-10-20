# Logging (OUTDATED)

When you create a new module in Jumpscale add a `logger` in the module using `j.logger.get("module_name")` and use the proper verb when logging.

Example:

```python
class MyModule:
  self.logger = j.logger.get('j.tools.mymodule')

 def foo(self):
   # do something
   self.logger.debug("trace something")
   self.logger.info("notify normal execution")
   self.logger.warn("something fishy happend but I can continue")
   self.logger.error("error happend, stop execution")
   self.logger.critical("this is really bad. probably should raise exception")
```

# How it works

Jumpscale use the standard Python logging module.

Logging modules organize the logger in a hierarchy based on their name. The root logger of Jumpscale is called `j`.

When you need to log something in a module make sure you get a logger instance using `j.logger.get(name)`. The name should start with `j` in order for the logger to inheriht the properties defined in the root logger.<br>
A good practice is to use the same name as the jslocation of the module itself. So if you're module is plugged to `j.tools.mymodule`, you probably want to get a logger with the name `j.tools.mymodule` too.

This organization is useful when an application uses Jumpscale and wants to have control on what logs get be printed or saved.

See handlers and filter for more informations:

- Handlers: <https://docs.python.org/3/howto/logging.html#handlers>
- Filter: <https://docs.python.org/3/library/logging.html#filter-objects>

# Example
```python
from Jumpscale import j

class TestLog(object):
    def __init__(self):
        self.__jslocation__ = "j.testlog"
        self.logger = j.logger.get('j.testlog')

    def foo(self):
        path = "/tmp/empty"
        self.logger.info("start foo method")
        if j.sal.fs.exists(path):
            self.logger.debug("%s exists, remove it" % path)
            j.sal.fs.remove(path)
        j.sal.fs.createEmptyFile(path)
        self.logger.info("end foo method")
        self.logger.error("BIG ERROR !!!")

j.logger.loggers_level_set(level='INFO')
j.testlog.foo()
```

The output of the `foo()` method of this simple `TestLog` class will be:

- In the console (in a real terminal you would even see nice coloring):

  ```
  [Wed30 05:50] - /opt/jumpscale//lib/Jumpscale/baselib/testlog/Testlog.py:12 - INFO     - start foo method
  [Wed30 05:50] - /opt/jumpscale//lib/Jumpscale/baselib/testlog/Testlog.py:17 - INFO     - end foo method
  [Wed30 05:50] - /opt/jumpscale//lib/Jumpscale/baselib/testlog/Testlog.py:18 - ERROR    - BIG ERROR !!!
  ```

  
# Configuration

Logging configuration is located by default in jumpscale config file (`/root/jumpscale/cfg/jumpscale.toml`).  
If the logging section doesn't exist in your config file, you can add it yourself.

There are 3 options you can configure.


- **level**: the minimum level of logging you want to see output to the console.
- **filter**: Filter is a list of logger name you want to filter out. Jumpscale is a big framework and console output can quickly become to verbose. Use this filter list to remove some of the module you don't want to see logged on the console. This filter only concern the console handler, log file will always contains logs from all modules.
- **exclude**: list of logger name you want to exclude from logs
- **enabled**: if false loging will be turned off

## Example logging configuration:

```toml
[logging]
filter = ["*"]
exclude = ["sal.fs"]
level = 20
enabled = true
```
