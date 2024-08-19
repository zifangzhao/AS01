#!/bin/bash
cp /usr/local/bin/cereloop/proc_ASSY37W-2_1-2_2.xml proc.xml
count=1
IFS=$'\n'
all=`wc -l<<<$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS`
$((all--))
for line in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS;
do
exec gnome-terminal -t "Processing Cerebus format data($count/$all): $line" -x bash -c "python3 /usr/local/bin/cereloop/run_resample.py \"$line\"; python3 /usr/local/bin/cereloop/run_ndm.py \"$line\";exec bash;"&
$((count++))
done
