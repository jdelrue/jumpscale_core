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

    __jscorelocation__ = "j.core.dirs"

    def __init__(self,j):
        ''' jumpscale sandbox base folder
        '''
        self._j = j
        self.reload()


    def reload(self):
        """ loads the environment (NOTE: does not clear out the old environment)
            from the config file [dirs] section.
        """
        dirs = self._j.core.config["dirs"]
        for key, val in dirs.items():
            self.__dict__[key] = val
            os.environ[key] = val


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
        if self._j.sal.fs.isFile(path):
            paths = [path]
        else:
            paths = self._j.sal.fs.listFilesInDir(path, recursive, filter)

        for path in paths:
            content = self._j.sal.fs.fileGetContents(path)
            content2 = self.replace_txt_dir_vars(content, additional_args)
            if content2 != content:
                self._j.sal.fs.writeFile(filename=path, contents=content2)

    def __str__(self):
        out = ""
        for key, value in self.__dict__.items():
            if key[0] == "_":
                continue
            out += "%-20s : %s\n" % (key, value)
        out = self._j.core.text.sort(out)
        return out

    __repr__ = __str__
