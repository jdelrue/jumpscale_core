# Jumpscale At The Command Line

Jumpscale offers the following command line tools:

 * [jsdocker](##jsdocker)
 * [jscode](##jscode)
 * [jsdesktop](##jsdesktop)
 * [jsnode](##jsnode)


## ays
Wrapper to Jumpscale's **At Your Service** tool.

```
Usage: ays [OPTIONS] COMMAND [ARGS]...

Options:
  --nodebug  disable debug mode
  --help     Show this message and exit.

Commands:
  blueprint      will process the blueprint(s) pointed to it...
  commit         commit the changes in the ays repo to git,...
  destroy        reset in current ays repo all services &...
  do             call an action (which is a method in the...
  init           ==== BASE ==== when using data the data is...
  install        make it reality if you want more finegrained...
  list           The list command lists all service instances...
  runinfo        print info about run, if not specified will...
  setstate       be careful what you do with this command this...
  showactions    shows all services with relevant actions
  showparents    Display the list of parent of a specific...
  showproducers  find the producers for this service & show
  simulate       is like do only does not execute it, is ideal...
  state          Print the state of the selected services.
  test           there is a test suite for ays, this command...
  uninstall      do uninstall
  update         update the metdata for the templates as well...
```

## jsdocker
Wrapper to Docker to do Docker operations.

```bash
Usage: jsdocker [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  commit
  create
  destroy
  destroyall
  execute
  exporttgz
  getip
  importrsync
  list
  pull
  push
  resetdocker
  restart
  start
  stop
```

## jscode
Wrapper to Git to do operations on multiple repositories.

```
Usage: jscode [OPTIONS] ACTION

Options:
  -n, --name TEXT           name or partial name of repo, can also be comma
                            separated, if not specified then will ask, if '*'
                            then all.
  --url TEXT                url
  -m, --message TEXT        commit message
  -b, --branch TEXT         branch
  -a, --accounts TEXT       comma separated list of accounts, if not specified
                            then will ask, if '*' then all.
  -u, --update TEXT         update merge before doing push or commit
  -f, --force TEXT          auto answer yes on every question
  -d, --deletechanges TEXT  will delete all changes when doing update
  -o, --onlychanges TEXT    will only do an action where modified files are
                            found
  --help                    Show this message and exit.

Actions:
  get
  commit
  push
  update
  status
  list
  init
  ```

## jsdesktop
Wrapper to Remote Desktop Protocol (RDP).

```
usage: jsdesktop [OPTIONS] COMMAND

Options:
  -n, --name NAME             desktop nr or name
  -d, --desktop               opendesktop
  -p, --passwd PASSWD         password for desktop

  --help                      Show this help message and exit

Commands:
  ps
  new
  list
  killall
  delete
  configure
  rdp
  userconfig
```

## jsnode
Wrapper to list and manage nodes in a G8 grid.

```
usage: jsnode [OPTIONS] COMMAND

Options:
  -h, --help                   Show this help message and exit
  -nid, --nodeid NID       Ex: -nid=1(note the = sign)
  -gid, --gridid GID       Filter on grid used for list
  --roles ROLES            Used with addrole or deleterole. ex: --roles=node,computenode.kvm(note the = sign). List is comma seperated

  --help                      Show this help message and exit

Commands:
  delete
  list
  enable
  disable
  addrole
  deleterole
```
