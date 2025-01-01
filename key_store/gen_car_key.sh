#!/usr/bin/env bash

echo "Generating key"
key=$(openssl rand -base64 32)

mkdir -p ./$1
echo "Saving key to $1/car.key"
echo $key > ./$1/car.key
