#!/bin/bash

# Script to run the Python program with the specified arguments

# Variables
PROGRAM="../src/cryptolib/main.py"
TARGET="input.json"
SYMKEY="./keys/symmetric.key"
OUTPUT="output.json"

# run the key generation script
bash ../key-gen.sh 1

if [ ! -f $TARGET ]; then
    echo "Creating target file: $TARGET"
    echo "{}" > $TARGET
fi

# Execute the command

if [ "$1" == "run_protect" ]; then
    python3 $PROGRAM protect $TARGET $SYMKEY $OUTPUT -t configuration -a user
fi

