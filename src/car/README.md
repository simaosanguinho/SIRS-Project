# Car

Flask app that represents the car

### How to run it?

```
export DEFAULT_CONFIG_PATH=../../test/input.json
python3 main.py <CAR_ID>
```

Ports start at address 5000.

### Available Endpoints:

- /update-config the client can change a car config

```sh
curl -X POST http://127.0.0.1:5001/update-config \
-H "Content-Type: application/json" \
-d '{
  "carId": 1,
  "user": "user1",
  "configuration": {
    "nonce": "y4GTeAOllv4s28VY",
    "ciphertext": "FiOITJ1bG6R1pDUcsbtfw+gkU6x0ATwpMVDil62+qWQsrQilhG65Hx1Pqcc1PtjlNwUY4kd9HgqfqRM+W9xCzq/LeZPOmiMk7lRmmn6EeGTNVVIHZMJIvmd0P00oS88FZQSvUQmx0QFRot/bxDVnDAFg9RSx5msp714X2ckRCXjdzg8BzlAGaBnouKW2vb0="
  },
  "firmware": {
    "nonce": "y4GTeAOllv4s28VY",
    "ciphertext": "TzPLs+RjC13OvJX25mvfF3NiyA=="
  }
}'

```
