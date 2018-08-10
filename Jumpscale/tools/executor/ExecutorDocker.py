"Docker executor"
import uuid
import os
from io import BytesIO
from tarfile import TarFile, TarInfo
from jumpscale import j
import docker
from docker.models.containers import Container
from .ExecutorBase import ExecutorBase


class ExecutorDocker(ExecutorBase):
    "Docker executor"

    def __init__(self, container, debug=False, checkok=True):

        ExecutorBase.__init__(self, debug=debug, checkok=checkok)

        if not isinstance(container, Container):
            raise ValueError(
                "Expected container variable as instance of running docker container")

        # Check if docker container is running and if the base image has bash
        # installed
        result = container.exec_run('bash -c "echo test"')
        if result.exit_code != 0:
            raise ValueError(
                "Container does not have bash installed! Need bash for using prefab")
        self.container = container
        self.type = "docker"

        self._id = None

        self._logger = j.logging.get("executordocker%s" % self.container.id)

    @classmethod
    def from_local_container(cls, id_or_name):
        """
        Creates docker executor of provided docker id/name

        @param id_or_name: id or name of docker container
        @raise keyError: container with id/name was not found
        @return: ExecutorDocker
        """
        dockerd = docker.from_env()
        for con in dockerd.containers.list():
            if id_or_name in (con.id, con.name):
                return cls(con)
        raise KeyError(
            "Container with id or name '%s' not found!" %
            id_or_name)

    @property
    def logger(self):
        """
        Returns the logger

        @return: logger
        """

        return self._logger

    def exists(self, path):
        """
        Checks if path exists

        @return: path exists bool
        """
        result = self.container.exec_run('bash -c "test -e %s"' % path)
        if result.exit_code > 0:
            return False
        else:
            return True

    @property
    def id(self):
        """
        Returns docker id

        @return: docker id
        """

        return self.container.id

    def file_read(self, path):
        """
        Read a file in the container

        @param path: path of the file on the container to read
        @return: bytes (utf8) of content
        """

        file_name = os.path.basename(path)
        data, _ = self.container.get_archive(path)
        buf = BytesIO()
        for chunk in data:
            buf.write(chunk)
        buf.seek(0)
        with TarFile(mode='r', fileobj=buf) as tarf:
            for tari in tarf:
                if tari.name == file_name:
                    reader = tarf.extractfile(tari)
                    return reader.read().decode("utf8")

    def file_write(
            self,
            path,
            content,
            mode=None,
            owner=None,
            group=None,
            append=False,
            hide=False,
            sudo=False):
        """
        Writes a file to the container

        @param path: path of the file
        @param content: content to be put in the file
        @param mode: file mode
        @param owner: owner of the file
        @param group: group of the file
        @param append: append content to the file
        @param hide: hide (debug) logs
        @raise runtimeError: path for file couldn't be created
        """
        if append and self.exists(path):
            content = self.file_read(path) + content
        file_name = os.path.basename(path)
        dir_name = os.path.dirname(path)
        buf = BytesIO()
        with TarFile("write_file", mode='w', fileobj=buf) as tarf:
            f = BytesIO()
            length = f.write(content.encode('utf8'))
            f.seek(0)
            tari = TarInfo(name=file_name)
            tari.size = length
            if mode is not None:
                tari.mode = mode
            if owner is not None:
                tari.uname = owner
            if group is not None:
                tari.gname = group
            tarf.addfile(tari, f)
        if not self.exists(dir_name):
            result = self.container.exec_run("mkdir -p %s" % dir_name)
            if result.exit_code != 0:
                raise RuntimeError(
                    "Could not create path %s!\n%s" %
                    (dir_name, result.output))
        self.container.put_archive(dir_name, buf.getvalue())

    def executeRaw(self, cmd, die=True, showout=False):
        """
        Raw execution of command in container

        @param cmd: command to be executed
        @param die: die on error
        @param showout: enable logger
        @return: exit code, output, error output
        @raise runtimeError: output in stderr and die is True
        """
        cmd_file = j.sal.fs.joinPaths("/", str(uuid.uuid4()))
        try:
            self.file_write(cmd_file, cmd)
            result = self.container.exec_run('bash -c "bash %s 2> %s.stderr"' %
                                             (cmd_file, cmd_file))
            output = result.output.decode("utf8")
            err_output = self.file_read("%s.stderr" % cmd_file)
            if die and result.exit_code != 0:
                raise RuntimeError(
                    "Error in:\n%s\n***\n%s\n%s" %
                    (cmd, output, err_output))
            if showout:
                self.logger.info(output)
                if err_output:
                    self.logger.info(err_output)
            return result.exit_code, output, err_output
        finally:
            self.container.exec_run(
                'bash -c "rm %s; rm %s.stderr"' %
                (cmd_file, cmd_file))

    def execute(self, cmds, die=True, checkok=False, showout=True, timeout=0, env=None,  # pylint: disable=R0913
                asScript=False, hide=False, sudo=False):  # pylint: disable=W0613
        """
        Executes command in container

        @param cmds: commands to be executed
        @param die: die on error
        @param checkok: feedback on success
        @param showout: enable logger
        @param timeout: timeout of execution (not implemented)
        @param env: sets environment variables
        @param asScript: execute as script
        @param hide: hide (debug) logs
        @return: exit code, output, error output
        """

        if hide:
            showout = False

        env = dict() if env is None else env
        # cmds2 = self._transformCmds(cmds, die, checkok=checkok, env=env)

        # online command, we use prefab
        if showout:
            self.logger.info("EXECUTE %s %s" % (self.id, cmds))
        else:
            if not hide:
                self.logger.debug("EXECUTE %s %s" % (self.id, cmds))

        exit_code, out, err = self.executeRaw(cmds, die=die, showout=showout)

        if hide is False:
            self.logger.debug("EXECUTE OK")

        if checkok and die:
            out = self.docheckok(cmds, out)

        return exit_code, out, err

    def upload(
            self,
            source,
            dest,
            dest_prefix="",
            recursive=True,
            createdir=True,
            rsyncdelete=True,
            ignoredir=None,
            keepsymlinks=False):
        """
        Uploads file to container

        @param source: file to be uploaded
        @param dest: destination of file on container
        @param dest_prefix: path prefix
        @param recursive: upload source recursively
        @param createdir: create dir if not exists
        @param rsyncdelete: rsyncdelete
        @param ignoredir: dirs ignored uploading
        @param keepsymlinks: keep symbolic links
        """

        if ignoredir is None:
            ignoredir = ['.egg-info', '.dist-info', '__pycache__', ".git"]

        if dest_prefix != "":
            dest = j.sal.fs.joinPaths(dest_prefix, dest)
        if dest[0] != "/":
            raise j.exceptions.RuntimeError("need / in beginning of dest path")
        tmpdir = j.sal.fs.joinPaths("/tmp", str(uuid.uuid4()))
        try:
            j.sal.fs.copyDirTree(
                source,
                tmpdir,
                keepsymlinks=keepsymlinks,
                deletefirst=False,
                overwriteFiles=True,
                ignoredir=ignoredir,
                ignorefiles=[".egg-info"],
                rsync=True,
                ssh=False,
                recursive=recursive,
                createdir=True,
                rsyncdelete=rsyncdelete)
            archiveid = str(uuid.uuid4())
            j.sal.process.execute(
                "tar -cvf %s.tar *" %
                archiveid, showout=False, cwd=tmpdir)
            with open(j.sal.fs.joinPaths(tmpdir, "%s.tar" % archiveid), 'rb') as fileh:
                data = fileh.read()
            if createdir:
                self.executeRaw("mkdir -p %s" % dest)
                self.container.put_archive(dest, data)
        finally:
            j.sal.fs.removeDirTree(tmpdir)

    def download(self, source, dest, source_prefix="", recursive=True):
        """
        Downloads a file to container

        @param source: file to be downloaded
        @param dest: destination of file on locally
        @param source_prefix: path prefix
        @param recursive: download source recursively
        """

        if source_prefix != "":
            source = j.sal.fs.joinPaths(source_prefix, source)
        if source[0] != "/":
            raise j.exceptions.RuntimeError(
                "need / in beginning of source path")
        tmptar = j.sal.fs.joinPaths("/tmp", "%s.tar" % str(uuid.uuid4()))
        tmpdir = j.sal.fs.joinPaths("/tmp", str(uuid.uuid4()))
        try:
            data, _ = self.container.get_archive(source)
            with open(tmptar, 'wb') as fileh:
                for chunk in data:
                    fileh.write(chunk)
            j.sal.process.execute(
                "tar -xvf %s" %
                tmptar, showout=False, cwd=tmpdir)
            j.sal.fs.copyDirTree(
                tmpdir,
                dest,
                keepsymlinks=True,
                deletefirst=False,
                overwriteFiles=True,
                ignoredir=[
                    ".egg-info",
                    ".dist-info"],
                ignorefiles=[".egg-info"],
                rsync=True,
                recursive=recursive)
        finally:
            j.sal.fs.remove(tmptar)
            j.sal.fs.removeDirTree(tmpdir)

    def __repr__(self):
        return "Executor docker: %s" % self.id

    __str__ = __repr__
