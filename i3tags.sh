#!/usr/bin/env bash
FULLPATH=`realpath $0`
DIRECTORY=`dirname $FULLPATH`
if [ "$1" = "nolog" ]
    then
    python3.8 $DIRECTORY/i3tags.py
else
    # Print/write stdout and stderr to console and log
    python3.8 $DIRECTORY/i3tags.py 2>&1 | tee -a ~/.i3tags.log
fi

