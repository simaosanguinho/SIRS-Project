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
    nonce = os.urandom(12) 

    # Encrypt only the target fields
    for field in target_fields:
        if field in encrypted_dict:
            value_to_encrypt = json.dumps(encrypted_dict[field], ensure_ascii=False).encode('utf-8')  # Ensure field value is bytes
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
        if field in encrypted_dict and isinstance(encrypted_dict[field], dict) and "ciphertext" in encrypted_dict[field] and "nonce" in encrypted_dict[field]:
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
@click.argument('output_file')
def check():
    # FIXME
    raise NotImplementedError

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
    