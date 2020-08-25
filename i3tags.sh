if [ "$1" = "log" ]
    then
    i3tags.py &>>~/aa/bin/i3/log.log
else
    i3tags.py
fi

