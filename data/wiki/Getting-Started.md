
Getting started with micropython development requires first building the appropriate binaries for your platform.

It is advisable to create a virtual environment on your system to separate your micropython build system from your local python installation. This is not mandatory, so skip the virtual environment setup if you are happy to create your build system directly on your host machine.

## Creating A Virtual Environment

To setup a virtual environment you first need **virtualenv** installed on your machine. [Go to here](https://gist.github.com/frfahim/73c0fad6350332cef7a653bcd762f08d) to find instructions on how to set this up. 

Once you have installed virtualenv, create a private virtual environment so that our build process which uses python scripts will not be influenced by python modules and libraries that a user may typically download and install on their root machine.

```bash
/> mkvirtualenv --python=/usr/bin/python3 microPython

Already using interpreter /usr/bin/python3
Using base prefix '/usr'
New python executable in /home/<your directory>/virtalenv/microPython/bin/python3
Also creating executable in /home/<your directory>/virtalenv/microPython/bin/python
Installing setuptools, pkg_resources, pip, wheel...done.
```
The mkvirtualenv command creates an area within your file system for your project files and updates environment variables to point to a local installation of a new python environment. The command **--python=/usr/bin/python3** tells virtualenv to use Python3 files. The **microPython** keyword is the name of the virtual environment.

### Setup Project Directory
Now you will be in your virtual environment. You know this from the output of your bash shell. It should show in brackets the name of the active virtual environment like this:

> (microPython) <your-machine-name> ~/virtalenv/microPython

Now create a project directory to hold micropython files

> mkdir project
> cd project

**Note** To deactivate your virtual environment you can type **deactivate**. And to work on your virtual environment after it has been deactivated you type: **/> source virtalenv/microPython/bin/activate**. This assumes that you created your virtual environment with the name 'micropython'.



## UNIX
* [DEB-based systems](https://github.com/micropython/micropython/wiki/Getting-Started#debian-ubuntu-mint-and-variants)
* [FreeBSD-based systems](https://github.com/micropython/micropython/wiki/Getting-Started#freebsd)
* [RPM-based systems](https://github.com/micropython/micropython/wiki/Getting-Started#fedora-centos-and-red-hat-enterprise-linux-and-variants)
* [Pacman-based systems](https://github.com/micropython/micropython/wiki/Getting-Started#archlinux)
* [Gentoo-based systems](https://github.com/micropython/micropython/wiki/Getting-Started#gentoo-linux)
* [Mac systems](https://github.com/micropython/micropython/wiki/Getting-Started#mac-osx)


### Debian, Ubuntu, Mint, and variants

The following packages will need to be installed before you can compile and run MicroPython:

* build-essential
* libreadline-dev
* libffi-dev
* git
* pkg-config (required at least in ubuntu 14.04)
* gcc-arm-none-eabi
* libnewlib-arm-none-eabi

To install these packages, use the following command:

> sudo apt-get install build-essential libreadline-dev libffi-dev git pkg-config gcc-arm-none-eabi libnewlib-arm-none-eabi

Then, clone the repository to your local machine, or if you have created a [virtual environment](https://github.com/micropython/micropython/wiki/Getting-Started#creating-a-virtual-environment) clone into your **project** folder.

> git clone --recurse-submodules https://github.com/micropython/micropython.git

First check that the mpy-cross script exists to allow cross compiling. This may be fixed at some point in the future to be done automatically but for now you need to do this manually. 
Change directory to the mpy-cross directory here:

> cd ~/virtalenv/microPython/project/micropython/mpy-cross

If mpy-cross does not exist do:

> make

You should notice the mpy-cross executable is now created.

Change directory to the Unix build directory:

> cd ./micropython/ports/unix

And then make the executable

> make axtls

> make

At that point, you will have a functioning micropython executable, which may be launched with the command:

> ./micropython

### FreeBSD
 
(Release 11.1 tested)

Ensure that you have git, GCC, gmake, python3, bash, autotools, and pkgconf packages installed:

> [as root] pkg install git gcc gmake python3 bash autotools pkgconf

Clone the git repository to your local machine:

> git clone --recurse-submodules https://github.com/micropython/micropython.git

Change directory to the Unix build directory:

> cd ./micropython/ports/unix

And then make the executable:

> gmake axtls

> gmake

At that point, you will have a functioning micropython executable, which may be launched with the command:

> ./micropython

### Fedora, CentOS, and Red Hat Enterprise Linux and variants

For Fedora 'micropython' is available in the [Fedora Package Collection](https://src.fedoraproject.org/rpms/micropython).

> sudo dnf -y install micropython

Additional details can be found in the [Fedora Developer Portal](https://developer.fedoraproject.org/tech/languages/python/micropython.html).

If you want a more recent release or if you are running CentOS then follow those steps. The required packages can be installed with:

> sudo yum install git gcc readline-devel libffi-devel

Clone the git repository to your local machine:

> git clone https://github.com/micropython/micropython.git

Change directory to the Unix build directory:

> cd ./micropython/ports/unix

And then make the executable

> make axtls

> make

At that point, you will have a functioning micropython executable, which may be launched with the command:

> ./micropython

### ArchLinux

The following packages will need to be installed before you can compile and run MicroPython:

* gcc or gcc-multilib
* readline
* git

To install these packages, use the following command:

> pacman -S gcc readline git

Then, clone the repository to your local machine:

> git clone https://github.com/micropython/micropython.git

Change directory to the Unix build directory:

> cd micropython/ports/unix

And then make the executable

> make axtls

> make

At that point, you will have a functioning micropython executable, which may be launched with the command:

> ./micropython

### Gentoo Linux

emerge dfu-util
app-mobilephone/dfu-util-0.9::gentoo

### Mac OSX

Dependencies are listed on [MicroPython on Mac OSX]( https://github.com/micropython/micropython/wiki/Micro-Python-on-Mac-OSX)

The XCode and Command Line Developer Tools package will need to be installed before you can compile and run MicroPython:

> xcode-select --install

Then, clone the repository to your local machine:

> git clone https://github.com/micropython/micropython.git

Change directory to the git repo and fetch all the submodules:

>  git submodule update --init

Change directory to the Unix build directory:

> cd micropython/ports/unix

Make the dependencies:

> make axtls

And then make the executable

> make

At that point, you will have a functioning micropython executable, which may be launched with the command:

> ./micropython

## Microcontrollers (Bare-Metal, without an OS)
### ARM-based microcontrollers
On a Ubuntu 14.04LTS this worked. First remove the arm-none-eabi that comes with Ubuntu 14.04LTS and install the gcc-arm-embedded version.

> sudo apt-get remove binutils-arm-none-eabi gcc-arm-none-eabi

> sudo add-apt-repository ppa:terry.guo/gcc-arm-embedded

> sudo apt-get update

> sudo apt-get install gcc-arm-none-eabi

(as of 2015Sept19 pulled in amd64 4.9.3.2015q2-1trusty1)

If needed to remove 
> sudo apt-get remove gcc-arm-none-eabi

For teensy script add-memzip.sh need
> sudo apt-get install realpath

Assuming micropython has been installed via git in current directory
> cd  git\micropython\stmhal

> make

(completes but didn't test)

> cd ../teensy

> make

(completes but didn't test)

See Running Scripts in https://github.com/micropython/micropython/wiki/Board-Teensy3.1)

Discussion on design https://forum.pjrc.com/threads/24794-MicroPython-for-Teensy-3-1/)

> cd ../minimal

> make - FAILS

### Fedora

Install packages arm-none-eabi-gcc, arm-none-eabi-binutils and arm-none-eabi-newlib to be able to build stmhal port. Install dfu-util for flashing the firmware.