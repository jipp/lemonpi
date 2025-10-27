#!/bin/bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh --dry-run
sudo sh get-docker.sh
sudo usermod -aG docker $USER

sudo sed -i 's/$/ cgroup_enable=memory cgroup_memory=1/' /boot/firmware/cmdline.txt

cat /etc/docker/daemon.json 
{
  "debug": false,
  "experimental": true,
  "live-restore": true,
  "ipv6": true,
  "ip6tables": true,
  "fixed-cidr-v6": "fd00:affe::/64",
  "default-address-pools": [
    { "base": "10.0.0.0/8", "size": 24 },
    { "base": "172.16.0.0/12", "size": 24 },
    { "base": "192.168.0.0/16", "size": 24 },
    { "base": "fd00:affe:1::/48", "size": 64 },
    { "base": "fd00:affe:2::/48", "size": 64 },
    { "base": "fd00:affe:3::/48", "size": 64 },
    { "base": "fd00:affe:4::/48", "size": 64 },
    { "base": "fd00:affe:5::/48", "size": 64 },
    { "base": "fd00:affe:6::/48", "size": 64 },
    { "base": "fd00:affe:7::/48", "size": 64 },
    { "base": "fd00:affe:8::/48", "size": 64 }
  ]
}

