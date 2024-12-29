from flask import Flask
import requests
import cryptolib


class Mechanic:
    def __init__(self, id):
        self.id = id


app = Flask(__name__)


@app.route("/")
def root():
    return "<h3>Welcome to the Mechanic App!  </h3> Mechanic Id: " + str(mechanic.id)


## ENDPOINTS

# See the usre configuration - to show that even when he has the key he cannot see the user config

# Change config of the car - to show that the mechanic can change
# the config of the car (only when in maintenance mode)


@app.route("/update-firmware")
def update_firmware():
    # fetch the firmware from manufacturer and send it to the car
    response = requests.get(f"{manufacturer_url}/get-firmware/{1}")
    if response.status_code != 200:
        return "Failed to fetch firmware"
    print(response.json())

    firmware = response.json()["firmware"]
    signature = response.json()["signature"]
    # DOES THE MECHANIC NEED TO CHECK THE SIGNATURE?
    if not cryptolib.verify_signature(
        "../../test/keys/user1.pubkey", firmware, signature
    ):
        return "Invalid signature"

    # send the firmware to the car
    response = requests.post(f"{car_url}/update-firmware", json=response.json())
    print(response.text)

    return response.text


if __name__ == "__main__":
    import sys

    mechanic = Mechanic(sys.argv[1])
    # set different port for mechanic
    car_url = f"http://127.0.0.1:{5000 + int(1)}"
    manufacturer_url = f"http://127.0.0.1:{5200 + int(1)}"
    port = 5100 + int(sys.argv[1])
    app.run(port=port)
    app.run()
