# References:
# https://web.archive.org/web/20210928235937/https://www.ajg.id.au/2018/01/01/mutual-tls-with-python-flask-and-werkzeug/
# from base64 import b64decode


# import cryptolib as lib
class Car:
    def __init__(self, car_folder_path: str):
        self.car_keyfile = f"{car_folder_path}/car.key"
        self.car_certfile = f"{car_folder_path}/car.crt"

        # Read and decode the key

    # with open(self.car_keyfile, "r") as key_file:
    # key_base64 = key_file.read().strip()  # Remove newline
    # dummy_key_bytes = b64decode(key_base64)
