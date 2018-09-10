
# from Jumpscale.core.JSBase import JSBase
import os
import sys
from Jumpscale import j

{% for syspath in md.syspaths %}
if "{{syspath}}" not in sys.path:
    sys.path.append("{{syspath}}")
{%- endfor %}


{% for name, jsgroup in md.jsgroups.items() %}
class group_{{jsgroup.name}}():
    def __init__(self):
        pass

        {% for module in jsgroup.jsmodules %}
        self._{{module.jname}} = None
        {%- endfor %}

    {% for module in jsgroup.jsmodules %}
    @property
    def {{module.jname}}(self):
        if self._{{module.jname}} is None:
            print("LOAD:{{module.name}}")
            try:
                from {{module.importlocation}} import {{module.name}}
            except Exception as e:
                print ("COULD NOT IMPORT:{{module.jname}}")
                msg = "ERROR:%s"%e
                print(msg)
                return msg
            print("RUN:{{module.name}}")
            self._{{module.jname}} =  {{module.name}}()
        return self._{{module.jname}}
    {%- endfor %}

{{jsgroup.jdir}} = group_{{jsgroup.name}}()
{% endfor %}

