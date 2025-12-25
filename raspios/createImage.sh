#!/bin/bash

PWD=`pwd`
SRC=$PWD"/download/"
DST=$PWD"/deploy"
RELEASE=$PWD"/trixie/"

if [ $# -eq 0 ]; then
	echo "No arguments supplied"
	exit 1
fi

function validate_checksum() {
	echo ">validate checksum"
	cd $SRC
	sha256sum -c $1.xz.sha256
	if [ $? -ne 0 ]; then
		exit 1
	fi
}

function decompress() {
	echo ">decompress"
	cd $SRC
	xz -kfd $1.xz
	cp $1 $DST
}

function setup_loop_device() {
	echo ">setup loop devide"
	cd $DST
	sudo losetup -D
	sudo losetup -P /dev/loop1  $1
}

function modify_boot_partition() {
	echo ">modify boot partition"
	cd $DST
	sudo mount /dev/loop1p1 /mnt
	sudo cp $RELEASE* /mnt
	sudo cp /mnt/config.txt /mnt/config.txt.orig
	sudo cp /mnt/cmdline.txt /mnt/cmdline.txt.orig
	ls -lh /mnt/*.orig
	ls -lh /mnt/meta-data
	ls -lh /mnt/network-config
	ls -lh /mnt/user-data
	sudo umount /mnt
}

function modify_root_partition() {
	echo ">modify root partition"
	cd $DST
	sudo mount /dev/loop1p2 /mnt
	sudo cp /mnt/etc/fstab /mnt/etc/fstab.orig
	ls -lh /mnt/etc/*.orig
	sudo umount /mnt
}

function prepare_image() {
	echo ">prepare image"
	cd $DST
	mv $1 raspios.img
	sha256sum raspios.img > raspios.img.sha256
	ls -lh raspios.img*
}

function compress_image() {
	echo ">compress image"
	cd $DST
	xz -kfz raspios.img
	sha256sum raspios.img.xz > raspios.img.xz.sha256
	ls -lh raspios.img.xz*
}

function clean_up() {
	echo ">clean up"
	sudo losetup -D
}

validate_checksum $1
decompress $1
setup_loop_device $1
modify_boot_partition
modify_root_partition
prepare_image $1
compress_image
clean_up
