#!/usr/bin/env bash

# An entity is either a user, where an e-mail should be passed as the first argument,
#    (e.g, ceo@motorist.lan )
# or a machine, where its hostname (<machine_name>.motorist.lan) should be passed instead.
ENTITY="$1"

if [ -z "$ENTITY" ]; then
  echo "Usage (servers): $0 <hostname>"
  echo "Usage (clients): $0 <username> <entity's role> [car the user is owner of]"
  echo "Usage examples:"
  echo "$0 car1-db"
  echo "$0 johndoe@mechanic.motorist.lan mechanic"
  echo "$0 mike_the_car_owner@user.motorist.lan user car1"
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
# If it's an e-mail (first argument contains an '@'), generate a CSR with the `email` attribute:
if [[ $ENTITY =~ '@' ]]; then
  EXTRA_ALT_NAME1=""
  EXTRA_ALT_NAME2=""
  if [[ $# -ge 2 ]]; then
    MOTORIST_ROLE="$2"
    # Adds an additional extension to the certificate, binding the entity
    # that owns this certificate's public key to a role in MotorIST.
    EXTRA_ALT_NAME1=", otherName:1.2.3.4.1;UTF8:motorist_role--$MOTORIST_ROLE"
  fi
  if [[ $# -eq 3 ]]; then
    MOTORIST_CAROWNER="$3"
    # Adds an additional extension to the certificate, binding the entity
    # that owns this certificate's public key as the owner of a MotorIST car.
    EXTRA_ALT_NAME2=", otherName:1.2.3.4.2;UTF8:motorist_carowner--$MOTORIST_CAROWNER"
  fi
  openssl req -new -key key.priv -out entity.csr -subj "/C=PT/O=MotorIST Lda./CN=${ENTITY}" \
    -addext "subjectAltName = email:${ENTITY}${EXTRA_ALT_NAME1}${EXTRA_ALT_NAME2}"
  # Otherwise, assume the entity is a server:
else
  openssl req -new -key key.priv -out entity.csr -subj "/C=PT/O=MotorIST Lda./CN=${ENTITY}" \
    -addext "subjectAltName = DNS:$ENTITY.motorist.lan"
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
