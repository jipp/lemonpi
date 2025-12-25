#!/bin/bash -e

cp /etc/fstab /etc/fstab.orig
cp /boot/firmware/cmdline.txt /boot/firmware/cmdline.txt.orig
cp /boot/firmware/config.txt /boot/firmware/config.txt.orig

curl -fsSL https://get.docker.com -o /home/${FIRST_USER_NAME}/get-docker.sh
sh /home/${FIRST_USER_NAME}/get-docker.sh
usermod -aG docker ${FIRST_USER_NAME}
