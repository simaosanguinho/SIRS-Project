from flask import Flask, request
import json
import os
import cryptolib
from cryptolib import PKI
import requests
from psycopg_pool import ConnectionPool
import sys
from enum import Enum

app = Flask(__name__)

# Database connection parameters
PG_CONNSTRING = os.getenv(
    "PG_CONNSTRING",
    "host=localhost port=7464 dbname=motorist-car-db user=postgres password=password",
)
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "../../")
KEY_STORE = os.getenv("KEY_STORE", f"{PROJECT_ROOT}/key_store")
MANUFACTURER_CERT_PATH = f"{KEY_STORE}/manufacturer.crt"
MANUFACTURER_CERT = PKI.load_certificate(MANUFACTURER_CERT_PATH)

# Initialize the connection pool
pool = ConnectionPool(
    min_size=1,
    max_size=10,
    conninfo=PG_CONNSTRING,
)


class Role(Enum):
    User = 1
    Mechanic = 2


class Entity:
    def __init__(self, cert):
        self.email = PKI.get_subject_email(cert)
        role_attr = PKI.get_san_custom_oid(cert, "1.2.3.4.1")
        carowner_attr = PKI.get_san_custom_oid(cert, "1.2.3.4.2")

        # TODO: verify certificate
        if role_attr:
            role_name = role_attr.removeprefix("motorist_role--")
            self.role = Role(role_name)
        if carowner_attr:
            self.car_owner = role_attr.removeprefix("motorist_carowner--")


class Car:
    def __init__(self, default_config, car_id, owner_id):
        self.maintenance_mode = False
        self.config = {}
        self.firmware = {}
        self.id = car_id
        self.user_id = owner_id
        self.battery_level = 100
        self.op_count = 0
        config = None
        # if there is a config in the database, use that
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT config
                        FROM configurations
                        WHERE car_id = %(car_id)s
                        AND user_id = %(user_id)s
                        ORDER BY id DESC
                        LIMIT 1;
                        """,
                        {"car_id": self.id, "user_id": self.user_id},
                    )
                    config = cur.fetchone()
        except Exception as e:
            raise (e)
        # existent config was found
        if config:
            self.config = config[0]
            print("Config from DB", self.config)
        # no config found, use default
        else:
            with open(default_config, "r") as file:
                self.config = json.load(file)
                print("Default Config", self.config)
                config_protected = cryptolib.protect_lib(
                    self.config,
                    "../../test/keys/chacha.key",
                    ["configuration"],
                )
                print("Default Config", config_protected)
                self.store_update(json.dumps(config_protected["configuration"]))

        # do the same with the firmware
        firmware = None
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT firmware
                        FROM firmwares
                        WHERE car_id = %(car_id)s
                        ORDER BY id DESC
                        LIMIT 1;
                        """,
                        {"car_id": self.id},
                    )
                    firmware = cur.fetchone()
        except Exception as e:
            raise (e)
        # existent firmware was found
        if firmware:
            self.firmware = firmware[0]
            print("Firmware from DB", self.firmware)

        else:
            # ask for a new firmware from the manufacturer
            response = requests.get(f"{manufacturer_url}/get-firmware/{1}")
            if response.status_code != 200:
                print("Failed to fetch firmware")
            print(response.json())
            firmware = response.json()["firmware"]
            signature = response.json()["signature"]
            self.update_firmware(firmware, signature)
            print("Firmware from Manufacturer", firmware)

    def setConfig(self, config_path):
        with open(config_path, "r") as file:
            self.config = json.load(file)

    def is_user_owner(self, user: Entity):
        return user in self.config["user"]

    # add method to build the car document (carid, user, config)
    def build_car_document(self, config):
        return {
            "carID": self.id,
            "user": self.user_id,
            "config": config,
        }

    def store_update(self, config):
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO configurations (car_id, user_id, config)
                        VALUES (%(car_id)s, %(user_id)s, %(config)s);
                        """,
                        {
                            "car_id": self.id,
                            "user_id": self.user_id,
                            "config": config,
                        },
                    )
                conn.commit()
        except Exception as e:
            raise (e)

    def get_current_config(self):
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT config
                        FROM configurations
                        WHERE car_id = %(car_id)s
                        AND user_id = %(user_id)s
                        ORDER BY id DESC
                        LIMIT 1;
                        """,
                        {"car_id": self.id, "user_id": self.user_id},
                    )
                    config = cur.fetchone()

            protected_car_config = {
                "carId": self.id,
                "user": self.user_id,
                "configuration": config[0],
            }
            print("Protected Config", protected_car_config)
            return json.dumps(protected_car_config)

        except Exception as e:
            raise (e)

    def update_firmware(self, firmware, signature):
        print("Updating Firmware")
        print("Maintenance Mode: ", self.maintenance_mode)
        # check if maintenance mode is on
        if not self.maintenance_mode:
            return "Firmware Update Failed: Maintenance Mode is Off"

        if not PKI.verify_signature(MANUFACTURER_CERT, firmware, signature):
            return "Invalid signature"

        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO firmwares (car_id, firmware, signature, timestamp)
                        VALUES (%(car_id)s, %(firmware)s, %(signature)s, NOW());
                        """,
                        {
                            "car_id": self.id,
                            "firmware": firmware,
                            "signature": signature,
                            "timestamp": "NOW()",
                        },
                    )
                conn.commit()
        except Exception as e:
            raise (e)

        return "Firmware Updated Successfully"


@app.route("/")
def root():
    return "<h3>Welcome to the Car App!  </h3> Car ID: " + str(car.id)


@app.route("/maintenance-mode/<mode>")
def maintenance_mode(mode):
    """if not car.is_user_owner("admin"):
    return "User not authorized to change maintenance mode" """

    if mode == "on":
        car.maintenance_mode = True
        # set car config to default
        car.setConfig(default_config_path)
    elif mode == "off":
        car.maintenance_mode = False
    else:
        return "Invalid mode"
    return f"Maintenance mode is {mode}"


@app.route("/update-config", methods=["POST"])
def update_config():
    data = request.get_json()
    print("Data Received", data)
    print("Type", type(data))

    # TODO: Add validation for the data - check car id and user id
    # Change the hardcoded values

    try:
        """unprotected_data = cryptolib.unprotect_lib(
            data, "../../test/keys/chacha.key", ["configuration"]
        )
        car.config = unprotected_data["configuration"]"""

        # store the update protected
        car.store_update(json.dumps(data["configuration"]))

    except Exception as e:
        return f"Error2: {e}"

    car.op_count += 1
    if car.op_count >= 10 and car.battery_level > 0:
        car.op_count = 0
        car.battery_level -= 5

    return "Config Updated Sucessfully"


@app.route("/get-config")
def get_config():
    try:
        config = car.get_current_config()
        return config
    except Exception as e:
        return f"Error: {e}"


@app.route("/check-battery")
def check_battery():
    return f"Battery Level: {car.battery_level} %"


@app.route("/charge-battery")
def charge_battery():
    car.battery_level = 100
    car.op_count = 0
    return "Battery has been charged to 100%"


# DEBUG ENDPOINTS
@app.route("/debug/get-doc")
def get_car_document():
    return json.dumps(car.build_car_document(car.config))


@app.route("/debug/whoami")
def whoami():
    return "FIXME"
    # return json.dumps(car.build_car_document(car.config))


# TODO: Add endpoint to update firmware
@app.route("/update-firmware", methods=["POST"])
def update_firmware():
    try:
        # check maintenance mode
        data = request.get_json()
        firmware = data["firmware"]
        signature = data["signature"]
        return car.update_firmware(firmware, signature)
    except Exception as e:
        return f"Error: {e}"


# Use environment variable to set config path - DEFAULT_CONFIG_PATH
default_config_path = os.getenv("DEFAULT_CONFIG_PATH")
if not default_config_path:
    raise ValueError("DEFAULT_CONFIG_PATH environment variable not set")


if __name__ == "__main__":
    manufacturer_url = f"http://127.0.0.1:{5200 + int(1)}"

    car = Car(default_config_path, sys.argv[1], sys.argv[2])
    # set different port for car based on id
    port = 5000 + int(sys.argv[1])
    app.run(port=port)
    app.run()
