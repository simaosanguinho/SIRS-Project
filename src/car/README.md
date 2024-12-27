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
        "nonce": "rh8vYjTDPfqVnpbU",
        "ciphertext": "Zms6TnhM0FB+e7Ci+K3UNmz2N04sN4nx9Wto7vRRV9n5kIlMHPb8S9EVXYVnEEHbWvq5DVIjFFkjtPj+1eK3DBIlp8nVbK4ukL99Ikq1qV3zBHOS3QwEF3GZj1M2mFJvIGV99qYn+91VRS4IlNFCmx8rFiSy0HNxbpuyGsPD1mNkN9Vj9DSh1NgdggY5wvUJlaM="
    },
    "firmware": {
        "nonce": "rh8vYjTDPfqVnpbU",
        "ciphertext": "P3t5WuC0YYkF4Mr+cUxzjm1Q7A=="
    }
}'

```
