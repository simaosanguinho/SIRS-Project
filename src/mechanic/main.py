from flask import Flask, request
import json
import os

import cryptolib.main as cryptolib


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

# Turn on maintenance mode???? - QUESTION



if __name__ == "__main__":
    import sys
    mechanic = Mechanic(sys.argv[1])
    # set different port for mechanic
    port = 5100 + int(sys.argv[1])
    app.run(port=port)
    app.run()