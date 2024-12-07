import click
import json
import sys
from base64 import b64decode, b64encode
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

@click.group()
def cli():
    pass


@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.argument('output_file')
@click.option('--target_field', '-t', multiple=True, required=True)
@click.option('--authenticated_field', '-a', multiple=True)
def protect(input_file, dummy_key, output_file, target_field: list[str], authenticated_field: list[str]):
    # Open and read the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    print("Original Data:", data)

    # Read and decode the key
    with open(dummy_key, 'r') as key_file:
        key_base64 = key_file.read().strip()  # Remove newline
        dummy_key_bytes = base64.b64decode(key_base64)

    # Ensure the key is of valid length
    if len(dummy_key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes long for AES encryption.")

    aesgcm = AESGCM(dummy_key_bytes)
    nonce = os.urandom(12) 

    # Encrypt only the target fields
    for field in target_field:
        if field in data:
            value_to_encrypt = json.dumps(data[field]).encode('utf-8')  # Ensure field value is bytes
            encrypted_value = aesgcm.encrypt(nonce, value_to_encrypt, None)  # Replace `aad` with None or valid data
            # Replace the original value with the encrypted value (Base64 encoded for storage)
            data[field] = {
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "ciphertext": base64.b64encode(encrypted_value).decode('utf-8')
            }

    print("Encrypted Data:", data)

    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)

    # Decryption
    for field in target_field:
        if field in data and isinstance(data[field], dict) and "ciphertext" in data[field] and "nonce" in data[field]:
            stored_nonce = base64.b64decode(data[field]["nonce"])
            stored_ciphertext = base64.b64decode(data[field]["ciphertext"])
            decrypted_value = aesgcm.decrypt(stored_nonce, stored_ciphertext, None)
            print(f"Decrypted value for {field}:", json.loads(decrypted_value))



@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.argument('output_file')
def unprotect():
    # FIXME
    raise NotImplementedError

@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.argument('output_file')
def check():
    # FIXME
    raise NotImplementedError

@cli.command()
@click.argument('output_file')
def generate_key(output_file):
    # FIXME
    raise NotImplementedError
 


#@cli.command()
# try to see if I can have the command be different from the function name. 
# this function breaks python REPL.
#def help():
#    # FIXME
#    raise NotImplementedError


def encrypt_data(data, aad, key=None, nonce=None):
    if not nonce:
        nonce = os.urandom(12)

    chacha = ChaCha20Poly1305(key)
    return chacha.encrypt(nonce, data, aad)

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


def bytes_to_dict(data: bytes) -> dict:
    return json.loads(data)


#def encrypt_field(doc: dict, key: bytes, field: str, authenticated_fields: list[str]):

#    if not key:
#        key = ChaCha20Poly1305.generate_key()
    
#click.option('--count', default=1, help='number of greetings')
#@click.argument('name')

if __name__ == '__main__':
    if not sys.flags.interactive:
        cli()
    