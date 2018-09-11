# Setting up an schroot with external mount --bind

Why set up a chroot?  Answer: to be able to have simultaneous development
branches checked out **without** any of them doing damage to each other
or interfering in any way.  Also, running the Jumpscale unit tests,
which need to be carried out as root, may actually damage a system,
by destroying /etc/passwd, /etc/group, /root/.ssh/authorized\_keys,
/root/.profile and other critical files.

**Without running the unit tests it is impossible to verify the code**

Therefore it is pretty much absolutely essential to run in a chroot.
Chroot itself however is quite inconvenient, so using schroot is much
better.  As root (sudo bash), run the following:


    # apt-get install schroot debootstrap
    # mkdir -p /opt/chroot/stretch
    # debootstrap stretch /opt/chroot/stretch http://deb.debian.org/debian

Add the following to /etc/schroot/chroot.d/stretch.conf:

    [stretch]
    description=Debian stretch (stable)
    directory=/opt/chroot/stretch
    groups=sbuild-security
    #aliases=stable
    #personality=linux32

To enter the chroot at any time, run the schroot command:

    # schroot -c stretch

To make sure that the prompt is easy to distinguish, whilst still in the
chroot run the following:

    # echo stretch > /etc/debian_chroot

Exit from the chroot (exit or Ctrl-D), then re-run the schroot command.
The prompt should now look like this:

    (stretch)root@debian:/root# 

Exit the chroot again and from **outside** the chroot,
create subdirectories for the codebase in the chroot:

    # mkdir /opt/chroot/stretch/opt/code/github/threefoldtech

Create a corresponding subdirectory for where the **branch** is to be
developed from:

    $ mkdir /home/code/threefoldtech_branchname

Add the following mount bind entries to /etc/fstab:

    /dev/pts /opt/chroot/stretch/dev/pts	none	bind	0	0
    /proc	/opt/chroot/stretch/proc	none	bind	0	0
    /sys	/opt/chroot/stretch/sys	none	bind	0	0
    /tmp	/opt/chroot/stretch/tmp	none	bind	0	0
    /home/code/threefoldtech_branchname	/opt/chroot/stretch/opt/code/github/threefoldtech	none	bind	0	0

The first three are essential; the mount --bind to /tmp is a "good idea"
as it allows convenient transfer from inside the chroot to outside (by
copying files to and from /tmp), and the fifth entry must match the
subdirectory created in the chroot (threefoldtech).

It is **not recommended** to try to have multiple development branches inside
one single chroot: instead, create separate chroots, one per development
branch.  It is perfectly fine to cp -aux one entire chroot (snapshot it)
to make life easier.

Run the following commands to get the mount binds to activate (don't reboot,
it is totally unnecessary):

    # mount /opt/chroot/stretch/dev/pts
    # mount /opt/chroot/stretch/proc
    # mount /opt/chroot/stretch/sys
    # mount /opt/chroot/stretch/tmp
    # mount /opt/chroot/stretch/opt/code/github/threefoldtech

To complete the install, it is now entirely up to you how to go about
doing that.  One way is to actually run the install script actually in
the chroot, making sure it is done in /opt/code/github/threefoldtech,
whilst another is to git clone the code from *outside* of the chroot
(in /home/code/threefoldtech\_branchname) and to go from there: it is
entirely up to you.

With this technique of using mount --bind, development (editing etc.)
can take place **outside** of the chroot,

