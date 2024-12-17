#!/usr/bin/env bash

EMAIL="$1"

if [ -z "$EMAIL" ]; then
  echo "Usage: $0 <email>"
  exit 1
fi

set -euo pipefail

CA_CRT="$(pwd)/ca.crt"
OPENSSL_CONF="$(pwd)/openssl.cnf"
CA_KEY="$(pwd)/ca/key.priv"

mkdir -p "$EMAIL"
pushd "$EMAIL"

# Generate user's key
openssl genrsa -out key.priv 2048
# Generate user's certificate signing request
openssl req -new -key key.priv -out user.csr -subj "/C=PT/O=MotorIST Lda./CN=$EMAIL" \
  -addext "subjectAltName = email:$EMAIL"

# Sign the CSR with the CA's key:
# NOTE: In a real-world scenario, the CA should NOT trust the CSR as the source of truth for subjectAltName.
openssl x509 -req -days 365 -in user.csr -CA "$CA_CRT" \
  -CAkey "$CA_KEY" \
  -out user.crt \
  -copy_extensions copyall # Copying all extensions from a CSR can have
# Verify the created certificate against the CA:
openssl verify -CAfile "$CA_CRT" user.crt
echo "Inspect newly generated certificate":
step certificate inspect user.crt
# TODO: maybe verify all certs with `step certificate lint`

popd
