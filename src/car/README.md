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
        "nonce": "WqrOG7T8Byua95wX",
        "ciphertext": "BL8nih7IXoizrzD8QZugFaw8qw+xzdDA66IrbOtYgkn7lCH97TugvpaJ2+hkKzyd1NUWRkDRrNsvQ0Li68arBFCyTUyyovzMUPBPcsTBeme9FBI8imMkCEFzgywUScMQBaOlb5nHLb64LR66NBgFeh5CwUhAGg4DzTcM5C+ZdFzQImSa1q55Ee8M+SzPDr4="
    },
    "firmware": {"nonce": "WqrOG7T8Byua95wX", "ciphertext": "Xa9k+LtOspIVGtSlU0b+Uozx1g=="}
}'

```
