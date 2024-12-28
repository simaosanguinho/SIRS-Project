#!/usr/bin/env bash

# An entity is either a user, where an e-mail should be passed as the first argument,
#    (e.g, ceo@motorist.lan )
# or a machine, where its hostname (<machine_name>.motorist.lan) should be passed instead.
ENTITY="$1"

if [ -z "$ENTITY" ]; then
  echo "Usage: $0 <entity's email or dns name>"
  exit 1
fi

set -euo pipefail

CA_CRT="$(pwd)/ca.crt"
OPENSSL_CONF="$(pwd)/openssl.cnf"
CA_KEY="$(pwd)/ca/key.priv"

mkdir -p "$ENTITY"
pushd "$ENTITY"

# Generate the entity's key
openssl genrsa -out key.priv 2048

# Generate entity's certificate signing request (CSR)
#   Note the only difference between a user and a machine is the SAN attribute in the certificate.
if [[ $ENTITY =~ '@' ]]; then
  # If it's an e-mail (contains an '@'), generate a CSR with the `email` attribute.
  openssl req -new -key key.priv -out entity.csr -subj "/C=PT/O=MotorIST Lda./CN=$ENTITY" \
    -addext "subjectAltName = email:$ENTITY"
else
  openssl req -new -key key.priv -out entity.csr -subj "/C=PT/O=MotorIST Lda./CN=$ENTITY" \
    -addext "subjectAltName = DNS:$ENTITY"
fi

# Sign the CSR with the CA's key:
# NOTE: In a real-world scenario, the CA should NOT trust the CSR as the source of truth for subjectAltName.
openssl x509 -req -days 365 -in entity.csr -CA "$CA_CRT" \
  -CAkey "$CA_KEY" \
  -out entity.crt \
  -copy_extensions copyall # Copying all extensions from a CSR can have
# Verify the created certificate against the CA:
openssl verify -CAfile "$CA_CRT" entity.crt
echo "Inspect newly generated certificate":
step certificate inspect entity.crt
# TODO: maybe verify all certs with `step certificate lint`

popd
