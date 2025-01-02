import requests
import sys
import os
from cryptolib import PKI


class Common:
    PROJECT_ROOT = os.getenv("PROJECT_ROOT", "../../")
    KEY_STORE = os.getenv("KEY_STORE", f"{PROJECT_ROOT}/key_store")
    ROOT_CA_PATH = f"{KEY_STORE}/ca.crt"
    MANUFACTURER_CERT = PKI.load_certificate(f"{KEY_STORE}/manufacturer.crt")
    CAR_PORT = os.getenv("CAR_PORT", "5001")
    CAR_URL = os.getenv("CAR_URL", f"https://127.0.0.1:{CAR_PORT}")
    MANUFACTURER_PORT = os.getenv("MANUFACTURER_PORT", "5201")
    MANUFACTURER_URL = os.getenv(
        "MANUFACTURER_URL", f"https://127.0.0.1:{MANUFACTURER_PORT}"
    )

    @staticmethod
    def get_tls_session():
        s = requests.Session()

        if not os.path.isfile(Common.ROOT_CA_PATH):
            print(f"FATAL ERROR: FILE {Common.ROOT_CA_PATH} does not exist!")
            sys.exit(1)

        s.verify = Common.ROOT_CA_PATH
        return s

    @staticmethod
    def get_mutual_tls_session(entity_name):
        entity_crt = f"{Common.KEY_STORE}/{entity_name}/entity.crt"
        entity_key = f"{Common.KEY_STORE}/{entity_name}/key.priv"

        # verify all files exist - panic otherwise.
        must_exit = False
        for critical_file in [entity_crt, entity_key, Common.ROOT_CA_PATH]:
            if not os.path.isfile(critical_file):
                must_exit = True
                print(f"FATAL ERROR: FILE {critical_file} does not exist!")
            if must_exit:
                sys.exit(1)

        s = requests.Session()
        s.verify = Common.ROOT_CA_PATH
        s.cert = (entity_crt, entity_key)

        return s
