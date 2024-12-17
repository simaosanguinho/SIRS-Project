from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, Label
from textual.containers import Vertical, Horizontal
import requests


class CarUI(App):
    TITLE = "Car Management UI"
    CSS_PATH = "styles.tcss"  # Optional for styling

    def __init__(self, car_id, owner_id, flask_url):
        super().__init__()
        self.car_id = car_id
        self.owner_id = owner_id
        self.flask_url = flask_url

    def compose(self) -> ComposeResult:
        # Header and footer
        yield Header()
        yield Footer()

        # Display current car status
        yield Static("Car Management System", id="title")
        yield Label(f"Car ID: {self.car_id} | Owner ID: {self.owner_id}", id="car-info")

        # Maintenance Mode Controls
        yield Static("Maintenance Mode:")
        with Horizontal():
            yield Button("Enable", id="maintenance-on")
            yield Button("Disable", id="maintenance-off")

        # Configuration
        yield Static("Configuration:")
        with Vertical():
            yield Button("Get Config", id="get-config")
            yield Input(placeholder="Enter new configuration JSON", id="update-config")
            yield Button("Update Config", id="send-update-config")

        # Battery Controls
        yield Static("Battery Management:")
        with Horizontal():
            yield Button("Check Battery", id="check-battery")
            yield Button("Charge Battery", id="charge-battery")

        # Output Display
        yield Static("Output:", id="output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button events and send appropriate requests."""
        button_id = event.button.id

        try:
            if button_id == "maintenance-on":
                response = requests.get(f"{self.flask_url}/maintenance-mode/on")
                self.display_output(response.text)

            elif button_id == "maintenance-off":
                response = requests.get(f"{self.flask_url}/maintenance-mode/off")
                self.display_output(response.text)

            elif button_id == "get-config":
                response = requests.get(f"{self.flask_url}/get-config")
                string_response = response.text
                self.display_output(string_response)

            elif button_id == "check-battery":
                response = requests.get(f"{self.flask_url}/check-battery")
                self.display_output(response.text)

            elif button_id == "charge-battery":
                response = requests.get(f"{self.flask_url}/charge-battery")
                self.display_output(response.text)

            elif button_id == "send-update-config":
                new_config = self.query_one("#update-config", Input).value
                if new_config:
                    response = requests.post(
                        f"{self.flask_url}/update-config",
                        json=new_config,  # Ensure correct format
                    )
                    self.display_output(response.text)
                else:
                    self.display_output("Please enter a valid configuration JSON.")

        except Exception as e:
            self.display_output(f"Error: {e}")

    def display_output(self, message: str) -> None:
        """Display output to the user."""
        self.query_one("#output", Static).update(message)


if __name__ == "__main__":
    import sys

    # Parse command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python textual_car_app.py <car_id> <owner_id>")
        sys.exit(1)

    car_id = sys.argv[1]
    owner_id = sys.argv[2]

    # Assume Flask app is running locally
    flask_url = f"http://127.0.0.1:{5000 + int(car_id)}"

    app = CarUI(car_id, owner_id, flask_url)
    app.run()
