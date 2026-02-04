The esp32 port requires a configured ESP IDF development environment to compile. Espressif provide a docker container that has this all set up and ready to go which can be used to simplify building the firmware, particularly if you want to try building under different IDF versions.

This script can be used as a wrapper to automate the process of running the compile inside the appropriate docker container without needing any additional configuration of your pc. This works with Linux or Windows/WSL2 with the official docker tools installed.

If you're using Windows/WSL2 and want to flash the board directly the [WSL USB Manager](https://gitlab.com/alelec/wsl-usb-gui#wsl-usb-manager) tool can simplify connecting your usb devices through to WSL.

``` bash
cat << "EOF" > ~/.local/bin/esp-compile
#!/bin/bash
SCRIPTPATH=$(readlink --canonicalize-existing "${BASH_SOURCE[0]}")

# Wrapper script to build / flash esp32 boards inside the official ESP IDF docker container
# Usage: esp-compile <IDF_VER> <BOARD> <port if want to deploy> <extra args if needed>
# Examples
# esp-compile v5.0.4 ESP32_GENERIC /dev/ttyACM0
# esp-compile v5.2.2 ESP32_GENERIC
# esp-compile v5.2.2 ESP32_GENERIC_C3 /dev/ttyACM0
# esp-compile v5.2.2 ESP32_GENERIC_S3 clean
# esp-compile v5.2.2 ESP32_GENERIC_S3 /dev/ttyACM1 BOARD_VARIANT=FLASH_4M


if [ ! -f /.dockerenv ]; then
# If not running in docker container, parse arguments then re-run this same script inside a new esp idf container

if [ "$1" == "" ]; then echo "$0 IDF_VER BOARD <DEPLOY_PORT> <extra args>"; exit; fi
IDF_VER=$1
BOARD=$2
if [[ $3 == /dev/* ]]; then
  DEPLOY_PORT=$3
  shift
fi
shift;shift
ARGS="${@}"
CD=$(pwd)

docker run -it --rm \
  -e BOARD=$BOARD -e ARGS="$ARGS" -e DEPLOY_PORT=$DEPLOY_PORT -e UID=$(id -u) \
  -v "$CD":"$CD" -v"$SCRIPTPATH":"$SCRIPTPATH" -v /sys/bus:/sys/bus -v /dev:/dev \
  --net=host --privileged -w "$CD" espressif/idf:$IDF_VER bash "$SCRIPTPATH"

else
# Now we're running inside the IDF container

if [ "$(id -u)" != "$UID" ]; then
# create new user with ID that matches the user who called this script (who should own the source tree)
useradd -ms /bin/bash -g root -G sudo -u $UID esp;
# now re-run this script as that new user
# this ensures that created binary files are owned by the calling user
su esp -m -c "$SCRIPTPATH"

else
# Now we're inside the container, running as the target user
. /opt/esp/entrypoint.sh
export HOME=/tmp

# inform git that we're in a trusted environemnt (container)
git config --global --add safe.directory '*';

if [ ! -e mpy-cross/build/mpy-cross ]; then 
make -C mpy-cross
fi

echo_and_run() { echo -e "\n\$ $*\n" ; "$@" ; }


# Build the firmware
make -C ports/esp32 BOARD=$BOARD submodules

if [ "$DEPLOY_PORT" == "" ]; then
# Just build the firmware
echo_and_run \
  make -C ports/esp32 BOARD=$BOARD $ARGS

else
# build and flash the firmware
echo_and_run \
  make -C ports/esp32 BOARD=$BOARD $ARGS deploy PORT=$DEPLOY_PORT

fi

fi  # end of user
fi  # end of container

EOF
chmod +x ~/.local/bin/esp-compile
```