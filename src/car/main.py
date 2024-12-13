from flask import Flask, request
import json
import os

import cryptolib.main as cryptolib


class Car:
    def __init__(self, default_config):
        self.maintnaince_mode = False
        self.config = {}
        with open(default_config, "r") as file:
            self.config = json.load(file)
            print("Default Config", self.config)

    def updateConfig(self, client_config):
        self.config.update(client_config)
        return "Config updated"

    def is_user_owner(self, user):
        return user in self.config["user"]


app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/maintenance-mode/<mode>")
def maintenance_mode(mode):
    if not car.is_user_owner("admin"):
        return "User not authorized to change maintenance mode"

    if mode == "on":
        car.maintnaince_mode = True
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
        data, "../../test/keys/chacha.key", ["configuration", "firmware"], ["user"]
    )
    config_str = json.dumps(car.config)
    return "Config updated" + config_str


# Use environment variable to set config path - DEFAULT_CONFIG_PATH
config_path = os.getenv("DEFAULT_CONFIG_PATH")
if not config_path:
    raise ValueError("DEFAULT_CONFIG_PATH environment variable not set")

car = Car(config_path)
