#!/usr/bin/env bash

sudo ip link add name car1-intra type bridge
sudo ip link set dev car1-intra up
