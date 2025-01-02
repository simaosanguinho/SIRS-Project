from flask import Flask, jsonify
import os
import sys
import time
from datetime import datetime
import cryptolib
from psycopg_pool import ConnectionPool


# Database connection parameters
PG_CONNSTRING = os.getenv(
    "PG_CONNSTRING",
    "host=localhost port=7654 dbname=motorist-manufacturer-db user=postgres password=password",
)
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "../../")
KEY_STORE = os.getenv("KEY_STORE", f"{PROJECT_ROOT}/key_store")
MANUF_PRIV_KEY = f"{KEY_STORE}/manufacturer/key.priv"
ROOT_CA_PATH = f"{KEY_STORE}/ca.crt"


# Initialize the connection pool
pool = ConnectionPool(
    min_size=1,
    max_size=10,
    conninfo=PG_CONNSTRING,
)


class Manufacturer:
    def __init__(self, id):
        self.id = id
        self.key_store = f"{KEY_STORE}/manufacturer"


app = Flask(__name__)


@app.route("/")
def root():
    return "<h3>Welcome to the Manufacturer App!  </h3> Manufacturer Id: " + str(
        manufacturer.id
    )


@app.route("/get-firmware/<car_id>", methods=["GET"])
def get_firmware(car_id):
    current_time = time.time()
    formatted_time = datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
    firmware = f"firmware-{car_id}-v{int(current_time)}"
    signature = cryptolib.sign_data(MANUF_PRIV_KEY, firmware)
    data = {"firmware": firmware, "signature": signature}

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO firmware_requests (car_id, firmware, timestamp, signature)
                VALUES (%(car_id)s, %(firmware)s, %(timestamp)s, %(signature)s);
                """,
                {
                    "car_id": car_id,
                    "firmware": firmware,
                    "timestamp": formatted_time,
                    "signature": signature,
                },
            )
        conn.commit()

    return jsonify(data)


@app.route("/get-history/<car_id>", methods=["GET"])
def get_history(car_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT firmware, timestamp, signature
                FROM firmware_requests
                WHERE car_id = %(car_id)s;
                """,
                {
                    "car_id": car_id,
                },
            )
            data = cur.fetchall()
    data = {"history": data}
    for i in range(len(data["history"])):
        data["history"][i] = {
            "firmware": data["history"][i][0],
            "timestamp": data["history"][i][1],
            "signature": data["history"][i][2],
        }
    return jsonify(data)


def start():
    global manufacturer
    manufacturer = Manufacturer(sys.argv[1])
    # set different port for manufacturer
    port = 5200 + int(sys.argv[1])

    app.run(
        port=port,
        ssl_context=(
            f"{manufacturer.key_store}/entity.crt",
            f"{manufacturer.key_store}/key.priv",
        ),
    )
