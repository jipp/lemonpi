#!/bin/bash -e

install -v -m 644 files/custom.toml "${ROOTFS_DIR}/boot/firmware/custom.toml"
install -v -m 644 files/daemon.json "${ROOTFS_DIR}/etc/docker/daemon.json"
sed -i '$s/$/ cgroup_enable=memory cgroup_memory=1/' "${ROOTFS_DIR}/boot/firmware/cmdline.txt"
