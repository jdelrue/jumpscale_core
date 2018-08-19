import os
from pathlib import Path


# def pathToUnicode(path):
#     """
#     Convert path to unicode. Use the local filesystem encoding. Will return
#     path unmodified if path already is unicode.
#
#     @param path: path to convert to unicode
#     @type path: basestring
#     @return: unicode path
#     @rtype: unicode
#     """
#     if isinstance(path, str):
#         return path
#
#     return path.decode(sys.getfilesystemencoding())

class Dirs(object):
    """ Utility class to configure and store all relevant directory paths
    """

    __jslocation__ = "j.core.dirs"

    def __init__(self):
        ''' jumpscale sandbox base folder
        '''
        self.reload()
        self._TEMPLATEDIR = None
        self._JSAPPSDIR = None
        self._templatedir_set = False
        self._jsappsdir_set = False

    def reload(self):
        """ loads the environment (NOTE: does not clear out the old environment)
            from the config file [dirs] section.
        """
        # when bootstrapping there *is* no config entry [dirs], consequently
        # an exception is attempted to be raised... but exceptions aren't
        # set up either!  this is called very very early.
        if self.j.core.state.configExists("dirs"):
            dirs = self.j.core.state.configGet("dirs")
        else:
            dirs = {}

        for key, val in dirs.items():
            self.__dict__[key] = val
            os.environ[key] = val

    @property
    def JSAPPSDIR(self):
        if self._jsappsdir_set:
            return self._JSAPPSDIR
        return self.VARDIR + "/apps/"

    @JSAPPSDIR.setter
    def JSAPPSDIR(self, d):
        self._JSAPPSDIR = d
        self._jsappsdir_set = True

    @property
    def TEMPLATEDIR(self):
        if self._templatedir_set:
            return self._TEMPLATEDIR
        return self.VARDIR + "/templates/"

    @TEMPLATEDIR.setter
    def TEMPLATEDIR(self, d):
        self._TEMPLATEDIR = d
        self._templatedir_set = True

    def replace_txt_dir_vars(self, txt, additional_args={}):
        """
        replace $BASEDIR,$VARDIR,$JSCFGDIR,$bindir,
                $codedir,$tmpdir,$logdir,$appdir with props of
        this class also the Dir... get replaces e.g. varDir
        @param   txt:             Text to be replaced
        @type    txt:             string
        @param   additional_args: Specify more variables and their
                values to be replaced in the path
        @type    additional_args: dict
        @return: string with replaced values
        """

        for key, val in self.__dict__.items():
            if "DIR" in key:
                txt = txt.replace("$%s" % key, val)

        # for backwardscompatibility
        txt = txt.replace("$TMPLSDIR", self.TEMPLATEDIR)
        txt = txt.replace("$CODEDIR", self.CODEDIR)
        txt = txt.replace("$VARDIR", self.VARDIR)
        txt = txt.replace("$CFGDIR", self.CFGDIR)
        txt = txt.replace("$BINDIR", self.BINDIR)
        txt = txt.replace("$LOGDIR", self.LOGDIR)
        txt = txt.replace("$TMPDIR", self.TMPDIR)
        txt = txt.replace("$JSLIBDIR", self.JSLIBDIR)
        txt = txt.replace("$JSAPPSDIR", self.JSAPPSDIR)

        for key, value in list(additional_args.items()):
            txt = txt.replace("$%s" % key, str(value))
        return txt

    @property
    def JSLIBDIR(self):
        """
        Returns location of Jumpscale library
        """
        return self.j.sal.fs.getParent(
            self.j.sal.fs.getDirName(
                self.j.sal.fs.getPathOfRunningFunction(
                    self.j.logger.__init__)))

    def replace_files_dir_vars(
            self,
            path,
            recursive=True,
            filter=None,
            additional_args={}):
        """
            Replace JumpScale directory variables in path with their
            values from this class

            @param path:            Could be either path to file or directory
            @type  path:            string
            @param recursive:       If True will search recursively
                                    in all subdirectories
            @type  recursive:       boolean
            @param filter:          unix-style wildcard (e.g. *.py) -                                               this is not a regular expression
            @type  filter:          string
            @param additional_args: Specify more variables and their
                                    values to be replaced in the path
            @type  additional_args: dict
        """
        if self.j.sal.fs.isFile(path):
            paths = [path]
        else:
            paths = self.j.sal.fs.listFilesInDir(path, recursive, filter)

        for path in paths:
            content = self.j.sal.fs.fileGetContents(path)
            content2 = self.replace_txt_dir_vars(content, additional_args)
            if content2 != content:
                self.j.sal.fs.writeFile(filename=path, contents=content2)

    def __str__(self):
        out = ""
        for key, value in self.__dict__.items():
            if key[0] == "_":
                continue
            out += "%-20s : %s\n" % (key, value)
        out = self.j.data.text.sort(out)
        return out

    __repr__ = __str__
