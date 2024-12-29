#!/usr/bin/env bash

set -euo pipefail

# Initializes Public key Infrastructure.
CA_DIR=./ca
CA_NAME="MotorIST Lda."

mkdir -p $CA_DIR

pushd $CA_DIR
# Create an elliptic curve P-256 keypair for the CA:
openssl ecparam -name prime256v1 -genkey -out key.priv
openssl ec -in "key.priv" -pubout -out "key.pub"

# Generate a CA.
openssl req -x509 -days 3650 -key "key.priv" -out "ca.crt" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "authorityInfoAccess = caIssuers;URI:https://manufacturer.motorist.lan" \
  -addext "keyUsage = critical, keyCertSign" \
  -subj "/C=PT/O=MotorIST Lda./CN=MotorIST Root CA"

#TODO: add this note to report and remove these lines
# Copy it to key store's root, simply to acknowledge every entity knows and can know this file.
# cp ./ca.crt ../

# Verify the public key in the certificate is equal to the key in "key.pub":
echo "Public key in CA's certificate:"
echo
step certificate key ca.crt
echo
echo "Public key in key.pub:"
cat key.pub
echo

popd
# Create a keypair for the CA using ellyptic curve.
# step crypto keypair foo.pub foo.key --kty EC --curve "P-256" \
#     --no-password --insecure
#
# # Initialize a CA.
# # https://smallstep.com/docs/step-cli/reference/ca/init/#usage
# step ca init \
#     --deployment-type=standalone \
#     --name="$CA_NAME" \
#     --profile="root-ca" \
#     --dns="ca.motorist.lan" \
#     --key=key.priv \
#     --root="ca.crt"
#
