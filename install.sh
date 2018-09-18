

die() {
    set +x
    rm -f /tmp/sdwfa #to remove temp passwd for restic, just to be sure
    echo
    echo "**** ERRORLOG ****"
    cat $LogFile
    echo
    echo "[-] something went wrong: $1"
    echo
    echo
    # set -x
    exit 1
}


Z_pushd(){
    echo "pushd to: $1" >> $LogFile
    pushd "$1" >> $LogFile 2>&1 || die "could not pushd to $1" || return 1
}

Z_popd(){
    popd > /dev/null || die "could not popd" || return 1
}

Z_mkdir(){
    echo "mkdir: $1" >> $LogFile
    mkdir -p "$1" >> $LogFile 2>&1 || die "could not mkdir $1" || return 1
}

Z_mkdir_pushd(){
    Z_mkdir "$1" || return 1
    Z_pushd "$1" || return 1
}

Z_brew_install(){
    echo "brew install: $@" >> $LogFile
    brew install  $@ >> $LogFile 2>&1 || die "could not brew install $@" || return 1
}

Z_apt_install(){
  echo "apt-get install: $@" >> $LogFile
  sudo apt-get -y install $@ >> $LogFile 2>&1 || die "could not install package $@" || return 1
}

Z_exists_dir(){
    if [ ! -d "$1" ]; then
        die "dir $1 not found" || return 1
    fi
}

Z_exists_file(){
    if [ ! -f "$1" ]; then
        die "file $1 not found" || return 1
    fi
}



ZCodeGetJSUsage() {
   cat <<EOF
Usage: ZCodeGet [-r reponame] [-g giturl] [-a account] [-b branch]
   -r reponame: name or repo which is being downloaded
   -b branchname: defaults to development_simple
   -h: help

check's out jumpscale repo to $CODEDIR/github/threefoldtech/$reponame
branchname can optionally be specified.

if specified but repo exists then a pull will be done & branch will be ignored !!!

if reponame not specified then will checkout
- lib
- core
- prefab

EOF
}

ZCodeGetJS() {
    echo FUNCTION: ${FUNCNAME[0]} >> $LogFile

    local OPTIND
    local account='threefoldtech'
    local reponame=''
    # local branch=${JUMPSCALEBRANCH:-development_simple} #this is being set elsewhere too
    [ -e $JUMPSCALEBRANCH ] && exit 1
    
    while getopts "r:b:h" opt; do
        case $opt in
           r )  reponame=$OPTARG ;;
           b )  branch=$OPTARG ;;
           h )  ZCodeGetJSUsage ; return 0 ;;
           \? )  ZCodeGetJSUsage ; return 1 ;;
        esac
    done

    if [ -z "$reponame" ]; then
        ZCodeGetJS -r jumpscale_core  -b $JUMPSCALEBRANCH || return 1
        ZCodeGetJS -r jumpscale_lib -b $JUMPSCALEBRANCH || return 1
        ZCodeGetJS -r jumpscale_prefab -b $JUMPSCALEBRANCH || return 1
        ZCodeGetJS -r 0-robot -b $JUMPSCALEBRANCH || return 1
        ZCodeGetJS -r digital_me -b $JUMPSCALEBRANCH || return 1
        ZCodeGetJS -r digital_me_recipes -b $JUMPSCALEBRANCH || return 1
        return 0
    fi

    # local giturl="git@github.com:Jumpscale/$reponame.git"
    local githttpsurl="https://github.com/threefoldtech/$reponame.git"

    # check if specificed branch or $JUMPSCALEBRANCH exist, if not then fallback to development_simple

    JUMPSCALEBRANCHExists ${githttpsurl} ${JUMPSCALEBRANCH} || JUMPSCALEBRANCH=development_simple
    JUMPSCALEBRANCHExists ${githttpsurl} ${JUMPSCALEBRANCH} || JUMPSCALEBRANCH=development

    echo "get code: ${githttpsurl} ${JUMPSCALEBRANCH}"

    # ZCodeGet -r $reponame -a $account -u $giturl -b $branch  || ZCodeGet -r $reponame -a $account -u $githttpsurl -b $branch || return 1
    ZCodeGet -r $reponame -a $account -u $githttpsurl -b $JUMPSCALEBRANCH || return 1

}

ZCodeGetUsage() {
   cat <<EOF
Usage: ZCodeGet [-r reponame] [-g giturl] [-a account] [-b branch]
   -t type: default is github but could be e.g. gitlab, ...
   -a account: will default to 'varia', but can be account name
   -r reponame: name or repo which is being downloaded
   -u giturl: e.g. git@github.com:mathieuancelin/duplicates.git
   -b branchname: defaults to development_simple
   -k sshkey: path to sshkey to use for authorization when connecting to the repository.
   -h: help

check's out any git repo repo to $CODEDIR/$type/$account/$reponame
branchname can optionally be specified.

if specified but repo exists then a pull will be done & branch will be ignored !!!

EOF
}
#to return to original dir do Z_pushd
ZCodeGet() {
    echo FUNCTION: ${FUNCNAME[0]} > $LogFile
    local OPTIND
    local type='github'
    local account='varia'
    local reponame=''
    local giturl=''
    local branch=${JUMPSCALEBRANCH:-development_simple}
    local sshkey=''
    while getopts "a:r:u:b:t:k:h" opt; do
        case $opt in
           a )  account=$OPTARG ;;
           t )  type=$OPTARG ;;
           r )  reponame=$OPTARG ;;
           u )  giturl=$OPTARG ;;
           b )  branch=$OPTARG ;;
           k )  sshkey=$OPTARG ;;
           h )  ZCodeGetUsage ; return 0 ;;
           \? )  ZCodeGetUsage ; return 1 ;;
        esac
    done
    if [ -z "$giturl" ]; then
        ZCodeGetUsage
        return 0
    fi

    if [ -z "$reponame" ]; then
        ZCodeGetUsage
        return 0
    fi

    echo "[+] get code $giturl ($branch)"

    Z_mkdir_pushd $CODEDIR/$type/$account || return 1

    touch ~/.ssh/known_hosts
    # check if docs.grid.tf (gogs) in the url
    if grep -q docs.grid.tf <<< $giturl; then
        ssh-keyscan -t rsa docs.grid.tf >> ~/.ssh/known_hosts 2>&1 >> $LogFile || die "ssh keyscan" || return 1
    fi

    if ! grep -q ^github.com ~/.ssh/known_hosts 2> /dev/null; then
        ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts 2>&1 >> $LogFile || die "ssh keyscan" || return 1
    fi

    if [ ! -e $CODEDIR/$type/$account/$reponame ]; then
        echo " [+] clone"
        git clone -b ${branch} $giturl $reponame 2>&1 >> $LogFile || die "git clone" || return 1
    else
        Z_pushd $CODEDIR/$type/$account/$reponame || return 1
        echo " [+] pull"
        echo 'git pull' >> $LogFile
        git pull  2>&1 >> $LogFile || die "could not git pull" || return 1
        Z_popd || return 1
    fi
    Z_popd || return 1
}

JUMPSCALEBRANCHExists() {
    local giturl="$1"
    local branch=${2:-${JUMPSCALEBRANCH}}

    # remove the trailing .git from the giturl if exist
    giturl=${giturl%.git}

    echo "[+] Checking if ${giturl}/tree/${branch} exists"
    httpcode=$(curl -o /dev/null -I -s --write-out '%{http_code}\n' $giturl/tree/${branch})

    if [ "$httpcode" = "200" ]; then
        return 0
    else
      echo "[+] Error: ${giturl}/tree/${branch} does not exist"
        return 1
    fi
}

ZInstall_jumpscale() {

    # if ZDoneCheck "ZInstall_jumpscale" ; then
    #     echo "[+] Host jumpscale installation already done."
    #    return 0
    # fi

    mkdir -p $HOME/jumpscale

    echo "[+] clean previous JS install"
    rm -rf /usr/local/lib/python3.6/site-packages/Jumpscale*
    rm -rf /usr/local/lib/python3.6/site-packages/JS*

    echo "[+] install JS"
    pushd $CODEDIR/github/threefoldtech/jumpscale_core
    pip3 install -e . > ${LogFile} 2>&1 || die "Could not install core of JS" || return 1
    popd
    # pip3 install -e $CODEDIR/github/threefoldtech/jumpscale_core || die "could not install core of JS" || return 1

    echo "[+] installing jumpscale lib"
    pushd $CODEDIR/github/threefoldtech/jumpscale_lib
    if [ -n "$JSFULL" ] ; then
      pip3 install -e .  > ${LogFile} 2>&1 || die "Coud not install lib of JS" || return 1
    else
      pip3 install --no-deps -e .  > ${LogFile} 2>&1 || die "Coud not install lib of JS" || return 1
    fi
    popd

    echo "[+] installing jumpscale prefab"
    pushd $CODEDIR/github/threefoldtech/jumpscale_prefab
    pip3 install -e .  > ${LogFile} 2>&1 || die "Coud not install prefab" || return 1
    popd

    echo "[+] installing jumspcale js_ commands"
    find  $CODEDIR/github/threefoldtech/jumpscale_core/cmds -exec ln -s {} "/usr/local/bin/" \; 2>&1 > /dev/null || die || return 1

    pip3 install Cython --upgrade  || die || return 1
    # pip3 install asyncssh
    pip3 install numpy --upgrade  || die || return 1
    # pip3 install tarantool
    pip3 install PyNaCl --upgrade || die || return 1

    echo "[+] jumpscale installed (OK)"

}


ZInstall_host_base(){

    if [ "$(uname)" == "Darwin" ]; then

        if [ -n "$JSFULL" ] ; then
            echo "[+] check to install xcode (am in jsfull development mode)"
            which xcode-select 2>&1 >> /dev/null
            if [ $? -ne 0 ]; then
                xcode-select --install
            fi
        fi

        which brew 2>&1 >> /dev/null
        if [ $? -ne 0 ]; then
            /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
        fi

        # echo "[+] upgrade brew"
        # brew upgrade  >> ${LogFile} 2>&1 || die "could not upgrade all brew installed components" || return 1

        echo "[+] installing git, python3, mc, tmux, curl"
        Z_brew_install mc wget python3 git unzip rsync tmux curl || return 1

        echo "[+] set system config params"
        echo kern.maxfiles=65536 | sudo tee -a /etc/sysctl.conf >> ${LogFile} 2>&1 || die || return 1
        echo kern.maxfilesperproc=65536 | sudo tee -a /etc/sysctl.conf >> ${LogFile} 2>&1 || die || return 1
        sudo sysctl -w kern.maxfiles=65536 >> ${LogFile} 2>&1 || die || return 1
        sudo sysctl -w kern.maxfilesperproc=65536 >> ${LogFile} 2>&1 || die || return 1
        ulimit -n 65536 >> ${LogFile} 2>&1 || die || return 1


    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        dist=''
        dist=`grep DISTRIB_ID /etc/*-release | awk -F '=' '{print $2}'`
        if [ "$dist" == "Ubuntu" ]; then
            echo "[+] updating packages"
            sudo apt-get update >> ${LogFile} 2>&1 || die "could not update packages" || return 1

            echo "[+] installing git, python, mc, tmux, curl"
            Z_apt_install mc wget python3 git unzip rsync tmux curl || return 1

            if [ -n "$JSFULL" ] ; then
                echo "[+] installing development tools: build essential & pythondev"
                Z_apt_install  build-essential python3-dev
            fi
        fi
    else
        die "platform not supported"
    fi

    if [ "$(uname)" == "Darwin" ]; then
        echo "no need to install pip, should be installed already"
    else
        curl -sk https://bootstrap.pypa.io/get-pip.py > /tmp/get-pip.py || die "could not download pip" || return 1
        python3 /tmp/get-pip.py  >> ${LogFile} 2>&1 || die "pip install" || return 1
        rm -f /tmp/get-pip.py
    fi

    echo "[+] upgrade pip"
    pip3 install --upgrade pip >> ${LogFile} 2>&1 || die "pip upgrade" || return 1

    # ZDoneSet "ZInstall_host_base"
}





#########################################################
#########################################################

#check if branch given, if not set do development
export JUMPSCALEBRANCH=${JUMPSCALEBRANCH:-development_simple}
# export JSFULL=1 #if set will install in developer mode

export LogFile='/tmp/jumpscale_install.log'
echo "init" > $LogFile

if [ "$(uname)" != "Darwin" ] ; then
    export CODEDIR=${CODEDIR:-/opt/code}
else
    export CODEDIR=${CODEDIR:-~/code}
fi

if [ -z "$HOMEDIR" ] ; then
    export HOMEDIR="$HOME"
fi

if [ -z "$LC_ALL" ] ; then
    export LC_ALL="C.UTF-8"
fi

if [ -z "$HOMEDIR" ] || [ ! -d "$HOMEDIR" ]; then
    echo "[-] ERROR, could not find homedir $HOMEDIR"
    return 1
fi

cd /tmp
#remove old stuff
rm -rf /usr/local/bin/js9_*
rm -rf /usr/local/bin/js_*
rm -f ~/jsenv.sh
rm -f ~/jsinit.sh 
sed -i.bak '/jsenv.sh/d' $HOMEDIR/.profile > /dev/null 2>&1
sed -i.bak '/export SSHKEYNAME/d' $HOMEDIR/.bashrc > /dev/null 2>&1
sed -i.bak '/jsenv.sh/d' $HOMEDIR/.bashrc > /dev/null 2>&1
sed -i.bak '/jsenv.sh/d' $HOMEDIR/.profile_js > /dev/null 2>&1
sed -i.bak '/.*zlibs.sh/d' $HOMEDIR/.bashrc > /dev/null 2>&1
sed -i.bak '/.*zlibs.sh/d' $HOMEDIR/.profile_js > /dev/null 2>&1
rm ~/opt/jumpscale/cfg/me.toml > /dev/null 2>&1
rm ~/opt/jumpscale/cfg/jumpscale.toml > /dev/null 2>&1
rm -rf ~/JShost* > /dev/null 2>&1
rm -rf ~/jumpscalehost* > /dev/null 2>&1
rm -rf ~/jumpscale_host* > /dev/null 2>&1
rm -rf ~/jumpscale* > /dev/null 2>&1
sudo rm -rf $TMPDIR/zutils_done > /dev/null 2>&1
sudo rm -rf /tmp/zutils_done > /dev/null 2>&1
find /usr/local/lib -iname jumpscale.py -exec rm {} \; > /dev/null 2>&1
find /usr/lib -iname jumpscale.py -exec rm {} \; > /dev/null 2>&1
find ../ -iname *.plugins.json  -exec rm {} \; > /dev/null 2>&1

echo "INSTALL Jumpscale on branch $JUMPSCALEBRANCH"
# set -x
# ZInstall_host_base || die "Could not prepare the base system" || exit 1
ZCodeGetJS || die "Could not download jumpscale code" || exit 1
ZInstall_jumpscale || die "Could not install core of jumpscale" || exit 1
