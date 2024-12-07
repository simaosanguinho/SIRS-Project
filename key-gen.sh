#!/usr/bin/env bash

# Check if the number of users is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <number_of_users>"
    exit 1
fi

# Get the number of users
num_users=$1

# Ensure the input is a valid positive integer
if ! [[ "$num_users" =~ ^[0-9]+$ ]] || [ "$num_users" -le 0 ]; then
    echo "Error: Please enter a valid positive integer for the number of users."
    exit 1
fi

# Create the keys directory if it doesn't exist
mkdir -p keys

# Loop to generate key pairs for each user
for (( i=1; i<=num_users; i++ ))
do
    privkey_file="keys/user${i}.privkey"
    pubkey_file="keys/user${i}.pubkey"

    # Generate private key
    openssl genpkey -algorithm RSA -out "$privkey_file" -pkeyopt rsa_keygen_bits:2048

    # Extract the public key
    openssl rsa -pubout -in "$privkey_file" -out "$pubkey_file"

    echo "Generated keys for user$i: $privkey_file, $pubkey_file"
done

# Generate a symmetric key for testing
# Key must be 16, 24, or 32 bytes long for AES encryption.
openssl rand -base64 24 > keys/symmetric.key





echo "Key generation complete for $num_users users."
