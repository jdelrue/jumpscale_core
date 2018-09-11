
from Jumpscale import j
import sys
import inspect


# TemplateCollectionClass= j.tools.zerorobot.models.TemplateCollection
# TemplateModelClass= j.tools.zerorobot.models.TemplateModel
JSBASE = j.application.JSBaseClass
class ZeroTemplate(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)

import time
def our_decorator(func):
    def function_wrapper(x):
        print("Before calling " + func.__name__)
        func(x)
        print("After calling " + func.__name__)
    return function_wrapper

def retry(func):
    def function_wrapper(x):
        print("retry " + func.__name__)
        while True:
            try:
                func(x)
            except Exception as e:
                print ("ERROR:%s"%e)
        print("retry " + func.__name__)
    return function_wrapper


class ZeroTemplates(JSBASE):
    def __init__(self):
        #is executed after the __init__ of the superclass
        JSBASE.__init__(self)
        self.__templateTmpDir=None

    @property
    def _templateTmpDir(self):
        if self.__templateTmpDir==None:
            self.__templateTmpDir=j.dirs.TMPDIR+"/actions"
            j.sal.fs.createDir(self.__templateTmpDir)
            if self.__templateTmpDir not in sys.path:
                sys.path.append(self.__templateTmpDir)
            j.sal.fs.touch(self.__templateTmpDir+"/__init__.py")
        return self.__templateTmpDir


    def load(self, path=None,repo=None):
        for repo in j.tools.zerorobot.repos:
            repo.templatesLoad()

    def _checkConfig(self,config):
        good=["recurring","log","job","timeout_policy"]
        for key,val in config.items():
            if key not in good:
                raise j.exceptions.Input("Cannot parse config, key '%s' in dict unknown, needs to be in %s"%(key,good))
        return config



    def _parse(self,code): #DO NOT TRY OTHER METHODS PLEASE, its easiest to do believe me (despiegk)
        state="start"
        out=""
        doc=""
        config=""
        for line in code.split("\n"):
            linestrip=line.strip()

            # print("state:%s '%s'"%(state,linestrip))

            if state=="start" and linestrip.startswith("def"):
                state="method"
                continue

            if state=="method":
                if linestrip.startswith("```") or linestrip.startswith("'''") or linestrip.startswith("\"\"\""):
                    state="doc"
                    continue

            if state=="doc" and (linestrip.startswith("config=") or linestrip.startswith("config =")):
                state="config"
                continue

            if state=="doc":
                if linestrip.startswith("```") or linestrip.startswith("'''") or linestrip.startswith("\"\"\""):
                    state="end"
                    continue
                else:
                    doc+=line+"\n"

            if state=="config":
                if line.strip().startswith("```") or line.strip().startswith("'''"):
                    state="doc"
                    continue
                else:
                    config+=line+"\n"

            if state in ["end","method"]:
                out+=line+"\n"

        out=j.core.text.strip(out)
        doc=j.core.text.strip(doc)
        config=j.core.text.strip(config)
        
        if config.strip()!="":
            try:
                config2= j.data.serializers.yaml.loads(config)
            except Exception as e:
                raise j.exceptions.Input("Cannot parse config out of method:%s\n%s"%(code,e))
            try:
                config2=self._checkConfig(config2)
            except Exception as e:
                raise j.exceptions.Input("Cannot parse config out of method:%s\n%s"%(code,e))
        else:
            config2={}
        return out,doc,config2
        


    def _loadTemplate(self, repo,path):
        if not [j.sal.fs.getBaseName(item) for item in j.sal.fs.listFilesInDir(path,False,filter="*.py")] == ["actions.py"]:
            raise j.exceptions.Input("Cannot find actions.py file, or too many python files")
        tpath=path+"/actions.py"
        name=j.sal.fs.getBaseName(path).replace(".","_")
        dpath=self._templateTmpDir+"/actions_%s.py"%name
        j.sal.fs.copyFile(tpath,dpath)
        Name=name[0].upper()+name[1:]
        exec("from actions_%s import Template as %s"%(name,Name))
        cl=eval("%s()"%(Name))
        cl.start()
        from IPython import embed;embed(colors='Linux')

        # for name,method in inspect.getmembers(cl, predicate=inspect.ismethod):
        #     code=inspect.getsource(method.__func__)
        #     try:
        #         code,doc,config=self._parse(code)
        #     except Exception as e:
        #         raise j.exceptions.Input("Cannot parse method:%s in path:%s\n%s"%(name,path,e))     

        # from IPython import embed;embed(colors='Linux')       
            
        # gitrepo=j.clients.git.get(repo)
        # key="%s/%s"%(gitrepo.unc,name)
        # from IPython import embed;embed(colors='Linux')
        # templNew = ZeroTemplate(key,new=True,collection=self)
        # templ._loadFromPath(path)
