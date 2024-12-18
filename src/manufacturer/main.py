from flask import Flask, request, jsonify
import time
import cryptolib

class Manufacturer:
    def __init__(self, id):
        self.id = id


app = Flask(__name__)


@app.route("/")
def root():
    return "<h3>Welcome to the Manufacturer App!  </h3> Manufacturer Id: " + str(mechanic.id)


@app.route("/get-firmware/<car_id>", methods=["GET"])
def get_firmware(car_id):
    firmware = f"firmware-{car_id}-v{int(time.time())}"
    signature = cryptolib.sign_data("../../test/keys/user1.privkey",firmware)
    data = {
        "firmware": firmware,
        "signature": signature
    }
    return jsonify(data)

if __name__ == "__main__":
    import sys
    mechanic = Manufacturer(sys.argv[1])
    # set different port for manufacturer
    port = 5200 + int(sys.argv[1])
    app.run(port=port)
    app.run()
