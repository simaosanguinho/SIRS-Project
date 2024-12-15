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

    def setConfig(self, config_path):
        with open(config_path, "r") as file:
            self.config = json.load(file)

        
        
    def is_user_owner(self, user):
        return user in self.config["user"]
    
    # add method to build the car document (carid, user, config, firmware)


app = Flask(__name__)


@app.route("/")
def root():
    return "<h3>Welcome to the Car App!  </h3> Car Id: " + str(car.config["carId"])


@app.route("/maintenance-mode/<mode>")
def maintenance_mode(mode):
    """ if not car.is_user_owner("admin"):
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
        data, "../../test/keys/chacha.key", ["configuration", "firmware"], ["user"]
    )
    config_str = json.dumps(car.config)
    return "Config updated" + config_str

@app.route("/get-config")
def get_config():
    return json.dumps(car.config)


# CHECK BATTERY LEVEL

# Use environment variable to set config path - DEFAULT_CONFIG_PATH
default_config_path = os.getenv("DEFAULT_CONFIG_PATH")
if not default_config_path:
    raise ValueError("DEFAULT_CONFIG_PATH environment variable not set")


if __name__ == "__main__":
    import sys
    car = Car(default_config_path)
    # set different port for car based on id
    port = 5000 + int(sys.argv[1])
    app.run(port=port)
    app.run()
