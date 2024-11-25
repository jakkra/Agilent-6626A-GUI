import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QComboBox,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QLCDNumber
import qdarkstyle
import json
import os
from power_supply import PowerSupply, PowerSupplyError  # Import the PowerSupply class

CONFIG_FILE = "./config.json"


class LogTerminal(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("background-color: black; color: white;")

    def log_error(self, message):
        """Log an error message in the terminal."""
        self.append(f'<span style="color: red;">ERROR: {message}</span>')

    def log_warning(self, message):
        """Log a warning message in the terminal."""
        self.append(f'<span style="color: yellow;">WARNING: {message}</span>')

    def log_debug(self, message):
        """Log a debug message in the terminal."""
        self.append(f'<span style="color: green;">DEBUG: {message}</span>')


class PowerSupplyGUI(QMainWindow):
    def __init__(self, config):
        super().__init__()

        self.setWindowTitle("HP 6626A")
        self.setGeometry(
            100, 100, 1000, 600
        )  # Adjusted width to accommodate config panel

        # Create an instance of PowerSupply
        self.power_supply = PowerSupply()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout()

        # Create and add config panel
        config_panel = self.create_config_panel()
        main_layout.addWidget(config_panel)

        # Create and add main control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # Set the main layout
        central_widget.setLayout(main_layout)

        if config:
            self.serial_port_input.setText(config.get("serial_port", ""))
            self.baud_rate_input.setCurrentText(config.get("baud_rate", "9600"))
            self.instrument_id_input.setText(config.get("instrument_id", ""))
            for i, output in enumerate(self.outputs, start=1):
                output_config = config.get(f"output_{i}", {})
                output["voltage_out"].display(
                    f"{output_config.get('voltage', '0.000'):.3f}"
                )
                output["current_out"].display(
                    f"{output_config.get('current', '0.000'):.3f}"
                )
                # if output_config.get("on", False):
                # output["on_off_button"].setChecked(True)

    def create_config_panel(self):
        """Create the configuration panel."""
        config_layout = QVBoxLayout()
        config_layout.setAlignment(Qt.AlignTop)  # Align elements to the top

        # Serial port input
        serial_port_label = QLabel("Serial Port:")
        self.serial_port_input = QLineEdit()
        self.serial_port_input.setPlaceholderText("Enter serial port")
        config_layout.addWidget(serial_port_label)
        config_layout.addWidget(self.serial_port_input)

        # Baud rate input
        baud_rate_label = QLabel("Baud Rate:")
        self.baud_rate_input = QComboBox()
        self.baud_rate_input.addItems(["9600", "19200", "38400", "57600", "115200"])
        config_layout.addWidget(baud_rate_label)
        config_layout.addWidget(self.baud_rate_input)

        # Instrument ID input
        instrument_id_label = QLabel("Instrument ID:")
        self.instrument_id_input = QLineEdit()
        self.instrument_id_input.setPlaceholderText("Enter instrument ID")
        config_layout.addWidget(instrument_id_label)
        config_layout.addWidget(self.instrument_id_input)

        # Open/Close connection button
        self.connection_button = QPushButton("Open Connection")
        self.connection_button.setCheckable(True)
        self.connection_button.toggled.connect(self.on_connection_toggled)
        config_layout.addWidget(self.connection_button)

        # Add terminal for log messages
        self.terminal = LogTerminal()
        config_layout.addWidget(self.terminal)

        # Wrap the config layout in a QWidget
        config_container = QWidget()
        config_container.setLayout(config_layout)
        config_container.setFixedWidth(200)  # Set fixed width for config panel

        return config_container

    def create_control_panel(self):
        """Create the main control panel."""
        control_layout = QVBoxLayout()

        # Add title
        title_label = QLabel("HP 6626A Power Supply Control")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        control_layout.addWidget(title_label)

        # Grid layout for outputs
        self.output_grid = QGridLayout()  # Create the grid layout
        self.output_grid.setHorizontalSpacing(20)  # Set horizontal spacing
        self.output_grid.setVerticalSpacing(20)  # Set vertical spacing
        self.outputs = []  # List to store references to each output section

        output_sections = [
            self.create_output_section("Output 1", "#00FF00"),  # Green
            self.create_output_section("Output 2", "#0000FF"),  # Blue
            self.create_output_section("Output 3", "#FFFF00"),  # Yellow
            self.create_output_section("Output 4", "#800080"),  # Purple
        ]

        for i, output_section in enumerate(output_sections, start=1):
            self.outputs.append(output_section)
            # Add to the grid: 2 rows x 2 columns layout
            row, col = divmod(i - 1, 2)
            self.output_grid.addWidget(output_section["container"], row, col)

        # Wrap the grid layout in a QWidget and add to the control layout
        grid_container = QWidget()
        grid_container.setLayout(self.output_grid)
        control_layout.addWidget(grid_container)

        # Shared input panel for voltage and current
        self.input_panel = self.create_input_panel()
        control_layout.addLayout(self.input_panel)

        # Wrap the control layout in a QWidget
        control_container = QWidget()
        control_container.setLayout(control_layout)

        return control_container

    def keyPressEvent(self, event):
        """Override keyPressEvent to handle Enter key press."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.on_set_clicked()

    def create_output_section(self, title, color):
        """Create a section for one power supply output."""
        layout = QVBoxLayout()

        # Section title
        section_title = QLabel(title)
        section_title.setAlignment(Qt.AlignCenter)
        section_title.setFixedHeight(50)
        section_title.setStyleSheet(
            f"""
            font-size: 18px;
            font-weight: bold;
            color: black;
            padding: 10px;
            background-color: {color};
            border-radius: 5px;
            margin: 2px;
        """
        )
        layout.addWidget(section_title)

        # Display current voltage and current
        voltage_out = QLCDNumber()
        voltage_out.setDigitCount(7)  # Adjust digit count to accommodate 3 decimals
        voltage_out.setSegmentStyle(QLCDNumber.Flat)
        voltage_out.display("0.000")
        voltage_out.setFixedSize(225, 75)  # Set fixed size for larger display

        current_out = QLCDNumber()
        current_out.setDigitCount(7)  # Adjust digit count to accommodate 3 decimals
        current_out.setSegmentStyle(QLCDNumber.Flat)
        current_out.display("0.000")
        current_out.setFixedSize(225, 75)  # Set fixed size for larger display

        # Layout for output values
        layout.addWidget(QLabel("Voltage Out (V):"))
        layout.addWidget(voltage_out)
        layout.addWidget(QLabel("Current Max Out (A):"))
        layout.addWidget(current_out)

        # ON/OFF toggle button
        on_off_button = QPushButton("OFF")
        on_off_button.setCheckable(True)
        on_off_button.setFixedHeight(40)
        on_off_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        on_off_button.toggled.connect(
            lambda checked, voltage_out=voltage_out, current_out=current_out: self.on_on_off_toggled(
                checked, voltage_out, current_out
            )
        )
        layout.addWidget(on_off_button)

        # Container widget for the section
        container = QWidget()
        container.setObjectName("outerContainer")
        container.setLayout(layout)
        container.mousePressEvent = lambda event: self.on_output_selected(container)
        # Add border around container
        container.setStyleSheet(
            "QWidget#outerContainer { border: 4px solid #545454; border-radius: 10px; }"
        )

        # Return references to widgets and layout
        return {
            "layout": layout,
            "container": container,
            "voltage_out": voltage_out,
            "current_out": current_out,
            "on_off_button": on_off_button,
            "title": title,
        }

    def create_input_panel(self):
        """Create a shared input panel for setting voltage and current."""
        layout = QVBoxLayout()

        # Load the seven-segment font
        font_id = QFontDatabase.addApplicationFont("digital-7.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            segment_font = QFont(font_family, 12)
        else:
            segment_font = QFont("Courier", 12)  # Fallback font

        # Title
        input_title = QLabel("Input Panel (Select an Output to Edit)")
        input_title.setAlignment(Qt.AlignCenter)
        input_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(input_title)

        # Voltage set
        h_layout1 = QHBoxLayout()
        voltage_label = QLabel("Voltage Set (V):")
        voltage_label.setStyleSheet("font-size: 16px;")  # Increase font size
        h_layout1.addWidget(voltage_label)
        self.voltage_input = QLineEdit()
        self.voltage_input.setPlaceholderText("Enter voltage")
        self.voltage_input.setFont(segment_font)
        self.voltage_input.setText(f"{0:.3f}")
        self.voltage_input.setStyleSheet(
            "border: 1px solid black; border-radius: 1px; margin: 0px; font-size: 24px;"
        )
        h_layout1.addWidget(self.voltage_input)

        # Fixed voltage buttons
        fixed_voltages = [1.8, 3.3, 5.0]
        for voltage in fixed_voltages:
            button = QPushButton(f"{voltage}V")
            button.setFixedSize(100, 30)  # Set button size
            button.setStyleSheet("font-size: 16px;")  # Increase font size
            button.clicked.connect(lambda _, v=voltage: self.set_fixed_voltage(v))
            h_layout1.addWidget(button)

        # Increment and Decrement buttons for voltage
        voltage_inc_button = QPushButton("+")
        voltage_inc_button.setFixedSize(50, 30)  # Set button size
        voltage_inc_button.setStyleSheet("font-size: 16px;")  # Increase font size
        voltage_inc_button.clicked.connect(
            lambda: self.increment_value(self.voltage_input, 0.1)
        )
        h_layout1.addWidget(voltage_inc_button)

        voltage_dec_button = QPushButton("-")
        voltage_dec_button.setFixedSize(50, 30)  # Set button size
        voltage_dec_button.setStyleSheet("font-size: 16px;")  # Increase font size
        voltage_dec_button.clicked.connect(
            lambda: self.increment_value(self.voltage_input, -0.1)
        )
        h_layout1.addWidget(voltage_dec_button)

        layout.addLayout(h_layout1)

        # Current set
        h_layout2 = QHBoxLayout()
        current_label = QLabel("Current Set (A):")
        current_label.setStyleSheet("font-size: 16px;")  # Increase font size
        h_layout2.addWidget(current_label)
        self.current_input = QLineEdit()
        self.current_input.setPlaceholderText("Enter current")
        self.current_input.setFont(segment_font)
        self.current_input.setText(f"{0:.3f}")
        self.current_input.setStyleSheet(
            "border: 1px solid black; border-radius: 1px; margin: 0px; font-size: 24px;"
        )
        h_layout2.addWidget(self.current_input)

        # Fixed current buttons
        fixed_currents = [0.1, 0.5, 1.0]
        for current in fixed_currents:
            button = QPushButton(f"{current}A")
            button.setFixedSize(100, 30)  # Set button size
            button.setStyleSheet("font-size: 16px;")  # Increase font size
            button.clicked.connect(lambda _, c=current: self.set_fixed_current(c))
            h_layout2.addWidget(button)

        # Increment and Decrement buttons for current
        current_inc_button = QPushButton("+")
        current_inc_button.setFixedSize(50, 30)  # Set button size
        current_inc_button.setStyleSheet("font-size: 16px;")  # Increase font size
        current_inc_button.clicked.connect(
            lambda: self.increment_value(self.current_input, 0.1)
        )
        h_layout2.addWidget(current_inc_button)

        current_dec_button = QPushButton("-")
        current_dec_button.setFixedSize(50, 30)  # Set button size
        current_dec_button.setStyleSheet("font-size: 16px;")  # Increase font size
        current_dec_button.clicked.connect(
            lambda: self.increment_value(self.current_input, -0.1)
        )
        h_layout2.addWidget(current_dec_button)

        layout.addLayout(h_layout2)

        # Set button
        self.set_button = QPushButton("Set")
        self.set_button.setStyleSheet(
            "font-size: 26px; padding: 5px;"
        )  # Increase font size to 30px
        self.set_button.setFixedSize(200, 50)  # Set button size to 200x70
        self.set_button.clicked.connect(self.on_set_clicked)
        self.set_button.setEnabled(False)  # Disable the set button initially

        # Center the set button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.set_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        return layout

    def set_fixed_voltage(self, voltage):
        """Set the voltage input to a fixed value."""
        self.voltage_input.setText(f"{voltage:.3f}")

    def set_fixed_current(self, current):
        """Set the current input to a fixed value."""
        self.current_input.setText(f"{current:.3f}")

    def increment_value(self, line_edit, step):
        """Increment the value in the QLineEdit by the given step."""
        try:
            value = float(line_edit.text())
        except ValueError:
            value = 0.0
        value += step
        line_edit.setText(f"{value:.3f}")

    def on_output_selected(self, output_container):
        """Handle selection of an output section."""
        # Reset the border of previously selected output (if any)
        if hasattr(self, "selected_output") and self.selected_output:
            self.selected_output["container"].setStyleSheet(
                "QWidget#outerContainer { border: 4px solid #545454; border-radius: 10px; }"
            )  # Remove previous highlight

        # Find and set the newly selected output
        for output in self.outputs:
            if output["container"] == output_container:
                self.selected_output = output
                # Apply border highlighting only to the outer container
                output["container"].setStyleSheet(
                    "QWidget#outerContainer { border: 5px solid #8ab6f7; border-radius: 10px; }"
                )
                break

        # Populate input fields with current values
        voltage_out = self.selected_output["voltage_out"].value()
        current_out = self.selected_output["current_out"].value()
        self.voltage_input.setText(f"{voltage_out:.3f}")
        self.current_input.setText(f"{current_out:.3f}")

    def on_set_clicked(self):
        """Apply the voltage and current to the selected output."""
        if not hasattr(self, "selected_output") or not self.selected_output:
            print("No output selected!")
            return

        voltage = self.voltage_input.text()
        current = self.current_input.text()

        # Update selected output's displayed values
        try:
            voltage_value = float(voltage)
            current_value = float(current)
            self.selected_output["voltage_out"].display(f"{voltage_value:.3f}")
            self.selected_output["current_out"].display(f"{current_value:.3f}")

            # Call the power supply methods
            output_index = self.outputs.index(self.selected_output) + 1
            self.power_supply.set_voltage(output_index, voltage_value)
            self.power_supply.set_current(output_index, current_value)
        except ValueError:
            print("Invalid input for voltage or current!")

    def on_on_off_toggled(self, checked, voltage_out, current_out):
        """Handle ON/OFF toggle for an output."""
        sender = self.sender()
        # Find the output container that contains the sender button
        for output in self.outputs:
            if output["on_off_button"] == sender:
                output_index = self.outputs.index(output) + 1
                break
        else:
            print("Output not found!")
            return

        if checked:
            print("Output turned ON.")
            try:
                self.power_supply.turn_on(output_index)
                sender.setText("ON")
                sender.setStyleSheet(
                    "background-color: green; font-size: 18px; font-weight: bold;"
                )
                # Change the color of the voltage_out digits to green
                voltage_out.setStyleSheet("color: green;")
                current_out.setStyleSheet("color: green;")
            except PowerSupplyError as e:
                # Log to the terminal
                self.terminal.log_error(str(e))
                sender.setChecked(False)
        else:
            print("Output turned OFF.")
            sender.setText("OFF")
            sender.setStyleSheet("font-size: 18px; font-weight: bold;")
            # Reset the color of the voltage_out digits
            voltage_out.setStyleSheet("")
            current_out.setStyleSheet("")
            self.power_supply.turn_off(output_index)

    def on_connection_toggled(self, checked):
        """Handle the toggling of the connection button."""
        if checked:
            serial_port = self.serial_port_input.text()
            baud_rate = self.baud_rate_input.currentText()
            instrument_id = self.instrument_id_input.text()
            # Implement the logic to open the connection
            print(
                f"Opening connection to {serial_port} at {baud_rate} baud with instrument ID {instrument_id}"
            )
            try:
                self.power_supply.connect(serial_port, int(baud_rate), instrument_id)
                self.set_button.setEnabled(True)  # Enable the set button when connected
                self.connection_button.setText("Close Connection")
                self.terminal.log_debug(
                    f"Connected to {serial_port} at {baud_rate} baud with instrument ID {instrument_id}"
                )
            except PowerSupplyError as e:
                # Log to the terminal
                self.terminal.log_error(str(e))
                self.connection_button.setChecked(False)
        else:
            # Implement the logic to close the connection
            print("Closing connection")
            self.connection_button.setText("Open Connection")
            self.set_button.setEnabled(
                False
            )  # Disable the set button when disconnected
            self.terminal.log_debug("Disconnected from power supply")


def load_config():
    """Load configuration from a file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}


def save_config(config):
    """Save configuration to a file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


def save_current_settings(window):
    print("Saving current settings...")
    """Save current settings from the GUI."""
    config = {
        "serial_port": window.serial_port_input.text(),
        "baud_rate": window.baud_rate_input.currentText(),
        "instrument_id": window.instrument_id_input.text(),
    }
    for i, output in enumerate(window.outputs, start=1):
        config[f"output_{i}"] = {
            "voltage": output["voltage_out"].value(),
            "current": output["current_out"].value(),
            "on": output["on_off_button"].isChecked(),
        }
    print(config)
    save_config(config)


if __name__ == "__main__":
    # Set attributes before creating the QApplication instance
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    # setup stylesheet
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    # or in new API
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyqt5"))

    config = load_config()
    window = PowerSupplyGUI(config)
    window.show()

    # Save current settings when the application is about to quit
    app.aboutToQuit.connect(lambda: save_current_settings(window))

    sys.exit(app.exec_())
