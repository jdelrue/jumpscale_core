
from jumpscale import j
import sys
import inspect

JSBASE = j.application.jsbase_get_class()
class ZeroRepo(JSBASE):

    def __init__(self,path,gitrepo):
        JSBASE.__init__(self)
        self.path=path
        self.gitrepo=gitrepo




    



class ZeroRepos(JSBASE):
    def __init__(self):
        JSBASE.__init__(self)
        self.repos = {}

    def load(self, path=None,repo=None):
        if path is None:
            repos = j.clients.git.getGitReposListLocal()
            for key, repo in repos.items():
                if key.startswith("zerorobot"):
                    self.load(repo=repo,path=repos[key])
        else:
            from IPython import embed;embed(colors='Linux')
            self.repos[name] = ZeroRepo(path=path,gitrepo=repo) 

    def __iter__(self):
        return self.repos.__iter__()

