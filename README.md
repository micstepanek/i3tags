# i3tags
Adds keyboard-driven context menu with tagging options
to your i3. As a side effect it can also replace i3bar.
Coded with Python3, i3ipc and Qt5.

Please see these tiny demonstration videos on YouTube.
You may like to play the first video 0.5 speed to see what is actually happening.

https://www.youtube.com/watch?v=IL9t-gS0clM

https://www.youtube.com/watch?v=HO1wq3JevYY

It is configured by adding keywords to your /i3/config. E.g.

    nop tags
    nop retag
    nop mode
    nop switch
    nop reset

Resolvable issues:
- only 'nop tags' and 'nop mode' can show window
- low consistency ('nop mode' clears window before adding,
 'nop tags' not)
- positions of windows in tagged workspaces are unstable
- hard-code
- documentation
- long functions
- back_and_forth must be disabled, i3tags is doing back and
forth for tag switching

Coming soon
- create window if content requested

Tough but minor issues:
- switching between tags that use the same window causes
undesired content to appear for a fraction of second. Cannot be
eliminated by this app, it is rooted in how i3 works.
Either background, resize or other irrelevant content is always
visible for a fraction of second.
- Qt showing rectangle instead of high unicode character
    
You may start i3tags anytime while i3 is running by i3tags.sh.

Here are some commands that may be useful for installation(untested):

    sudo apt install python3.8
    sudo apt install qt5-default
    sudo python3.8 -m pip install i3ipc
    sudo python3.8 -m pip install PySide2
    sudo python3.8 -m pip install logging
    sudo python3.8 -m pip install multipledispatch
    sudo python3.8 -m pip install subprocess
    sudo python3.8 -m pip install threading

Kill the app by typing 'exit' to retag entry.
