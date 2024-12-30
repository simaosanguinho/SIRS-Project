from flask import Flask, request, jsonify
import os
import sys
import time
from datetime import datetime
import cryptolib
from psycopg_pool import ConnectionPool
# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 7654
DB_NAME = "motorist-manufacturer-db"
DB_USER = "postgres"
DB_PASSWORD = "password"

PROJECT_ROOT = os.getenv("PROJECT_ROOT", "../../")
KEY_STORE = os.getenv("KEY_STORE", f"{PROJECT_ROOT}/key_store")
MANUF_PRIV_KEY = f"{KEY_STORE}/manufacturer/key.priv"

# Initialize the connection pool
pool = ConnectionPool(
    min_size=1,
    max_size=10,
    conninfo=f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}",
)

class Manufacturer:
    def __init__(self, id):
        self.id = id


app = Flask(__name__)


@app.route("/")
def root():
    return "<h3>Welcome to the Manufacturer App!  </h3> Manufacturer Id: " + str(mechanic.id)


@app.route("/get-firmware/<car_id>", methods=["GET"])
def get_firmware(car_id):
    current_time = time.time()
    formatted_time = datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
    firmware = f"firmware-{car_id}-v{int(current_time)}"
    signature = cryptolib.sign_data(MANUF_PRIV_KEY ,firmware)
    data = {
        "firmware": firmware,
        "signature": signature
    }
    
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
                    "signature": signature
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
    data = {
        "history": data
    }
    for i in range(len(data["history"])):
        data["history"][i] = {
            "firmware": data["history"][i][0],
            "timestamp": data["history"][i][1],
            "signature": data["history"][i][2]
        }
    return jsonify(data)

if __name__ == "__main__":
    mechanic = Manufacturer(sys.argv[1])
    # set different port for manufacturer
    port = 5200 + int(sys.argv[1])
    app.run(port=port)
