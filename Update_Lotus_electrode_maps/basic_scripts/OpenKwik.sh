#!/bin/bash
count=1
IFS=$'\n'
all=`wc -l<<<$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS`
$((all--))
for line in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS;
do
exec gnome-terminal -t "Processing Binary format data($count/$all): $line" -x bash -c "export PATH=~/anaconda3/bin:$PATH;source activate phy2;phy kwik-gui \"$line\";exec bash;"&
$((count++))
done
