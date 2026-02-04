This page covers installing the ARM toolchain needed to build firmware for the pyboard (or other ARM processors).

# Linux (general)
One source of the ARM toolchain (for all platforms) is from: https://launchpad.net/gcc-arm-embedded

For all of the linux variants, you should download the "Linux installation tarball". There is a link over on the right side of the page. The actual URL changes periodically (about once every 3 months).
```bash
mkdir ~/stm
cd ~/stm
wget https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q2-update/+download/gcc-arm-none-eabi-4_8-2014q2-20140609-linux.tar.bz2
tar xf gcc-arm-none-eabi-4_8-2014q2-20140609-linux.tar.bz2
```
and then add ```${HOME}/stm/gcc-arm-none-eabi-4_8-2014q2/bin``` to your PATH. You might do this by adding the following line to your ```~/.bashrc``` file:
```bash
export PATH="${PATH}:${HOME}/stm/gcc-arm-none-eabi-4_8-2014q2/bin"
```
and then it will be added automatically each time you login. You can also just execute the command directly from your bash shell and it will work until you exit your shell.

Note: This is a 32-bit toolchain, so if you're using a 64-bit version of linux, you may need to also install the 32-bit version of libc.

For Ubuntu 14.04, I did:
```bash
sudo apt-get install libc6:i386
```

# Using Symbolic Debugging
Symbolics can be useful for module or hardware integration testing. The hardware link to the processor is often manufacturer specific, and the debugging software needs a driver to that software. For STM32  https://github.com/micropython/micropython/wiki/Symbolic-Debugging-for-STM32