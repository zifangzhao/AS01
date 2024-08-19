#!/bin/bash
rst=1
while [ "$rst" -ne "0" ] 
do
sudo ubuntu-drivers autoinstall
rst=$?
sudo apt upgrade -f -y 
sudo apt -f install -f -y 
done


rst=1
while [ "$rst" -ne "0" ] 
do
sudo dpkg -i ./teamviewer_15.5.3_amd64.deb
rst=$?
sudo apt upgrade -f -y 
sudo apt -f install  -y 
done

teamviewer
sudo teamviewer daemon enable
sudo teamv12iewer passwd 12345678
