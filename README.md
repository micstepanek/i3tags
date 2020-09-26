# i3tags
adds keyboard-driven context menu with tagging options
to your i3. As a side effect it can also replace i3bar.
Coded with Python3, i3ipc and Qt5.

It is configured by adding keywords to your /i3/config. E.g.

    nop retag 

will show entry to set new tags for focused window.

Resolvable issues:
- hard-code
- long functions
- documentation

Coming soon
- dissolve class GUI into graphical_elements.py and
BusinessLogic
- create window if content requested
- create command 'tags' 
- get rid of command 'new'

Tough but minor issues:
- switching between tags that use the same window causes
undesired content to appear for a fraction of second. Cannot be
eliminated by this app, it is rooted in how i3 works.
Either background, resize or other irrelevant content is always
visible for a fraction of second.
- Qt showing rectangle instead of high unicode character