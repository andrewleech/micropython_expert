During development, tools like [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) are fantastic for quickly running code on a micropython device.

Once an application is ready for release however you will often want your code to be bundled into the firmware for easy deployment.

The official way to achieve this is called [freezing](https://docs.micropython.org/en/latest/reference/manifest.html).

Code freezing however only works with python file, to deploy other kinds of data or assets there are a number of different options (listed in no particular order):

* https://github.com/peterhinch/micropython_data_to_py
* https://insigh.io/blog/how-to-freeze-the-unfreezable/
* https://github.com/bixb922/freezefs
* https://github.com/Josverl/vfs_merge
* https://github.com/glenn20/micropython-esp32-ota
* https://github.com/glenn20/mp-image-tool-esp32

Longer term this is intended to be an official way to deploy any kind of files: https://github.com/micropython/micropython/pull/8191
