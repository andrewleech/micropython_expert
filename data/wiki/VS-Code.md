Visual Studio Code, also commonly referred to as VS Code, is a source-code editor made by Microsoft, for Windows, Linux and macOS. Features include support for debugging, syntax highlighting, intelligent code completion, snippets, code refactoring, and embedded Git. Users can change the theme, keyboard shortcuts, preferences, and install extensions that add functionality.

In the Stack Overflow 2022 Developer Survey, Visual Studio Code was ranked the most popular developer environment tool among 71,010 respondents, with 74.48% reporting that they use it.

While there isn't an official plugin for micropython, the official python plugins can be set up to be quite helpful while the built in terminal can be used to communicate with your board via mpremote etc. VSCode devcontainer support can be used to make compilation easier to simplify getting built toolchains set up to match each port.

# VS Code settings & Python plugin
All project-specific vscode settings are stored in a `<myproject>/.vscode/settings.json` file which can be editing manually, or via the gui settings editor in vscode.

I like to structure my project such that the top level folder has things like readme, tool config files like pyproject.toml, Makefiles, .devcontainer etc.
I then have a `src` folder which contains a `firmware` folder with my project `.py` files and a `lib` folder with any external libraries I bring in.
These folders can be listed in the settings `extraPaths` so that the python plugin find and uses them.

It also helps to get a copy of micropython stubs to assist with type hinting (and mypy). Pick the [appropriate platform for you project](https://micropython-stubs.readthedocs.io/en/latest/firmware_grp.html) and [install a copy](https://micropython-stubs.readthedocs.io/en/latest/20_using.html#install-into-a-typings-folder) to `<myproject>/tools/typing` or similar:
```
pip install -U micropython-stm32-stubs==1.20.* --target ./tools/typings --no-user
```
This can then be referenced in the settings file below.

Here's a copy of my `.vscode/settings.json` files:
``` jsonc
{
    "python.linting.enabled": true,
    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.diagnosticSeverityOverrides": {
        "reportMissingModuleSource": "none"
    },
    "python.analysis.typeshedPaths": [
        "tools/typings"
    ],
    "python.analysis.extraPaths": [
        "src/firmware",
        "src/firmware/test",
        "src/libs",
        "src/libs/micropython-lib/micropython/aiorepl",
        "tools/typings"
    ],
    "python.formatting.provider": "black",
    // Set line length to 99 to match micropython
    "python.formatting.blackArgs": [
        "--line-length",
        "99"
    ],
    // pylint doesn't honor extraPaths settings
    "python.linting.pylintEnabled": false,
    "python.linting.pylintArgs": [
        "--disable=W"
    ],
    "python.linting.flake8Enabled": false,
    "editor.formatOnSave": true,
    "editor.formatOnType": true,
    "files.trimTrailingWhitespace": true,
    "files.exclude": {
        "build-*/**": false
    },
    "files.insertFinalNewline": true
}
```

# devcontainer
VS Code [devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) feature allows your coding environment to be hosted inside a docker container, providing all the tools and consistent environment of that docker container, without needing to install everything onto your computer manually.

This can be set up quickly by adding a `.devcontainer.json` file to the root folder of your project, after which VS Code will ask in a popup if you want to re-open your project in the container.
Here's an example `.devcontainer.json` micropython project file you could base yours on:
``` jsonc
{
  "name": "Micropython Project",
  "image": "micropython/unix:latest",
  "containerEnv": {
    "DEVCONTAINER": "1"
  },
  "runArgs": [
    "-e",
    "GIT_EDITOR=code --wait",
    // Docker will clean up the container and remove the file system when
    // the system exits
    "--rm",
    // -e will set environment variables
    // SSH_AUTH_SOCK is used to specify the ssh permission files
    "-eSSH_AUTH_SOCK=/run/user/1000/keyring/ssh",
    // Specify the work directory as the local workspace folder
    "-w${localWorkspaceFolder}",
    // Tell docker to use the same user as the host is using. Value should
    // match output of the command "id -u".
    "--user=1000:1000",
    "-eHOME=/home",
    // Use the same display, and network ports, as the host. (This allows
    // graphical applications, such as JFlashLite, to be launched in the
    // container environment)
    "--env=\"DISPLAY\"",
    "--hostname=Micropython",
    "--add-host=Micropython:127.0.0.1",
    "--net=host",
    // By default, docker does not allow access to the host computer's
    // devices. This option adds permission for docker to access the host
    // computer's decices, allowing utilities like JFlashLite to work
    // properly
    "--privileged"
  ],
  "customizations": {
    "vscode": {
      "extensions": [
        // Python development
        "ms-python.python",
        "ms-python.vscode-pylance",
        // Extensions recommended by vscode for C++ development
        "ms-vscode.cpptools-extension-pack",
        "ms-vscode.makefile-tools",
        // Allows user to debug ST devices, using the settings recommended in:
        // https://gitlab.pi.planetinnovation.com.au/lonsdale/firmware/code-editor-settings
        "marus25.cortex-debug",
        // Other helpful extensions
        "visualstudioexptteam.vscodeintellicode",
        "redhat.vscode-yaml",
        "esbenp.prettier-vscode",
      ]
    }
  },
  "updateRemoteUserUID": true,
  "mounts": [
    // Map user ssh settings & auth to container for git use.
    "source=${localEnv:HOME}/.ssh,target=${localEnv:HOME}/.ssh,type=bind,consistency=cached",
    // Provide USB access to container
    "type=bind,source=/dev/bus/usb,target=/dev/bus/usb",
    // Provide docker-in-docker support
    "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock",
    // Bring the local timezone into the container
    "type=bind,readonly,source=/etc/localtime,target=/etc/localtime"
  ]
}
```

The image used could be swapped from `micropython/unix:latest` to `espressif/idf:release-v4.4` if you want to compile for esp32, or one with arm-none-eabi-gcc like `micropython/build-micropython-arm:latest` for building arm ports like stm32 or mimxrt.