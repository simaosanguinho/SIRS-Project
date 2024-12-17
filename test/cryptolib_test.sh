#!/usr/bin/env bash

# Script to run the Python program with the specified arguments

# Variables
PROGRAM="../src/cryptolib/main.py"
INPUT="input.json"
AES_KEY="./keys/symmetric.key"
CHACHA_KEY="./keys/chacha.key"
OUTPUT_PROTECTED="output_protected.json"
OUTPUT_UNPROTECTED="output_unprotected.json"

# run the key generation script
#bash ../key-gen.sh 1

if [ ! -f $INPUT ]; then
  echo "Creating input file: $INPUT"
  echo "{}" >$INPUT
fi

# Execute the command
if [ "$1" == "run_protect" ]; then
  python3 $PROGRAM protect $INPUT $CHACHA_KEY $OUTPUT_PROTECTED -t configuration -t firmware
fi

if [ "$1" == "run_unprotect" ]; then
  python3 $PROGRAM unprotect $OUTPUT_PROTECTED $CHACHA_KEY $OUTPUT_UNPROTECTED -t configuration -t firmware
fi

if [ "$1" == "gen_key_aes" ]; then
  python3 $PROGRAM generate-key $AES_KEY
fi

if [ "$1" == "gen_key_chacha" ]; then
  python3 $PROGRAM generate-key $CHACHA_KEY
fi
