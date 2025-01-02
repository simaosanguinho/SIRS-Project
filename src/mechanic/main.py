from textual.app import App, ComposeResult
from textual.widgets import Footer, Button, Static, Label, Input
from textual.containers import Vertical, Container, Horizontal
from textual.screen import Screen
from textual.theme import Theme
from common import Common
import json
import cryptolib
import os
import sys

# from textual.widgets import Input

MECHANIC_EMAIL = os.getenv("MECHANIC_EMAIL", "messi@mechanic.motorist.lan")


class HomeScreen(Screen):
    """Home screen that displays basic mechanic actions."""

    def compose(self) -> ComposeResult:
        yield Static("Car Management System", id="title")
        yield Label(f"Mechanic ID: {self.app.mechanic_id}", id="mechanic-info")

        # add two buttons to enable and disable maintenance mode
        with Vertical(classes="vertical"):
            yield Container(
                Input(placeholder="Insert Car ID", id="car-id"),
                Static("Update Firmware", classes="section-label"),
                Button("Update Car Firmware", id="update-firmware"),
                classes="controls",
            )
            yield Container(
                Static("Testing:", classes="section-label"),
                Button("Perform Tests", id="tests"),
                classes="controls",
            )

            yield Container(
                Static("Test Configuration:", classes="section-label"),
                Button("Go to Test Configuration", id="go-config"),
                classes="controls",
            )

        # Navigation to Config View
        # Output Display
        yield Static("Output:", id="output")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        global MECHANIC_PRIV_KEY
        """Handle button events and send appropriate requests."""
        button_id = event.button.id
        # app = self.app  # Get reference to the main app instance
        # app = self.app

        try:
            if button_id == "tests":
                self.display_output("Running tests...")
                tests = {}

                for i in range(1, 10):
                    tests[f"test{i}"] = "Passed"
                # convert to string
                self.display_output(str(tests))

                signature = cryptolib.sign_data(MECHANIC_PRIV_KEY, str(tests))

                data = {"tests": tests, "signature": signature}
                response = req.post(f"{Common.CAR_URL}/run-tests", json=data)
                self.display_output(response.text)

            elif button_id == "update-firmware":
                car_id = self.query_one("#car-id", Input).value

                if not car_id:
                    self.display_output("Please enter a car ID")
                    return

                response = update_firmware(car_id)
                self.display_output(response)

            elif button_id == "go-config":
                # Navigate to the UpdateConfigScreen
                self.display_output("Output:")
                self.app.push_screen(UpdateConfigScreen())

        except Exception as e:
            self.display_output(f"Error1: {e}")

    def display_output(self, message: str) -> None:
        """Display output to the user."""
        self.query_one("#output", Static).update(message)


class UpdateConfigScreen(Screen):
    """A dedicated screen for displaying and updating the car configuration."""

    def compose(self) -> ComposeResult:
        yield Static("Car Management System", id="title")
        yield Label(f"Mechanic ID: {self.app.mechanic_id}", id="mechanic-info")
        with Vertical(classes="vertical"):
            with Horizontal(classes="horizontal"):
                yield Container(
                    Label(f"Mechanic ID: {self.app.mechanic_id}", id="mechanic-info"),
                    Button("<", id="back-to-home"),
                    id="controls",
                )

            with Vertical(classes="vertical"):
                yield Static("Edit Car Test Configuration:", id="config-title")
                self.config_input = Input(
                    placeholder="Enter new configuration JSON", id="update-config"
                )
                yield Container(self.config_input)
                yield Button("Update Car Test Configuration", id="send-update-config")
                yield Button("Get Mechanic Configuration", id="get-mechanic-config")

        yield Static("Output:", id="output")
        yield Footer()

    def on_mount(self) -> None:
        """Fetch the current configuration when the screen is mounted."""
        try:
            # Fetch current configuration from Flask API
            response = req.get(f"{Common.CAR_URL}/get-mechanic-config")
            if response.status_code == 200:
                car_unprotected_doc = response.json()
                # Assuming the config is returned as a dictionary
                self.config_input.value = json.dumps(
                    car_unprotected_doc["configuration"]
                )
            else:
                self.display_output("Failed to fetch current configuration.")
        except Exception as e:
            self.display_output(f"Error2: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses on the UpdateConfigScreen."""
        button_id = event.button.id
        # app = self.app

        try:
            if button_id == "send-update-config":
                # Get the value from the input field
                new_config_str = self.query_one("#update-config", Input).value
                new_config = json.loads(new_config_str) if new_config_str else None

                if new_config:
                    car_doc_unprotected = {
                        "configuration": new_config,
                    }

                    response = req.post(
                        f"{Common.CAR_URL}/update-mechanic-config",
                        json=car_doc_unprotected,
                    )

                    self.display_output(response.text)
                else:
                    self.display_output("Please enter a valid configuration JSON.")
            elif button_id == "get-mechanic-config":
                response = req.get(f"{Common.CAR_URL}/get-mechanic-config")
                if response.status_code == 200:
                    car_unprotected_doc = response.json()
                    self.display_output(
                        json.dumps(car_unprotected_doc["configuration"])
                    )
                else:
                    self.display_output("Failed to fetch current configuration.")

            elif button_id == "back-to-home":
                self.display_output("Output:")
                self.app.push_screen("home")
        except Exception as e:
            self.display_output(f"Error3: {e}")

    def display_output(self, message: str) -> None:
        """Display output to the user on the config page."""
        self.query_one("#output", Static).update(message)


def update_firmware(car_id):
    # fetch the firmware from manufacturer and send it to the car
    response = req.get(f"{Common.MANUFACTURER_URL}/get-firmware/{1}")
    if response.status_code != 200:
        return "Failed to fetch firmware"
    print(response.json())

    firmware = response.json()["firmware"]
    signature = response.json()["signature"]
    # DOES THE MECHANIC NEED TO CHECK THE SIGNATURE?
    if not cryptolib.PKI.verify_signature(
        Common.MANUFACTURER_CERT, firmware, signature
    ):
        return "Invalid signature"

    try:
        response = req.post(f"{Common.CAR_URL}/update-firmware", json=response.json())
    except Exception as e:
        return f"Failed to establish connection with car {car_id}: \n{e}"
    print(response.text)
    if response.status_code != 200:
        return "Failed to update firmware"

    return response.text


class MechanicApp(App):
    SCREENS = {"home": HomeScreen}
    BINDINGS = [
        ("h", "push_screen('home')", "Home Screen"),
        ("c", "push_screen('config')", "Config Screen"),
    ]

    # CSS_PATH = "styles.css"
    CSS_PATH = "/var/project-src/mechanic/styles.css"

    # encrypt the mechanic.key with the manufacturer public key

    def __init__(self, mechanic_id):
        super().__init__()
        self.mechanic_id = mechanic_id

    def on_mount(self) -> None:
        self.push_screen("home")


# Define the theme
arctic_theme = Theme(
    name="arctic",
    primary="#88C0D0",
    secondary="#81A1C1",
    accent="#B48EAD",
    foreground="#D8DEE9",
    background="#2E3440",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#3B4252",
    panel="#434C5E",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)


def tui():
    global MECHANIC_EMAIL
    global MECHANIC_PRIV_KEY
    global req
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <MECHANIC_ID>")
        sys.exit(1)

    mechanic_id = sys.argv[1]

    req = Common.get_mutual_tls_session(MECHANIC_EMAIL)

    MECHANIC_PRIV_KEY = os.getenv(
        "MECHANIC_PRIV_KEY", f"{Common.KEY_STORE}/{MECHANIC_EMAIL}/key.priv"
    )
    if not os.path.isfile(MECHANIC_PRIV_KEY):
        print(f"FATAL: mechanic priv key does not exist at {MECHANIC_PRIV_KEY}")
        sys.exit(1)

    MechanicApp(mechanic_id).run()


if __name__ == "__main__":
    tui()
