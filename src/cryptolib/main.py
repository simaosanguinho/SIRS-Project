import click
import json
import sys
from base64 import b64decode, b64encode
import os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


@click.group()
def cli():
    pass

@cli.command()
@click.argument('input_file')
@click.argument('dummy_key')
@click.argument('output_file')
@click.option('--target_field', '-t', multiple=True, required=True)
@click.option('--authenticated_field', '-a', multiple=True)
# <cli> protect <input_file <dummy_key> <output_file> -t json_field -a authenticated_field
def protect(input_file, dummy_key, output_file, target_field: list[str], authenticated_field: list[str]):
    # FIXME
    raise NotImplementedError

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
    