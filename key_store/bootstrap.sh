#!/usr/bin/env bash

# Delete EVERYTHING in the key_store folder that is included in gitignore.
git clean -d -f -X ./

# Init CA
./init_ca.sh

# Init servers
servers=(manufacturer-web manufacturer-db car1-db car1-web)

for item in "${servers[@]}"; do
  ./gen_entity.sh $item
done

# Init clients
./gen_entity.sh ronaldo@user.motorist.lan user 1
./gen_entity.sh messi@mechanic.motorist.lan mechanic
./gen_entity.sh johndoe@user.motorist.lan user

# Init car keys
./gen_car_key.sh ronaldo@user.motorist.lan
