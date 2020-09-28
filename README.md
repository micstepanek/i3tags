# i3tags
Adds keyboard-driven context menu with tagging options
to your i3. As a side effect it can also replace i3bar.
Coded with Python3, i3ipc and Qt5.

Please see these tiny demonstration videos on YouTube.
Play the first video 0.5 speed to see what is actually happening.

https://www.youtube.com/watch?v=IL9t-gS0clM

https://www.youtube.com/watch?v=HO1wq3JevYY

It is configured by adding keywords to your /i3/config. E.g.

    nop tags
    nop retag
    nop mode
    nop switch

Resolvable issues:
- positions of windows in tagged workspace is unstable
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