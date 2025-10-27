#!/bin/bash

if [ $# -eq 0 ]; then
	echo "No arguments supplied"
	exit 1
fi

echo "check checksum"
sha256sum -c $1.xz.sha256
if [ $? -ne 0 ]; then
	exit 1
fi

echo "decompress"
xz -kd $1.xz
sudo losetup -P /dev/loop0 $1

echo "modify image part 1"
sudo mount /dev/loop0p1 /mnt
sudo cp custom.toml /mnt
sudo cp /mnt/config.txt /mnt/config.txt.orig
sudo cp /mnt/cmdline.txt /mnt/cmdline.txt.orig
ls -lh /mnt/*.orig
ls -lh /mnt/*.toml
sudo umount /mnt

echo "modify part 2"
sudo mount /dev/loop0p2 /mnt
sudo cp /mnt/etc/fstab /mnt/etc/fstab.orig
ls -lh /mnt/etc/*.orig
sudo umount /mnt

echo "clean-up"
sudo losetup -D

echo "rename"
mv $1 raspios.img

echo "compress"
xz -kz raspios.img
sha256sum raspios.img.xz > raspios.img.xz.sha256
