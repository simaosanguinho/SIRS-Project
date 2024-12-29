from textual.app import App, ComposeResult
from textual.widgets import Footer, Button, Static, Label, Input
from textual.containers import Vertical, Container
from textual.screen import Screen
from textual.theme import Theme

import requests
import cryptolib

# from textual.widgets import Input


class HomeScreen(Screen):
    """Home screen that displays basic mechanic actions."""

    def compose(self) -> ComposeResult:
        yield Static("Car Management System", id="title")
        yield Label(f"Mechanic ID: {self.app.mechanic_id}", id="mechanic-info")

        # add two buttons to enable and disable maintenance mode
        with Vertical(classes="vertical"):
            yield Container(
                Static("Update Firmware", classes="section-label"),
                Input(placeholder="Insert Car ID", id="car-id"),
                Button("Update Car Firmware", id="update-firmware"),
                classes="controls",
            )
            yield Container(
                Static("Testing:", classes="section-label"),
                Button("Perform Tests", id="tests"),
                classes="controls",
            )

        # Navigation to Config View
        # Output Display
        yield Static("Output:", id="output")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button events and send appropriate requests."""
        button_id = event.button.id
        # app = self.app  # Get reference to the main app instance

        try:
            if button_id == "tests":
                # TODO: Implement tests
                self.display_output("Running tests ")

            elif button_id == "update-firmware":
                car_id = self.query_one("#car-id", Input).value

                if not car_id:
                    self.display_output("Please enter a car ID")
                    return

                response = update_firmware(car_id)
                self.display_output(response)

        except Exception as e:
            self.display_output(f"Error1: {e}")

    def display_output(self, message: str) -> None:
        """Display output to the user."""
        self.query_one("#output", Static).update(message)


""" @app.route("/")
def root():
    return "<h3>Welcome to the Mechanic App!  </h3> Mechanic Id: " + str(self.mechanic_id)


## ENDPOINTS

# See the usre configuration - to show that even when he has the key he cannot see the user config

# Change config of the car - to show that the mechanic can change
# the config of the car (only when in maintenance mode)


@app.route("/update-firmware")
def update_firmware():
    # fetch the firmware from manufacturer and send it to the car
    response = requests.get(f"{manufacturer_url}/get-firmware/{1}")
    if response.status_code != 200:
        return "Failed to fetch firmware"
    print(response.json())

    firmware = response.json()["firmware"]
    signature = response.json()["signature"]
    # DOES THE MECHANIC NEED TO CHECK THE SIGNATURE?
    if not cryptolib.verify_signature(
        "../../test/keys/user1.pubkey", firmware, signature
    ):
        return "Invalid signature"

    # send the firmware to the car
    response = requests.post(f"{car_url}/update-firmware", json=response.json())
    print(response.text)

    return response.text
 """


def update_firmware(car_id):
    # fetch the firmware from manufacturer and send it to the car
    response = requests.get(f"{manufacturer_url}/get-firmware/{1}")
    if response.status_code != 200:
        return "Failed to fetch firmware"
    print(response.json())

    firmware = response.json()["firmware"]
    signature = response.json()["signature"]
    # DOES THE MECHANIC NEED TO CHECK THE SIGNATURE?
    if not cryptolib.verify_signature(
        "../../test/keys/user1.pubkey", firmware, signature
    ):
        return "Invalid signature"

    # send the firmware to the car
    car_url = f"http://127.0.0.1:{5000 + int(car_id)}"
    try:
        response = requests.post(f"{car_url}/update-firmware", json=response.json())
    except Exception:
        return f"Failed to establish connection with car {car_id}"
    print(response.text)
    if response.status_code != 200:
        return "Failed to update firmware"

    return response.text


class MechanicApp(App):
    SCREENS = {"home": HomeScreen}
    BINDINGS = [("h", "push_screen('home')", "Home Screen")]

    CSS_PATH = "styles.css"

    def __init__(self, mechanic_id, manufacturer_url):
        super().__init__()
        self.mechanic_id = mechanic_id
        self.manufacturer_url = manufacturer_url

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


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 app.py <mechanic_id>")
        sys.exit(1)

    mechanic_id = sys.argv[1]
    # set different port for mechanic
    # car_url = f"http://127.0.0.1:{5000 + int(1)}"
    manufacturer_url = f"http://127.0.0.1:{5200 + int(1)}"
    MechanicApp(mechanic_id, manufacturer_url).run()
