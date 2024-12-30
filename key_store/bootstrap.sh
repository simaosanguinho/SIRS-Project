#!/usr/bin/env bash

# Delete EVERYTHING uncommitted in the key_store folder.
git restore --source=HEAD --staged --worktree -- ./

# Init CA
./init_ca.sh

# Init servers
servers=(manufacturer manufacturer-db car1-db car1-web)

for item in "${servers[@]}"; do
  ./gen_entity.sh $item
done

# Init clients
./gen_entity.sh ronaldo@user.motorist.lan user car1
./gen_entity.sh messi@mechanic.motorist.lan mechanic
./gen_entity.sh johndoe@user.motorist.lan user
