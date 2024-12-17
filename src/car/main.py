from flask import Flask, request
import json
import os

import cryptolib.main as cryptolib


class Car:
    def __init__(self, default_config, car_id, owner_id):
        self.maintnaince_mode = False
        self.config = {}
        self.id = car_id
        self.user_id = owner_id
        self.battery_level = 100
        self.op_count = 0
        with open(default_config, "r") as file:
            self.config = json.load(file)
            print("Default Config", self.config)

    def setConfig(self, config_path):
        with open(config_path, "r") as file:
            self.config = json.load(file)

    def is_user_owner(self, user):
        return user in self.config["user"]

    # add method to build the car document (carid, user, config, firmware)
    def build_car_document(self, config):
        return {
            "carID": self.id,
            "user": self.user_id,
            "config": config,
            "firmware": "v1.0",
        }


app = Flask(__name__)


@app.route("/")
def root():
    return "<h3>Welcome to the Car App!  </h3> Car ID: " + str(car.id)


@app.route("/maintenance-mode/<mode>")
def maintenance_mode(mode):
    """if not car.is_user_owner("admin"):
    return "User not authorized to change maintenance mode" """

    if mode == "on":
        car.maintnaince_mode = True
        # set car config to default
        car.setConfig(default_config_path)
    elif mode == "off":
        car.maintnaince_mode = False
    else:
        return "Invalid mode"
    return f"Maintenance mode is {mode}"


@app.route("/update-config", methods=["POST"])
def update_config():
    data = request.get_json()
    print("Data Received", data)
    print("Type", type(data))

    # TODO: Add validation for the data
    # Change the hardcoded values

    car.config = cryptolib.unprotect_lib(
        data, "../../test/keys/chacha.key", ["configuration", "firmware"]
    )
    config_str = json.dumps(car.config)

    car.op_count += 1
    if car.op_count >= 10:
        car.op_count = 0
        car.battery_level -= 5

    return "Config updated" + config_str


@app.route("/get-config")
def get_config():
    return json.dumps(car.config)


@app.route("/check-battery")
def check_battery():
    return f"Battery Level: {car.battery_level} %"


@app.route("/charge-battery")
def charge_battery():
    car.battery_level = 100
    car.op_count = 0
    return check_battery()


# DEBUG ENDPOINTS
@app.route("/debug/get-doc")
def get_car_document():
    return json.dumps(car.build_car_document(car.config))


# Use environment variable to set config path - DEFAULT_CONFIG_PATH
default_config_path = os.getenv("DEFAULT_CONFIG_PATH")
if not default_config_path:
    raise ValueError("DEFAULT_CONFIG_PATH environment variable not set")


if __name__ == "__main__":
    import sys

    car = Car(default_config_path, sys.argv[1], sys.argv[2])
    # set different port for car based on id
    port = 5000 + int(sys.argv[1])
    app.run(port=port)
    app.run()
