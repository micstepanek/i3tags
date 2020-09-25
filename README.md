# i3tags
Experimenting with i3ipc, dwm-like tags, i3/window/context keyboard menu, status bar replacement and autocomplete menu.

Please see 'dev' branch for more recent development.

Resolvable issues:
- hard-code
- long functions
- documentation

Coming soon
- dissolve class GUI into graphical_elements.py and
BusinessLogic
- create command 'tags' 
- create window if content requested
- get rid of command 'new'

Tough but minor issues:
- switching between tags that use the same window causes
undesired content to appear for a fraction of second. Cannot be
eliminated by this app, it is rooted in how i3 works.
Either background, resize or other irrelevant content is always
visible for a fraction of second.
- Qt showing rectangle instead of high unicode character