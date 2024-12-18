import requests
import os
import cryptolib

# Configuration
MANUFACTURER_URL = "http://127.0.0.1:5201"  # Adjust port as needed
CAR_ID = 2
PUBLIC_KEY_PATH = "./keys/user1.pubkey"


def fetch_firmware_and_signature(url, car_id):
    """Fetch firmware and signature from the Manufacturer App."""
    response = requests.get(f"{url}/get-firmware/{car_id}")
    if response.status_code == 200:
        data = response.json()
        return data["firmware"], data["signature"]
    else:
        raise Exception(
            f"Failed to fetch firmware data: {response.status_code}, {response.text}"
        )


def main():

    # Step 1: Fetch firmware and signature
    print("Fetching firmware and signature...")
    try:
        firmware, signature = fetch_firmware_and_signature(MANUFACTURER_URL, CAR_ID)
        print(f"Firmware: {firmware}")
        print(f"Signature: {signature}")
    except Exception as e:
        print(e)
        return

    # ================================================
    # Test 1: Verify the original signature
    print("\nVerifying original signature...")
    if cryptolib.verify_signature(PUBLIC_KEY_PATH, firmware, signature):
        print("Original signature verification: SUCCESS")
    else:
        print("Original signature verification: FAILURE")

    # ================================================
    # Test 2: Modify the signature and verify again
    print("\nTesting with modified signature...")
    # append random char to the signature
    modified_signature = signature[:7] + "x" + signature[8:]
    if cryptolib.verify_signature(PUBLIC_KEY_PATH, firmware, modified_signature):
        print("Modified signature verification: SUCCESS (This should not happen!)")
    else:
        print("Modified signature verification: FAILURE (Expected)")

    # ================================================
    # Test 3: Modify the firmware and verify again
    print("\nTesting with modified firmware...")
    # append random char to the firmware
    modified_firmware = firmware + "x"
    if cryptolib.verify_signature(PUBLIC_KEY_PATH, modified_firmware, signature):
        print("Modified firmware verification: SUCCESS (This should not happen!)")
    else:
        print("Modified firmware verification: FAILURE (Expected)")


if __name__ == "__main__":
    main()
