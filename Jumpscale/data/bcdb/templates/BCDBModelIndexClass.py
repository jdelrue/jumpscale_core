from Jumpscale import j
#GENERATED CODE, can now change

{%- if index.enable %}
from peewee import *
{%- endif %}


class {{BASENAME}}:

    def _init_index(self):
        pass #to make sure works if no index
        {%- if index.enable %}
        self.logger.info("init index:%s"%self.schema.url)

        db = self.bcdb.sqlitedb
        print(db)

        class BaseModel(Model):
            class Meta:
                print("*%s"%db)
                database = db

        class Index_{{schema.key}}(BaseModel):
            id = IntegerField(unique=True)
            {%- for field in index.fields %}
            {{field.name}} = {{field.type}}(index=True)
            {%- endfor %}

        self.index = Index_{{schema.key}}
        self.index.create_table(safe=True)

        {%- endif %}

    {% if index.enable %}
    def index_set(self,obj):
        idict={}
        {%- for field in index.fields %}
        {%- if field.jumpscaletype.NAME == "numeric" %}
        idict["{{field.name}}"] = obj.{{field.name}}_usd
        {%- else %}
        idict["{{field.name}}"] = obj.{{field.name}}
        {%- endif %}
        {%- endfor %}
        idict["id"] = obj.id
        if not self.index.select().where(self.index.id == obj.id).count()==0:
            #need to delete previous record from index
            self.index.delete().where(self.index.id == obj.id).execute()
        self.index.insert(**idict).execute()

    {% endif %}
