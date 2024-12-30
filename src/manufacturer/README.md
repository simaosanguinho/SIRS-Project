# Manufacturer

Flask app that represents the manufacturer

### How to run it?

First, you need to generate the manufacturer's private key and public key.

To create a database, simply run the following command:

```bash
docker compose up
```

This will create a database with the necessary tables, which will be running on port 7654 locally.

Finally, to run the manufacturer server, run the following command:

```bash
python3 main.py <Manufacturer ID>
```

Ports start at address 5200.

### Available Endpoints:

- `/get-firmware/<car_id>`: Get the firmware for a specific car
- `/get-history/<car_id>`: Get the history of a specific car
