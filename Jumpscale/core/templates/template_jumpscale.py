
# from Jumpscale.core.JSBase import JSBase
import os
import sys
from Jumpscale import j

{% for syspath in md.syspaths %}
if "{{syspath}}" not in sys.path:
    sys.path.append("{{syspath}}")
{%- endfor %}


{% for jclass in md.jclasses %}
class {{jclass.name}}():
    def __init__(self):
        pass

        {% for module in jclass.jsmodules %}
        self._{{module.jname}} = None
        {%- endfor %}

    {% for module in jclass.jsmodules %}
    @property
    def {{module.jname}}(self):
        if self._{{module.jname}} is None:
            print("LOAD:{{module.name}}")
            from {{module.importlocation}} import {{module.name}} as  {{module.name}}
            print("RUN:{{module.name}}")
            self._{{module.jname}} =  {{module.name}}()
        return self._{{module.jname}}
    {%- endfor %}

{{jclass.jdir}} = {{jclass.name}}()
{% endfor %}

