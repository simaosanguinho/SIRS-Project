from flask import Flask, request
import json
import os
import cryptolib
from cryptolib import PKI
import requests
from psycopg_pool import ConnectionPool
import sys
from enum import Enum

import werkzeug.serving
import ssl

# Database connection parameters
PG_CONNSTRING = os.getenv(
    "PG_CONNSTRING",
    "host=localhost port=7464 dbname=motorist-car-db user=postgres password=password",
)
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "../../")
KEY_STORE = os.getenv("KEY_STORE", f"{PROJECT_ROOT}/key_store")
MANUFACTURER_CERT = PKI.load_certificate(f"{KEY_STORE}/manufacturer.crt")
ROOT_CA_PATH = f"{KEY_STORE}/ca.crt"

app = Flask(__name__)


# Source: https://web.archive.org/web/20210928235937/https://www.ajg.id.au/2018/01/01/mutual-tls-with-python-flask-and-werkzeug/
class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    """
    We subclass this class so that we can gain access to the connection
    property. self.connection is the underlying client socket. When a TLS
    connection is established, the underlying socket is an instance of
    SSLSocket, which in turn exposes the getpeercert() method.

    The output from that method is what we want to make available elsewhere
    in the application.
    """

    def make_environ(self):
        """
        The superclass method develops the environ hash that eventually
        forms part of the Flask request object.

        We allow the superclass method to run first, then we insert the
        peer certificate into the hash. That exposes it to us later in
        the request variable that Flask provides
        """
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()
        x509_binary = self.connection.getpeercert(binary_form=True)

        peer_cert = PKI.load_certificate(cert_binary=x509_binary)
        environ["peercert"] = peer_cert
        return environ


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
    def __init__(self, default_config, car_id, owner_id=None):
        self.maintenance_mode = False
        self.config = {}
        self.mechanic_config = {}
        self.firmware = {}
        self.id = car_id
        self.user_id = owner_id
        self.battery_level = 100
        self.op_count = 0
        self.car_name = f"car{car_id}"
        self.key_store = f"{KEY_STORE}/{self.car_name}-web"
        self.car_key = None
        self.initialized = False
        self.default_config = default_config
        print(f"DEBUG: {self.key_store}")
        if self.car_key:
            self.complete_init()

    def complete_init(self):
        # if there is a config in the database, use that
        config = None

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
            with open(self.default_config, "r") as file:
                self.config = json.load(file)
                print("Default Config", self.config)
                config_protected = cryptolib.protect_lib(
                    # FIXME: dont use hardcoded key
                    self.config,
                    f"{self.car_key}",
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
        self.initialized = True

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
    if not car.car_key:
        return "Not allowed without a key", 503
    return "<h3>Welcome to the Car App!  </h3> Car ID: " + str(car.id)


@app.route("/set-car-key", methods=["POST"])
def set_car_key():
    data = request.get_json()
    encrypted_car_key = data["key"]
    car.car_key = PKI.decrypt_data(encrypted_car_key, f"{car.key_store}/key.priv")
    if not car.initialized:
        car.complete_init()
    return "Car key set successfully"


@app.route("/maintenance-mode/<mode>")
def maintenance_mode(mode):
    """if not car.is_user_owner("admin"):
    return "User not authorized to change maintenance mode" """

    if not car.car_key:
        return "Not allowed without a key", 503
    if mode == "on":
        car.maintenance_mode = True
        # set car config to default
        with open(car.default_config, "r") as file:
            car.mechanic_config = json.load(file)
        print("Default Config", car.mechanic_config)

    elif mode == "off":
        car.mechanic_config = {}
        car.maintenance_mode = False
    else:
        return "Invalid mode"
    return f"Maintenance mode is {mode}"


@app.route("/update-config", methods=["POST"])
def update_config():
    if not car.car_key:
        return "Not allowed without a key", 503
    data = request.get_json()
    print("Data Received", data)
    print("Type", type(data))

    # TODO: Add validation for the data - check car id and user id
    # Change the hardcoded values

    try:
        """unprotected_data = cryptolib.unprotect_lib(
            data, f"{car.key_store}/car.key", ["configuration"]
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


@app.route("/update-mechanic-config", methods=["POST"])
def update_mechanic_config():
    if not car.maintenance_mode:
        return "Maintenance Mode is off", 504
    data = request.get_json()
    print("Data Received", data)
    print("Type", type(data))

    try:
        config = data["configuration"]
        car.mechanic_config = config

    except Exception as e:
        return f"Error: {e}"


@app.route("/get-mechanic-config")
def get_mechanic_config():
    if not car.maintenance_mode:
        return "Maintenance Mode is off", 504
    return json.dumps(car.mechanic_config)


@app.route("/get-config")
def get_config():
    if not car.car_key:
        return "Not allowed without a key", 503
    try:
        config = car.get_current_config()
        return config
    except Exception as e:
        return f"Error: {e}"


@app.route("/check-battery")
def check_battery():
    if not car.car_key:
        return "Not allowed without a key", 503
    return f"Battery Level: {car.battery_level} %"


@app.route("/charge-battery")
def charge_battery():
    if not car.car_key:
        return "Not allowed without a key", 503
    car.battery_level = 100
    car.op_count = 0
    return "Battery has been charged to 100%"


# DEBUG ENDPOINTS
@app.route("/debug/get-doc")
def get_car_document():
    if not car.car_key:
        return "Not allowed without a key", 503
    return json.dumps(car.build_car_document(car.config))


@app.route("/debug/whoami")
def whoami():
    if not car.car_key:
        return "Not allowed without a key", 503
    return str(request.environ["peercert"])


# TODO: Add endpoint to update firmware
@app.route("/update-firmware", methods=["POST"])
def update_firmware():
    if not car.car_key:
        return "Not allowed without a key", 503
    try:
        # check maintenance mode
        data = request.get_json()
        firmware = data["firmware"]
        signature = data["signature"]
        return car.update_firmware(firmware, signature)
    except Exception as e:
        return f"Error: {e}"


# Use environment variable to set config path - DEFAULT_CONFIG_PATH
default_config_path = os.getenv(
    "DEFAULT_CONFIG_PATH", f"{os.path.dirname(__file__)}/default_config.json"
)
if not default_config_path:
    raise ValueError("DEFAULT_CONFIG_PATH environment variable not set")


if __name__ == "__main__":
    manufacturer_url = f"http://127.0.0.1:{5200 + int(1)}"

    car = Car(default_config_path, sys.argv[1], sys.argv[2])
    # set different port for car based on id
    port = 5000 + int(sys.argv[1])

    # create_default_context establishes a new SSLContext object that
    # aligns with the purpose we provide as an argument. Here we provide
    # Purpose.CLIENT_AUTH, so the SSLContext is set up to handle validation
    # of client certificates.
    ssl_context = ssl.create_default_context(
        purpose=ssl.Purpose.CLIENT_AUTH, cafile=ROOT_CA_PATH
    )

    # load in the certificate and private key for our server to provide to clients.
    # force the client to provide a certificate.
    ssl_context.load_cert_chain(
        certfile=f"{car.key_store}/entity.crt",
        keyfile=f"{car.key_store}/key.priv",
        password="",
    )
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    app.run(
        port=port, ssl_context=ssl_context, request_handler=PeerCertWSGIRequestHandler
    )
