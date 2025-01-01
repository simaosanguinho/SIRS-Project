from textual.app import App, ComposeResult
from textual.widgets import Footer, Button, Static, Label
from textual.containers import Horizontal, Vertical, Container
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Input
import requests
import cryptolib
import json
import os
from cryptolib import PKI


PROJECT_ROOT = os.getenv("PROJECT_ROOT", "../../")
KEY_STORE = os.getenv("KEY_STORE", f"{PROJECT_ROOT}/key_store")
USER = os.getenv("USER", "ronaldo@user.motorist.lan")

class HomeScreen(Screen):
    """Home screen that displays basic car management options."""

    def compose(self) -> ComposeResult:
        yield Static("Car Management System", id="title")
        yield Label(
            f"Car ID: {self.app.car_id} | Owner ID: {self.app.owner_id}", id="car-info"
        )

        # Maintenance Mode Controls
        with Vertical(classes="vertical"):
            with Horizontal(classes="horizontal"):
                yield Container(
                    Static("Maintenance Mode:", classes="section-label"),
                    Button("Enable", id="maintenance-on"),
                    Button("Disable", id="maintenance-off"),
                    classes="controls",
                )

                yield Container(
                    # Battery Controls
                    Static("Battery Management:", classes="section-label"),
                    Button("Check Battery", id="check-battery"),
                    Button("Charge Battery", id="charge-battery"),
                    classes="controls",
                )

            with Horizontal(classes="horizontal"):
                yield Container(
                    # Config View Navigation
                    Static("Car Configuration:", classes="section-label"),
                    Button("Get Car Configuration", id="get-config"),
                    Button("Update Car Configuration", id="go-config"),
                    classes="car-config-btn",
                )

        # Navigation to Config View
        # Output Display
        yield Static("Output:", id="output")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button events and send appropriate requests."""
        button_id = event.button.id
        app = self.app  # Get reference to the main app instance

        try:
            if button_id == "maintenance-on":
                response = requests.get(f"{app.flask_url}/maintenance-mode/on")
                if response.status_code == 503:
                    requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                    response = requests.get(f"{app.flask_url}/maintenance-mode/on")
                self.display_output(response.text)

            elif button_id == "maintenance-off":
                response = requests.get(f"{app.flask_url}/maintenance-mode/off")
                if response.status_code == 503:
                    requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                    response = requests.get(f"{app.flask_url}/maintenance-mode/off")
                self.display_output(response.text)

            elif button_id == "check-battery":
                response = requests.get(f"{app.flask_url}/check-battery")
                if response.status_code == 503:
                    requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                    response = requests.get(f"{app.flask_url}/check-battery")
                self.display_output(response.text)

            elif button_id == "charge-battery":
                response = requests.get(f"{app.flask_url}/charge-battery")
                if response.status_code == 503:
                    requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                    response = requests.get(f"{app.flask_url}/charge-battery")
                self.display_output(response.text)

            elif button_id == "get-config":
                response = requests.get(f"{app.flask_url}/get-config")
                if response.status_code == 503:
                    requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                    response = requests.get(f"{app.flask_url}/get-config")
                car_unprotected_doc = cryptolib.unprotect_lib(
                    response.json(), f"{app.key_store}/car.key", ["configuration"]
                )
                self.display_output(
                    "Current Configuration: "
                    + json.dumps(car_unprotected_doc["configuration"])
                )

            elif button_id == "go-config":
                # Navigate to the UpdateConfigScreen
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

        with Vertical(classes="vertical"):
            with Horizontal(classes="horizontal"):
                yield Container(
                    Label(
                        f"Car ID: {self.app.car_id} | Owner ID: {self.app.owner_id}",
                        id="car-info",
                    ),
                    Button("<", id="back-to-home"),
                    id="controls",
                )

            with Vertical(classes="vertical"):
                yield Static("Edit Car Configuration:", id="config-title")
                self.config_input = Input(
                    placeholder="Enter new configuration JSON", id="update-config"
                )
                yield Container(self.config_input)
                yield Button("Update Car Configuration", id="send-update-config")

        yield Static("Output:", id="output")
        yield Footer()

    def on_mount(self) -> None:
        """Fetch the current configuration when the screen is mounted."""
        app = self.app  # Get reference to the main app instance
        try:
            # Fetch current configuration from Flask API
            response = requests.get(f"{app.flask_url}/get-config")
            if response.status_code == 503:
                requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                response = requests.get(f"{app.flask_url}/get-config")
            if response.status_code == 200:
                car_unprotected_doc = cryptolib.unprotect_lib(
                    response.json(), f"{app.key_store}/car.key", ["configuration"]
                )
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
        app = self.app

        try:
            if button_id == "send-update-config":
                # Get the value from the input field
                new_config_str = self.query_one("#update-config", Input).value
                new_config = json.loads(new_config_str) if new_config_str else None

                if new_config:
                    car_doc_unprotected = {
                        "carID": app.car_id,
                        "user": app.owner_id,
                        "configuration": new_config,
                    }
                    # TODO: change these hardcoded values
                    car_doc_protected = cryptolib.protect_lib(
                        car_doc_unprotected,
                        f"{app.key_store}/car.key",
                        ["configuration"],
                    )

                    response = requests.post(
                        f"{app.flask_url}/update-config",
                        json=car_doc_protected,
                    )
                    if response.status_code == 503:
                        requests.post(f"{app.flask_url}/set-car-key", json={"key": app.encrypted_car_key})
                        response = requests.post(
                            f"{app.flask_url}/update-config",
                            json=car_doc_protected,
                        )
                    self.display_output(response.text)
                else:
                    self.display_output("Please enter a valid configuration JSON.")
            elif button_id == "back-to-home":
                self.app.push_screen("home")
        except Exception as e:
            self.display_output(f"Error3: {e}")

    def display_output(self, message: str) -> None:
        """Display output to the user on the config page."""
        self.query_one("#output", Static).update(message)


class CarApp(App):
    SCREENS = {"home": HomeScreen, "config": UpdateConfigScreen}
    BINDINGS = [
        ("h", "push_screen('home')", "Home Screen"),
        ("c", "push_screen('config')", "Config Screen"),
    ]

    CSS_PATH = "styles.css"

    def __init__(self, car_id, owner_id, flask_url):
        super().__init__()
        self.car_id = car_id
        self.owner_id = owner_id
        self.flask_url = flask_url
        self.key_store = f"{KEY_STORE}/{USER}"
        
        # encrypt the car.key with the car public key
        self.encrypted_car_key = PKI.encrypt(
            f"{self.key_store}/car.key", f"{self.key_store}/../car1-web/entity.crt"
        )
        

    def on_mount(self) -> None:
        # self.install_screen(HomeScreen(), name="home")
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

if __name__ == "__main__":
    import sys

    # Parse command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 app.py <car_id> <owner_id>")
        sys.exit(1)

    car_id = sys.argv[1]
    owner_id = sys.argv[2]

    # Assume Flask app is running locally
    flask_url = f"http://127.0.0.1:{5000 + int(car_id)}"

    # Run the app
    CarApp(car_id, owner_id, flask_url).run()
