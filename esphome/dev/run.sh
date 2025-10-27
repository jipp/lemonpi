#!/usr/bin/sh

docker run --rm --network host -v "${PWD}":/config -it esphome/esphome $1 $2
