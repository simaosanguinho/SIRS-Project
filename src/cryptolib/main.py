import click
import json
import sys
from base64 import b64encode
import base64
import secrets
from rich import pretty
from rich import print
import datetime

# TODO: make this dynamic by taking AEAD algorithm dynamically
# from cryptography.hazmat.primitives.ciphers import aead
# aead.__all__['AESGCM']
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from cryptography import x509
from cryptography.exceptions import InvalidTag


@click.group()
def cli():
    pass

EncryptionAlgo = ChaCha20Poly1305
@cli.command()
@click.argument("input_file")
@click.argument("dummy_key")
@click.argument("output_file")
@click.option("--target_fields", "-t", multiple=True, required=True)
def protect(
    input_file: str,
    dummy_key: str,
    output_file: str,
    target_fields: list[str],
) -> None:
    """
    Command that encrypts the target fields in the input JSON file and writes
    the result to the output file.

    Args:
        input_file (str): json file to be encrypted
        dummy_key (str): key file to be used for encryption
        output_file (str): output file to write the encrypted data
        target_fields (list[str]): json fields to be encrypted
    """
    with open(input_file, "r", encoding="utf-8") as file:
        data_dict = json.load(file)

    encrypted_data_dict = protect_lib(data_dict, dummy_key, target_fields)
    print(f"Encrypted data: {encrypted_data_dict}")

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(encrypted_data_dict, file, indent=4, ensure_ascii=False)


def protect_lib(
    data_dict: dict,
    dummy_key: str,
    target_fields: list[str],
) -> dict:
    """
    Encrypts the target fields in the input dictionary and returns the encrypted
    dictionary.

    Args:
        data_dict (dict): dictionary to be encrypted
        dummy_key (str): key file to be used for encryption
        target_fields (list[str]): fields to be encrypted

    Returns:
        dict: the dictionary with the target fields encrypted
    """

    with open(dummy_key, "r", encoding="utf-8") as key_file:
        dummy_key_bytes = base64.b64decode(key_file.read().strip())

    nonce = secrets.token_bytes(12)

    for field in target_fields:
        if field in data_dict:
            value_to_encrypt = json.dumps(data_dict[field], ensure_ascii=False).encode(
                "utf-8"
            )

            encrypted_value = EncryptionAlgo(dummy_key_bytes).encrypt(
                nonce, value_to_encrypt, None
            )

            # Replace the original value with the encrypted value (Base64 encoded for storage)
            data_dict[field] = {
                "nonce": base64.b64encode(nonce).decode("utf-8"),
                "ciphertext": base64.b64encode(encrypted_value).decode("utf-8"),
            }

    return data_dict


@cli.command()
@click.argument("input_file")
@click.argument("dummy_key")
@click.argument("output_file")
@click.option("--target_fields", "-t", multiple=True, required=True)
def unprotect(
    input_file: str,
    dummy_key: str,
    output_file: str,
    target_fields: list[str],
) -> None:
    """
    Command that decrypts the target fields in the input JSON file and writes
    the result to the output file.

    Args:
        input_file (str): json file to be decrypted
        dummy_key (str): key file to be used for decryption
        output_file (str): output file to write the decrypted data
        target_fields (list[str]): json fields to be decrypted
    """

    with open(input_file, "r", encoding="utf-8") as file:
        encrypted_data_dict = json.load(file)

    decrypted_data_dict = unprotect_lib(encrypted_data_dict, dummy_key, target_fields)
    print(f"Decrypted data: {decrypted_data_dict}")

    with open(output_file, "w+", encoding="utf-8") as file:
        json.dump(decrypted_data_dict, file, indent=4, ensure_ascii=False)


def unprotect_lib(
    encrypted_dict: dict, dummy_key: str, target_fields: list[str]
) -> dict:
    """
    Decrypts the target fields in the input dictionary and returns the decrypted

    Args:
        encrypted_dict (dict): dictionary to be decrypted
        dummy_key (str): key file to be used for decryption
        target_fields (list[str]): fields to be decrypted

    Returns:
        dict: the dictionary with the target fields decrypted
    """

    with open(dummy_key, "r", encoding="utf-8") as key_file:
        dummy_key_bytes = base64.b64decode(key_file.read().strip())

    data = decrypt(encrypted_dict, dummy_key_bytes, target_fields)
    return data


def decrypt(encrypted_dict: dict, key_bytes: bytes, target_fields: list[str]) -> dict:
    """
    Decrypts the target fields in the input dictionary and returns the decrypted dictionary.

    Args:
        encrypted_dict (dict): dictionary to be decrypted
        key_bytes (bytes): key to be used for decryption
        target_fields (list[str]): fields to be decrypted

    Raises:
        ValueError: When the field is not in the dictionary or the field is not encrypted

    Returns:
        dict: the dictionary with the target fields decrypted
    """

    decrypted_dict = encrypted_dict.copy()

    for field in target_fields:
        if not (
            field in encrypted_dict
            and isinstance(encrypted_dict[field], dict)
            and "ciphertext" in encrypted_dict[field]
            and "nonce" in encrypted_dict[field]
        ):
            raise ValueError("Invalid arguments for field: ", field)

        stored_nonce = base64.b64decode(encrypted_dict[field]["nonce"])
        stored_ciphertext = base64.b64decode(encrypted_dict[field]["ciphertext"])

        decrypted_value = EncryptionAlgo(key_bytes).decrypt(
            stored_nonce, stored_ciphertext, None
        )
        print(f"Decrypted value for {field}:", json.loads(decrypted_value))
        decrypted_dict[field] = json.loads(decrypted_value)

    return decrypted_dict


@cli.command()
@click.argument("input_file")
@click.argument("dummy_key")
@click.option("--target_fields", "-t", multiple=True, required=True)
def check(input_file: str, dummy_key: str, target_fields: list[str]) -> bool:
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            encrypted_dict = json.load(file)

        with open(dummy_key, "r", encoding="utf-8") as key_file:
            dummy_key_bytes = base64.b64decode(key_file.read().strip())

        decrypt(encrypted_dict, dummy_key_bytes, target_fields)
        return True

    except InvalidTag:
        print(f"Check for file {input_file} has failed!")
        return False
    except Exception as e:
        print(f"Uncaught excpetion! {e}")
        return False


@cli.command()
@click.argument("output_file")
def generate_key(output_file: str):
    key = ChaCha20Poly1305.generate_key()
    with open(output_file, "wb+") as f:
        key_encoded = b64encode(key)
        print(f"key_encoded={key_encoded}")
        f.write(key_encoded)

def load_private_key(file_path):
    """Loads an RSA private key from a file."""
    with open(file_path, "rb") as key_file:
        private_key = load_pem_private_key(
            key_file.read(), password=None, backend=default_backend()
        )
    return private_key


def load_public_key(file_path):
    """Loads an RSA public key from a file."""
    with open(file_path, "rb") as key_file:
        public_key = load_pem_public_key(key_file.read(), backend=default_backend())
    return public_key


def sha256_hash(data):
    """Calculates the SHA-256 hash of the given data."""
    hash_object = hashlib.sha256(data.encode("utf-8"))
    sha256 = hash_object.hexdigest()
    return sha256


def sign_data(file_path, data):
    """Signs the given data (SHA-256 hash) using the private key."""
    # Calculate hash
    private_key = load_private_key(file_path)
    # data to bytes
    data_hash = sha256_hash(data)

    # Sign the hash
    signature = private_key.sign(
        data_hash.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    signature = base64.b64encode(signature)

    return signature.decode("utf-8")


def verify_signature(file_path, data, signature):
    """Verifies the signature of the given data using the public key."""
    data_hash = sha256_hash(data)
    # Decode the signature
    signature = base64.b64decode(signature)
    # Load the public key
    public_key = load_public_key(file_path)

    try:
        public_key.verify(
            signature,
            data_hash.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return True
    except Exception as e:
        print("Verification failed:", e)
        return False


class PKI:
    """
    Manages (MotorIST) Public Key Infrastructure.
    """

    def __init__(self):
        self.subject = self.issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "PT"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Lisbon"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Lisbon"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MotorIST Lda."),
                x509.NameAttribute(NameOID.COMMON_NAME, "MotorIST Root CA"),
            ]
        )
        self.root_key = None

    def gen_root_ca(self, duration=None):
        if not self.root_key:
            # Generate our key
            self.root_key = ec.generate_private_key(ec.SECP256R1())

        if not duration:
            duration = datetime.timedelta(days=365 * 10)

        self.root_cert = (
            x509.CertificateBuilder()
            .subject_name(self.subject)
            .issuer_name(self.issuer)
            .public_key(self.root_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(
                # Our certificate will be valid for ~10 years
                datetime.datetime.now(datetime.timezone.utc) + duration
            )
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
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
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(self.root_key.public_key()),
                critical=False,
            )
            .sign(self.root_key, hashes.SHA256())
        )

    def gen_int_ca(self):
        if not (self.root_key and self.root_cert):
            raise ValueError("No root key and/or cert defined.")
        # Generate our intermediate key
        int_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "PT"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Lisbon"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Lisbon"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Motorist Lda."),
                x509.NameAttribute(NameOID.COMMON_NAME, "MotorIST Root CA"),
            ]
        )
        self.int_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.root_cert.subject)
            .public_key(int_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(
                # Our intermediate will be valid for ~3 years
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=365 * 3)
            )
            .add_extension(
                # Allow no further intermediates (path length 0)
                x509.BasicConstraints(ca=True, path_length=0),
                critical=True,
            )
            .add_extension(
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
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(int_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    self.root_cert.extensions.get_extension_for_class(
                        x509.SubjectKeyIdentifier
                    ).value
                ),
                critical=False,
            )
            .sign(self.root_key, hashes.SHA256())
        )

    def gen_server_cert(self, server_name):
        # Generate and end-entity cert and key.
        ee_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
            ]
        )
        ee_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.int_cert.subject)
            .public_key(ee_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(
                # Our cert will be valid for 10 days
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=10)
            )
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        # Describe what sites we want this certificate for.
                        x509.DNSName(server_name),
                    ]
                ),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
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
            )
            .add_extension(
                x509.ExtendedKeyUsage(
                    [
                        x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                        x509.ExtendedKeyUsageOID.SERVER_AUTH,
                    ]
                ),
                critical=False,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(ee_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    self.int_cert.extensions.get_extension_for_class(
                        x509.SubjectKeyIdentifier
                    ).value
                ),
                critical=False,
            )
            .sign(self.int_key, hashes.SHA256())
        )

    # TODO: serialize keys & certs to disk

    def verify_cert(self):
        return NotImplementedError


if __name__ == "__main__":
    if not sys.flags.interactive:
        cli()
    else:
        pretty.install()
