#!/bin/bash
username=$(whoami)
echo "Generating function for:$username"
cd "./scripts"
sudo mkdir -p "/home/$username/.local/share/nautilus/scripts/Lotus Electrodes/"

this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	sudo cp "./$f" "/home/$username/.local/share/nautilus/scripts/Lotus Electrodes/$f"
done



cd ..
cd ./basic_scripts
this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	sudo cp "./$f" "/home/$username/.local/share/nautilus/scripts/$f"
done

sudo chmod 777 -R "/home/$username/.local/share/nautilus/scripts/"

cd ..
cd ./maps
sudo mkdir -p "/usr/local/bin/cereloop/"
this_path=*
for f in $this_path
do
	echo "Copying $f file..."
	sudo cp "./$f" "/usr/local/bin/cereloop/$f"
done

sudo chmod 777 -R "/usr/local/bin/cereloop/"
