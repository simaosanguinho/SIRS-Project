from flask import Flask, request, jsonify
import time
import cryptolib
from psycopg_pool import ConnectionPool
# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 7654
DB_NAME = "motorist-manufacturer-db"
DB_USER = "postgres"
DB_PASSWORD = "password"
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
    current_time = int(time.time())
    firmware = f"firmware-{car_id}-v{current_time}"
    signature = cryptolib.sign_data("../../test/keys/user1.privkey",firmware)
    data = {
        "firmware": firmware,
        "signature": signature
    }
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO firmware_requests (car_id, firmware, timestamp)
                VALUES (%(car_id)s, %(firmware)s, %(timestamp)s);
                """,
                {
                    "car_id": car_id,
                    "firmware": firmware,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
        conn.commit()
    
    return jsonify(data)

if __name__ == "__main__":
    import sys
    mechanic = Manufacturer(sys.argv[1])
    # set different port for manufacturer
    port = 5200 + int(sys.argv[1])
    app.run(port=port)
    app.run()
