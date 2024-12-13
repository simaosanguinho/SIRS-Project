# Car

Flask app that represents the car

### How to run it?

```
export DEFAULT_CONFIG_PATH=../../test/input.json
flask --app main.py run
```

### Available Endpoints:

- /update-config the client can change a car config

```sh
curl -X POST http://127.0.0.1:5000/update-config \
-H "Content-Type: application/json" \
-d '{
    "carId": 1,
    "user": "user1",
    "configuration": {
        "nonce": "RpuhCQqQjbKS2DYN",
        "ciphertext": "WVn5v5dKqxn7EXaKcaaFLTj2X5WwJyKqjIRUMnLlKatwJsrbvZNJ/cR6pgRFe+EDlPQi0HeogKN7havirUFfGsAwf83XuE68uHQWF2+90mkPRNgIe5fw7H3byeh0acTrD2KSn3i+bciA8PiIlUW+vIa4L64xB6/S+mahkA=="
    },
    "firmware": {
        "nonce": "RpuhCQqQjbKS2DYN",
        "ciphertext": "AEm6OQnrI5FxKRwMi0oDmLVdHQ=="
    }
}'

```
