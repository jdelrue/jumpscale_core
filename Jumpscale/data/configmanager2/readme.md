



# how to create a configuration object


## How to enable a jumpscale module to have a secret config management
### Setup the factory
- Make you factory module inherits from the config manager base class, available at `j.tools.configmanager.base_class_configs`.
- set the `__jslocation__` on your factory class
- Call the constructor of the base class with as first argument, the Class of object that the factory produces (`super().__init__(MyModule)`)

### Setup the client class
- Define the template of your configuration. This template is a multi string representing a dictionary.  
You need to specified a default value for each key. The type of the value will be automatically deducted. The type per key will be remember and checked when updating the config. If you tried to set a value with a wrong type, an exception will be raised.  
If the key last end with an '_' then the value will always be encrypted.

- Make your child class inherits from the config manager base class, available at `j.tools.configmanager.base_class_config`
- Make your child class accept `instance, data={}, parent=None` as argument for its constructor
- call the constructor of the base class like this : `super().__init__(instance=instance, data=data, parent=parent,template=CONFIG_TEMPLATE)`


Example code:

```python
CONFIG_TEMPLATE = """
host = ""
port = 0
secret_ = ""
"""

JSConfigFactoryBase = j.tools.configmanager.base_class_configs
JSConfigClientBase = j.tools.configmanager.base_class_config

class MyModuleFactory(JSConfigFactoryBase):

    def __init__(self):
        # define the jslocation like any other js module
        self.__jslocation__ = "j.client.mymodule"
        
        # you need to call the constructor
        # of the base class to boostrap the config
        # by passing the Class this factory will instantiate
        super().__init__(MyModule)
    

class MyModule(JSConfigClientBase):

    def __init__(self, instance, data={}, parent=None):
        # configure the base class with the 
        # the instance name, the data of the config, 
        # the parent which is the factory class
        # and the template config
        super().__init__(instance=instance, data=data, parent=parent,template=CONFIG_TEMPLATE)
    
```
