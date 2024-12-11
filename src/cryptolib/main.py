import click
import json
import sys
from base64 import b64decode, b64encode
import base64
import os

#TODO: make this dynamic by taking AEAD algorithm dynamically
# e.g       from cryptography.hazmat.primitives.ciphers import aead 
#           aead.__all__['AESGCM']
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from rich import pretty
from rich import print
import datetime
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidTag

@click.group()
def cli():
    pass

EncryptionAlgo = ChaCha20Poly1305

@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.argument('output_file')
@click.option('--target_fields', '-t', multiple=True, required=True)
@click.option('--authenticated_fields', '-a', multiple=True)
def protect(input_file, dummy_key, output_file, target_fields: list[str], authenticated_fields: list[str]):
    # Open and read the JSON file
    with open(input_file, 'r') as file:
        encrypted_dict = json.load(file)
    print("Original encrypted_dict:", encrypted_dict)

    # Read and decode the key
    with open(dummy_key, 'r') as key_file:
        key_base64 = key_file.read().strip()  # Remove newline
        dummy_key_bytes = base64.b64decode(key_base64)

    # Ensure the key is of valid length
    if len(dummy_key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes long for AES encryption.")

    encryption_algo = EncryptionAlgo(dummy_key_bytes)
    #TODO: use secrets module instead of urandom
    nonce = os.urandom(12) #

    # Encrypt only the target fields
    for field in target_fields:
        if field in encrypted_dict:
            value_to_encrypt = json.dumps(encrypted_dict[field], ensure_ascii=False).encode('utf-8')  # Ensure field value is bytes
            #TODO: use authenticated fields param
            encrypted_value = encryption_algo.encrypt(nonce, value_to_encrypt, None)  # Replace `aad` with None or valid encrypted_dict
            # Replace the original value with the encrypted value (Base64 encoded for storage)
            encrypted_dict[field] = {
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "ciphertext": base64.b64encode(encrypted_value).decode('utf-8')
            }

    print("Encrypted encrypted_dict:", encrypted_dict)

    with open(output_file, 'w') as file:
        json.dump(encrypted_dict, file, indent=4, ensure_ascii=False)

    # Decryption
    for field in target_fields:
        if field in encrypted_dict and isinstance(encrypted_dict[field], dict) and "ciphertext" in encrypted_dict[field] and "nonce" in encrypted_dict[field]:
            stored_nonce = base64.b64decode(encrypted_dict[field]["nonce"])
            stored_ciphertext = base64.b64decode(encrypted_dict[field]["ciphertext"])
            decrypted_value = encryption_algo.decrypt(stored_nonce, stored_ciphertext, None) #TODO aead
            print(f"Decrypted value for {field}:", json.loads(decrypted_value))


@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.argument('output_file')
@click.option('--target_fields', '-t', multiple=True, required=True)
@click.option('--authenticated_fields', '-a', multiple=True)
def unprotect(input_file, dummy_key, output_file, target_fields: list[str], authenticated_fields: list[str]):
    # Open and read the JSON file
    with open(input_file, 'r') as file:
        encrypted_dict = json.load(file)

    print("Encrypted encrypted_dict:", encrypted_dict)

    # Read and decode the key
    with open(dummy_key, 'r') as key_file:
        key_base64 = key_file.read().strip()  # Remove newline
        dummy_key_bytes = base64.b64decode(key_base64)

    data = decrypt(encrypted_dict, dummy_key_bytes, target_fields, authenticated_fields)
    print(f"Decrypted data: {data}")
    with open(output_file, 'w+') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def decrypt(encrypted_dict, key_bytes, target_fields, authenticated_fields):
    encryption_algo = EncryptionAlgo(key_bytes)

    final_dict = {}

    # Decryption
    for field in target_fields:
        if not (field in encrypted_dict and isinstance(encrypted_dict[field], dict) and "ciphertext" in encrypted_dict[field] and "nonce" in encrypted_dict[field]):
            raise ValueError("Invalid arguments!")

        stored_nonce = base64.b64decode(encrypted_dict[field]["nonce"])
        stored_ciphertext = base64.b64decode(encrypted_dict[field]["ciphertext"])
        print(f"Decrypting field {field}")
#           print(f"stored_nonce={stored_nonce}\nstored_ciphertext={stored_ciphertext}, aead=None")
        decrypted_value = encryption_algo.decrypt(stored_nonce, stored_ciphertext, None) #aead
        print(f"Decrypted value for {field}:", json.loads(decrypted_value))
        #return json.loads(decrypted_ata)

@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.option('--target_fields', '-t', multiple=True, required=True)
@click.option('--authenticated_fields', '-a', multiple=True)
def check(input_file, dummy_key, target_fields, authenticated_fields):
    try:
        # Open and read the JSON file
        with open(input_file, 'r') as file:
            encrypted_dict = json.load(file)

        # Read and decode the key
        with open(dummy_key, 'r') as key_file:
            key_base64 = key_file.read().strip()  # Remove newline
            dummy_key_bytes = base64.b64decode(key_base64)

        print(f"encrypted_dict = {encrypted_dict}")
        decrypt(encrypted_dict, dummy_key_bytes, target_fields, authenticated_fields)

        return True

    except InvalidTag:
        print(f"Check for file {input_file} has failed!")
        return False
    except Exception as e:
        print(f"Uncaught excpetion! {e}")


@cli.command()
@click.argument('output_file')
def generate_key(output_file):
    key = ChaCha20Poly1305.generate_key()
    with open(output_file, "wb+") as f:
        key_encoded = b64encode(key)
        print(f"key_encoded={key_encoded}")
        f.write(key_encoded)


#@cli.command()
# try to see if I can have the command be different from the function name. 
# this function breaks python REPL.
#def help():
#    # FIXME
#    raise NotImplementedError



def encrypt_data(encrypted_dict, aad, key=None, nonce=None):
    if not nonce:
        nonce = os.urandom(12)
    chacha = ChaCha20Poly1305(key)
    return chacha.encrypt(nonce, encrypted_dict, aad)

def dict_to_bytes(d: dict, keys: list[str]=None):
    """
    TODO: docstrings
    """
    if not keys:
        final_d = d
    else:
        final_d = {}
        for key in keys:
            final_d[key] = d[key]

    return bytes(json.dumps(final_d, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def bytes_to_dict(encrypted_dict: bytes) -> dict:
    return json.loads(encrypted_dict)

class PKI:
    """
    Manages (MotorIST) Public Key Infrastructure.
    """

    def __init__(self):
        self.subject = self.issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PT"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Lisbon"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Lisbon"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MotorIST Lda."),
            x509.NameAttribute(NameOID.COMMON_NAME, "MotorIST Root CA"),
        ])
        self.root_key = None


    def gen_root_ca(self, duration=None):
        if not self.root_key:
            # Generate our key
            self.root_key = ec.generate_private_key(ec.SECP256R1())

        if not duration:
            duration = datetime.timedelta(days=365*10)

        self.root_cert = x509.CertificateBuilder().subject_name(
            self.subject
        ).issuer_name(
            self.issuer
        ).public_key(
            self.root_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            # Our certificate will be valid for ~10 years
            datetime.datetime.now(datetime.timezone.utc) + duration
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(self.root_key.public_key()),
            critical=False,
        ).sign(self.root_key, hashes.SHA256())

    def gen_int_ca(self):
        if not (self.root_key and self.root_cert):
            raise ValueError("No root key and/or cert defined.")
        # Generate our intermediate key
        int_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PT"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Lisbon"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Lisbon"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Motorist Lda."),
            x509.NameAttribute(NameOID.COMMON_NAME, "MotorIST Root CA"),
        ])
        self.int_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.root_cert.subject
        ).public_key(
            int_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            # Our intermediate will be valid for ~3 years
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365*3)
        ).add_extension(
            # Allow no further intermediates (path length 0)
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(int_key.public_key()),
            critical=False,
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                self.root_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
            ),
            critical=False,
        ).sign(self.root_key, hashes.SHA256())

    def gen_server_cert(self, server_name):
        # Generate and end-entity cert and key.
        ee_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
        ])
        ee_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.int_cert.subject
        ).public_key(
            ee_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            # Our cert will be valid for 10 days
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
        ).add_extension(
            x509.SubjectAlternativeName([
                # Describe what sites we want this certificate for.
                x509.DNSName(server_name),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ee_key.public_key()),
            critical=False,
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                self.int_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
            ),
            critical=False,
        ).sign(self.int_key, hashes.SHA256())

#TODO: serialize keys & certs to disk

    def verify_cert(self):
        return NotImplementedError
#def encrypt_field(doc: dict, key: bytes, field: str, authenticated_fields: list[str]):

#    if not key:
#        key = ChaCha20Poly1305.generate_key()
    
#click.option('--count', default=1, help='number of greetings')
#@click.argument('name')

if __name__ == '__main__':
    if not sys.flags.interactive:
        cli()
    else:
        pretty.install()
    