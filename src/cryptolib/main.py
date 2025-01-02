import click
import json
import sys
from base64 import b64encode
import base64
import secrets
from rich import pretty
from rich import print
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509 import Certificate
from cryptography.x509.oid import ExtensionOID
from cryptography.x509.verification import PolicyBuilder, Store, VerificationError
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


class PKI:
    """
    Manages (MotorIST) Public Key Infrastructure.
    References:
      - https://cryptography.io/en/43.0.1/x509/verification/
      - https://cryptography.io/en/43.0.1/x509/reference/#general-name-classes
    """

    def __init__(self, root_cacert_path):
        self.root_ca = PKI.load_certificate(root_cacert_path)
        self.store = Store([self.root_ca])

    # Not yet sure if needed.
    # def verify_server_cert(self, cert: Certificate, dns_name: str):
    #     builder = PolicyBuilder().store(self.store)
    #     builder = builder.time(datetime.now())
    #     verifier = builder.build_server_verifier(DNSName(dns_name))
    #     return verifier.verify(cert, [])

    # Verifies if a client certificate is valid.
    def verify_client_cert(self, cert: Certificate) -> tuple[bool, str]:
        builder = PolicyBuilder().store(self.store)
        builder = builder.time(datetime.now())
        verifier = builder.build_client_verifier()
        try:
            verified_client = verifier.verify(cert, [])
            # Assume a client certificate only contains one subject a.k.a email identifier.
            return (True, verified_client.subjects[0].value)

        except VerificationError:
            # Client's certificate is not valid.
            return (False, None)

    @staticmethod
    def __get_subject_names(cert: Certificate):
        return cert.extensions.get_extension_for_oid(
            ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        ).value

    @staticmethod
    def get_subject_email(cert: Certificate) -> list:
        # Assume only one e-mail per subject in our context.
        return PKI.__get_subject_names(cert).get_values_for_type(x509.RFC822Name)[0]

    @staticmethod
    def get_san_custom_oid(cert: Certificate, oid: str):
        """
        Fetches data from a certificate, identified by a custom (arbitrary) extension OID.

        https://docs.openssl.org/3.4/man5/x509v3_config/#arbitrary-extensions
        """
        # Our custom objects are stored in the certificate, according to RFC5280.
        # They are stored as `Subject Alternative Names` of the `otherName` type.
        other_names = PKI.__get_subject_names(cert).get_values_for_type(x509.OtherName)

        # Since our values of otherName contain data in a custom format (i.e. have a custom OID),
        # OpenSSL will not know how to correctly parse its data when adding it to a certificate.
        # It's up to the implementors of the custom OID to correctly handle the data.
        for other_name in other_names:
            if other_name.type_id.dotted_string == oid:
                return other_name.value[2:].decode("utf-8")
        return None

    @staticmethod
    def verify_signature(cert: Certificate, data, signature) -> bool:
        """Verifies the signature of the given data using a certificate's public key."""
        data_hash = sha256_hash(data)
        signature = base64.b64decode(signature)
        public_key = cert.public_key()

        try:
            public_key.verify(
                signature,
                data_hash.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception as e:
            print("Signature verification failed with exception: ", e)
            return False

    @staticmethod
    def load_certificate(cert_path=None, cert_binary=None):
        if cert_path:
            with open(cert_path, "rb") as f:
                cert_bytes = f.read()
            return x509.load_pem_x509_certificate(cert_bytes)
        elif cert_binary:
            return x509.load_der_x509_certificate(cert_binary)

        raise ValueError("must specify either cert_path or cert_binary")

    @staticmethod
    def encrypt_data(data, cert_path):
        """Encrypts data using a certificate's public key."""
        cert = PKI.load_certificate(cert_path)
        public_key = cert.public_key()
        encrypted_data = public_key.encrypt(
            data.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted_data).decode("utf-8")

    @staticmethod
    def decrypt_data(encrypted_data, private_key_path):
        """Decrypts data using a private key."""
        encrypted_data = base64.b64decode(encrypted_data)
        private_key = load_private_key(private_key_path)
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return decrypted_data.decode("utf-8")


if __name__ == "__main__":
    if not sys.flags.interactive:
        cli()
    else:
        pretty.install()
