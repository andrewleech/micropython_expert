# Overview

Micropython offers a significant advancement to developing code on a microcontroller. With the pyboard, you no longer have to have special tools, debugging IDE's or any other "fluff" to develop code that runs on a microcontroller. Instead, the pyboard (and other supported platforms) present themselves to your computer as two things:

- a serial module where you can access the python interactive interpreter (REPL prompt)
    - follow [this tutorial](http://docs.micropython.org/en/latest/tutorial/repl.html) to access the interactive interpreter
- a standard flash drive for doing file system operations

This allows you to develop code using your favorite text editor and run it *directly on the pyboard* -- no need to install complex tool chains or anything else. In addition, you are writing code with python, which is widely considered to be a very productive language to use.

## Basic Development
The file system and REPL prompt give you a lot of power and choice for how to develop. One possibility:

- play with some code on the interactive interpreter
- write a module directly on the pyboard with your favorite text editor
- do a [[soft reset|Soft reset]] to reload the file system
- use and test your newly created module in the REPL

## Revision Control (with git) on a microcontroller board

One thing that can be tricky to use is a revision control system. [Git](http://git-scm.com/) is the most popular revision control system, and it is possible to use it to do revision control on the pyboard.

The key is that we do NOT want to actually put the git data (stored in the `.git` folder) on the pyboard itself. This is for several reasons:

- the pyboard has limited space (about 1 MB)
- the pyboard is still in development, and has a bug where occasionally it will delete the flash. If your code is under revision control outside the pyboard, then it can still be retrieved (at least since the last commit). If not, you run the risk of loosing data and therefore work.
- you don't always have the pyboard plugged in, and may want to reference your code at other times.

For these reasons we will not be storing the git data directly on the pyboard, but will instead be using features of git that allow you to "reference" the pyboard while modifying code in a pyboard directory.

These directions are for linux only, but should be informative to windows users with only a few tweaks.

Steps to reference git directory:
- First we will make the git directory we will be using in our regular file system.
- `cd ~` cd to our home folder 
- `mkdir dev` make your development folder 
- `cd dev` cd into it 
- `git init` initialize it as a git repository 

Now we will change to your pyboard and create the folder we will be developing on
- `cd /media/user/PYBFLASH` cd to your pyboard directory
- `mkdir dev` create the same folder (doesn't have to be named the same, but I would recommend it!)
- `touch dev/__init__.py` put a file inside of it
- `export GIT_DIR=~/dev/.git` set the `GIT_DIR` variable to where your actual version control folder is
- `git status` -- should show that you have an unadded file, `__init__.py`!
- everything should now work as a normal git repository

Some notes:
- This "trick" uses the standard git environment variables, which are [documented here](http://git-scm.com/2010/04/11/environment.html)
     - you may be able to find other ways to do this that you like better from that (or other) documentation
- **BE WARNED** that when you set the `GIT_DIR` variable it will use that directory no matter where you are. This means that if you change directories, it will still think that your version control folder is in `~/dev/.git`
    - for this reason, it is recommended to use a dedicated terminal for all git operations in the `$PYBOARD/dev` folder. For linux/mac/cygwin, a tool like [screen](https://wiki.archlinux.org/index.php/GNU_Screen) or [tmux](https://wiki.archlinux.org/index.php/Tmux) is recommended for managing multiple open terminals.








