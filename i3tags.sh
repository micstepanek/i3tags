#!/usr/bin/env bash
if [ "$1" = "nolog" ]
    then
    i3tags.py
else
    # Print/write stdout and stderr to console and log
    i3tags.py 2>&1 | tee -a ~/aa/bin/i3/i3tags.log
fi

