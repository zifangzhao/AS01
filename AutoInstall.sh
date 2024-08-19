#!/bin/bash
#sudo ubuntu-drivers autoinstall
sudo apt -y upgrade -f -qq

this_path=*.deb
for f in $this_path
do
	echo "Installing $f "
	rst=1
	while [ "$rst" -ne "0" ] 
	do
	sudo dpkg -i $f
	rst=$?
	sudo apt upgrade -f -y 
	sudo apt -f install  -y 
	done
done

sudo apt install python-pip -y
sudo apt install python3-pip -y
pip install pip -U
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install psutil 
pip install pyarmor 
pip install tkinter 
pip3 install psutil 
pip3 install pyarmor 
pip3 install tkinter 

sudo ./Deploy_server.sh

cd "./Update_Lotus_electrode_maps"
./Update_Electrode_maps.sh
