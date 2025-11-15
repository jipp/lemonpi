#!/bin/bash
sudo sed -i s/"PARTUUID=........-02"/"\/dev\/nvme0n1p2"/ /boot/firmware/cmdline.txt
sudo sed -i s/"PARTUUID=........-01"/"\/dev\/nvme0n1p1"/ /etc/fstab
sudo sed -i s/"PARTUUID=........-02"/"\/dev\/nvme0n1p2"/ /etc/fstab
sudo apt update && sudo apt -y upgrade && sudo apt -y clean
sudo apt install -y git
#git config --global user.email "wolfgang.keller@wobilix.de"
#git config --global user.name "Wolfgang Keller"
#sudo sh -c "echo 'dtoverlay=disable-bt' >> /boot/firmware/config.txt"
#sudo sh -c "echo 'dtoverlay=disable-wifi' >> /boot/firmware/config.txt"
