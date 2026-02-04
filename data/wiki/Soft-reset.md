## Task:
During development, one might want to restart a python program over and over again and keep the source code in an editor to perform quick changes. This is an useful scenario to test new features and to achieve a quick debug cycle.

## Problem:
Pressing the reset button will disconnect the board (confirmed on the STM Discovery boards) from the system and reattach it. This includes loosing connection to the mass storage device which keeps the python files for execution. Mount points on Linux systems will be not longer valid and you have to remount (or use an automounter) and reenter the mounted folder.
This tends to confuse text editors up to the possible loss of (unsaved) data.

## Solution:
To avoid this problem, one can perform a soft reset. This restarts micropython and the start-up python files (e.g. main.py) without a disconnect reconnect cylce of the mass storage device.
To perform a soft-reset, a connection to the board via a serial console program is required e.g.,

`screen /dev/ttyACM0`.

Note, since micropython executes the start-up files (e.g. main.py) there will be no micropython prompt.

Pressing `Ctrl-C` will interrupt the micropython execution and drops back into an interactive micropython shell. 

Pressing `Ctrl-D` will terminate the interactive micropython shell and soft-reset the controller to restart the start-up files.

### Further improvements
One can send those commands to the serial connection of the board to achieve the same result (make sure you have write permissions).
`echo "\x03\x04" > /dev/ttyACM0`

### Integrate into IDE/Editor
Several IDEs and Editors allow to customize shortkeys to execute arbitrary code.

#### Emacs
Add this somewhere in your emacs init (e.g. ~/.emacs.d/init.el). Adapt the serial device name if necessary. Now press `Ctrl-F5` within Emacs whenever you wish to soft-reset the controller.

```
(defun restart_micropython ()
" Restart Micropython-Board"
(interactive)
(save-buffer) ;; make sure to write changes to disk
(shell-command "echo \"\\x03\\x04\" > /dev/ttyACM0")
)
;; Set a global key to initiate soft reset (customize as desired)
(global-set-key (kbd "C-<f5>") 'restart_micropython)
```