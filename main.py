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
    QSizePolicy,
    QDialog,
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QLCDNumber
import qdarkstyle
import json
import os
from PyQt5.QtCore import QThread, pyqtSignal
from power_supply import (
    PowerSupply,
    PowerSupplyError,
    PowerSupplyChannelNotEnabledError,
    PowerSupplyTimeoutError,
)
from plot_window import PlotWindow
import time

CONFIG_FILE = "./config.json"


class InputDialog(QDialog):
    def __init__(
        self, parent=None, channel=1, current_voltage=0.0, current_current=0.0
    ):
        super().__init__(parent)
        self.channel = channel
        self.voltage_value = current_voltage
        self.current_value = current_current
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle(f"Set Output {self.channel} Values")
        self.setModal(True)
        self.setFixedSize(600, 400)

        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Output {self.channel} Settings")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px;")
        layout.addWidget(title)

        # Load the seven-segment font
        font_id = QFontDatabase.addApplicationFont("digital-7.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            segment_font = QFont(font_family, 16)
        else:
            segment_font = QFont("Courier", 16)  # Fallback font

        # Voltage section
        voltage_group = QVBoxLayout()
        voltage_label = QLabel("Voltage (V):")
        voltage_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        voltage_group.addWidget(voltage_label)

        voltage_input_row = QHBoxLayout()
        self.voltage_input = QLineEdit()
        self.voltage_input.setText(f"{self.voltage_value:.3f}")
        self.voltage_input.setFont(segment_font)
        self.voltage_input.setStyleSheet(
            "border: 2px solid black; border-radius: 5px; padding: 8px; font-size: 20px; min-height: 40px;"
        )
        self.voltage_input.setFixedWidth(100)
        voltage_input_row.addWidget(self.voltage_input)

        # Voltage increment/decrement
        v_dec = QPushButton("-")
        v_dec.setStyleSheet(
            "font-size: 20px; font-weight: bold; min-height: 50px; min-width: 50px;"
        )
        v_dec.clicked.connect(lambda: self.adjust_voltage(-0.1))
        voltage_input_row.addWidget(v_dec)

        v_inc = QPushButton("+")
        v_inc.setStyleSheet(
            "font-size: 20px; font-weight: bold; min-height: 50px; min-width: 50px;"
        )
        v_inc.clicked.connect(lambda: self.adjust_voltage(0.1))
        voltage_input_row.addWidget(v_inc)

        # Add some preset buttons in the same row
        for voltage in [1.8, 3.0, 3.3]:
            btn = QPushButton(f"{voltage}V")
            btn.setStyleSheet("font-size: 14px; min-height: 50px; min-width: 60px;")
            btn.clicked.connect(lambda _, v=voltage: self.set_voltage(v))
            voltage_input_row.addWidget(btn)

        voltage_group.addLayout(voltage_input_row)

        # Second row with more voltage presets to fill the row
        voltage_controls2 = QHBoxLayout()
        for voltage in [4.2, 5.0, 12.0, 18.0, 20.0]:
            btn = QPushButton(f"{voltage}V")
            btn.setStyleSheet("font-size: 14px; min-height: 45px; min-width: 60px;")
            btn.clicked.connect(lambda _, v=voltage: self.set_voltage(v))
            voltage_controls2.addWidget(btn)
        voltage_group.addLayout(voltage_controls2)
        layout.addLayout(voltage_group)

        # Current section
        current_group = QVBoxLayout()
        current_label = QLabel("Current (A):")
        current_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        current_group.addWidget(current_label)

        current_controls = QHBoxLayout()
        self.current_input = QLineEdit()
        self.current_input.setText(f"{self.current_value:.3f}")
        self.current_input.setFont(segment_font)
        self.current_input.setStyleSheet(
            "border: 2px solid black; border-radius: 5px; padding: 8px; font-size: 20px; min-height: 40px;"
        )
        self.current_input.setFixedWidth(100)
        current_controls.addWidget(self.current_input)

        # Current increment/decrement
        c_dec = QPushButton("-")
        c_dec.setStyleSheet(
            "font-size: 20px; font-weight: bold; min-height: 50px; min-width: 60px;"
        )
        c_dec.clicked.connect(lambda: self.adjust_current(-0.1))

        c_inc = QPushButton("+")
        c_inc.setStyleSheet(
            "font-size: 20px; font-weight: bold; min-height: 50px; min-width: 60px;"
        )
        c_inc.clicked.connect(lambda: self.adjust_current(0.1))

        current_controls.addWidget(c_dec)
        current_controls.addWidget(c_inc)

        # Current preset buttons
        for current in [0.1, 0.5, 1.0]:
            btn = QPushButton(f"{current}A")
            btn.setStyleSheet("font-size: 16px; min-height: 50px; min-width: 80px;")
            btn.clicked.connect(lambda _, c=current: self.set_current(c))
            current_controls.addWidget(btn)

        current_group.addLayout(current_controls)
        layout.addLayout(current_group)

        # Dialog buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "font-size: 18px; min-height: 50px; min-width: 120px; background-color: #f44336; color: white;"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet(
            "font-size: 18px; min-height: 50px; min-width: 120px; background-color: #4CAF50; color: white;"
        )
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def set_voltage(self, voltage):
        self.voltage_input.setText(f"{voltage:.3f}")

    def set_current(self, current):
        self.current_input.setText(f"{current:.3f}")

    def adjust_voltage(self, delta):
        try:
            current_val = float(self.voltage_input.text())
            new_val = max(0, current_val + delta)
            self.voltage_input.setText(f"{new_val:.3f}")
        except ValueError:
            pass

    def adjust_current(self, delta):
        try:
            current_val = float(self.current_input.text())
            new_val = max(0, current_val + delta)
            self.current_input.setText(f"{new_val:.3f}")
        except ValueError:
            pass

    def get_values(self):
        try:
            voltage = float(self.voltage_input.text())
            current = float(self.current_input.text())
            return voltage, current
        except ValueError:
            return None, None


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


class VoltageMonitorThread(QThread):
    realtime_data_updated = pyqtSignal(
        int, float, float
    )  # Signal to emit voltage and current updates

    def __init__(self, power_supply, interval=100):
        super().__init__()
        self.power_supply = power_supply
        self.interval = interval
        self.running = False

    def run(self):
        print("Voltage monitor thread started.")
        self.running = True
        while self.running:
            for channel in range(1, 5):
                try:
                    voltage = self.power_supply.get_output_voltage(channel)
                    current = self.power_supply.get_output_current(channel)
                    # print(f"Channel {channel} voltage: {voltage}V, current: {current}A")
                    self.realtime_data_updated.emit(channel, voltage, current)
                except PowerSupplyChannelNotEnabledError as e:
                    pass  # Ignore not enabled channels
                except PowerSupplyTimeoutError as e:
                    pass
                except PowerSupplyError as e:
                    pass

            self.msleep(self.interval)

    def stop(self):
        self.running = False


class PowerSupplyGUI(QMainWindow):
    def __init__(self, config):
        super().__init__()

        self.setWindowTitle("HP 6626A")
        self.setGeometry(
            100, 100, 1000, 600
        )  # Adjusted width to accommodate config panel

        # Create an instance of PowerSupply
        self.power_supply = PowerSupply(debug=False, mock=False)

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

        # Initialize voltage history
        self.voltage_history = {i: [] for i in range(1, 5)}
        self.current_history = {i: [] for i in range(1, 5)}
        self.plot_windows = {i: PlotWindow(i) for i in range(1, 5)}

        # Start the voltage monitor thread
        self.voltage_monitor_thread = VoltageMonitorThread(self.power_supply)
        self.voltage_monitor_thread.realtime_data_updated.connect(
            self.update_voltage_history
        )

        if config:
            saved_serial_port = config.get("serial_port", "")
            index = self.serial_port_input.findText(saved_serial_port)
            if index != -1:
                self.serial_port_input.setCurrentIndex(index)
            # self.serial_port_input.setText(config.get("serial_port", ""))
            self.baud_rate_input.setCurrentText(config.get("baud_rate", "9600"))
            self.instrument_id_input.setText(config.get("instrument_id", "705"))
            for i, output in enumerate(self.outputs, start=1):
                output_config = config.get(f"output_{i}", {})
                output["voltage_out"].display(
                    f"{output_config.get('voltage', '0.000'):.3f}"
                )
                output["current_out"].display(
                    f"{output_config.get('current', '0.000'):.3f}"
                )

    def update_voltage_history(self, channel, voltage, current):
        """Update the voltage history for a specific channel."""
        self.voltage_history[channel].append(voltage)
        self.current_history[channel].append(current)
        if len(self.voltage_history[channel]) > 100:  # Limit history to 100 entries
            self.voltage_history[channel].pop(0)
            self.current_history[channel].pop(0)

        # Since QT signal may not be handled when the signalling thread is stopped,
        # check if the channel is enabled, to avoid overwriting wrong values in UI.
        if not self.power_supply.is_channel_enabled(channel):
            return

        # Update voltage and current on all outputs
        self.outputs[channel - 1]["voltage_out"].display(f"{voltage:.3f}")
        self.outputs[channel - 1]["current_out"].display(f"{current:.3f}")

        self.plot_windows[channel].update_plot(
            self.current_history[channel], self.voltage_history[channel]
        )

    def closeEvent(self, event):
        """Handle the window close event to stop the thread."""
        self.voltage_monitor_thread.stop()
        self.voltage_monitor_thread.wait()
        print("Voltage monitor thread stopped.")

        # Close all plot windows
        for plot_window in self.plot_windows.values():
            plot_window.close()

        super().closeEvent(event)

    def create_config_panel(self):
        """Create the configuration panel."""
        config_layout = QVBoxLayout()
        config_layout.setAlignment(Qt.AlignTop)  # Align elements to the top

        def populate_serial_ports():
            """Populate the serial port dropdown with available ports."""
            self.serial_port_input.clear()
            ports = self.power_supply.list_resources()
            for port in ports:
                self.serial_port_input.addItem(port)

        # Serial port input
        serial_port_label = QLabel("Serial Port:")
        self.serial_port_input = QComboBox()
        self.serial_port_input.setStyleSheet("min-height: 35px;")
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("font-size: 14px; min-height: 35px;")
        self.refresh_button.clicked.connect(populate_serial_ports)
        config_layout.addWidget(serial_port_label)
        config_layout.addWidget(self.serial_port_input)
        config_layout.addWidget(self.refresh_button)
        populate_serial_ports()  # Populate the dropdown initially

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
        self.connection_button.setStyleSheet("font-size: 14px; min-height: 40px;")
        self.connection_button.toggled.connect(self.on_connection_toggled)
        config_layout.addWidget(self.connection_button)

        # Add terminal for log messages
        self.terminal = LogTerminal()
        config_layout.addWidget(self.terminal)

        # Add input field and send button below the terminal
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter command")
        self.input_field.setStyleSheet("min-height: 35px;")
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("font-size: 14px; min-height: 35px;")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.input_field.returnPressed.connect(self.send_button.click)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        config_layout.addLayout(input_layout)

        # Wrap the config layout in a QWidget
        config_container = QWidget()
        config_container.setLayout(config_layout)
        config_container.setMaximumWidth(
            350
        )  # Reduced width for better space usage on small screen

        return config_container

    def create_control_panel(self):
        """Create the main control panel."""
        control_layout = QVBoxLayout()

        # Add title
        self.title_label = QLabel("HP 6626A Power Supply Control")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        # Create a horizontal layout for the title and fullscreen button
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.title_label)

        # Add fullscreen toggle button
        self.fullscreen_button = QPushButton("Toggle Fullscreen")
        self.fullscreen_button.setStyleSheet("font-size: 14px; min-height: 40px;")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        title_layout.addWidget(self.fullscreen_button, alignment=Qt.AlignRight)

        control_layout.addLayout(title_layout)

        # Remove duplicate title layout code

        # Grid layout for outputs
        self.output_grid = QGridLayout()  # Create the grid layout
        self.output_grid.setHorizontalSpacing(20)  # Set horizontal spacing
        # self.output_grid.setVerticalSpacing(20)  # Set vertical spacing
        self.outputs = []  # List to store references to each output section

        output_sections = [
            self.create_output_section(1, "Output 1", "#00FF00"),  # Green
            self.create_output_section(2, "Output 2", "#0000FF"),  # Blue
            self.create_output_section(3, "Output 3", "#FFFF00"),  # Yellow
            self.create_output_section(4, "Output 4", "#800080"),  # Purple
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

        # Wrap the control layout in a QWidget
        control_container = QWidget()
        control_container.setLayout(control_layout)

        return control_container

    def toggle_fullscreen(self):
        """Toggle between fullscreen and normal window."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        """Override keyPressEvent to handle Enter key press."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not self.input_field.hasFocus():
                # Enter key now does nothing since we use modal dialogs
                pass

    def create_output_section(self, channel, title, color):
        """Create a section for one power supply output."""
        layout = QVBoxLayout()

        # Section title
        section_title = QLabel(title)
        section_title.setAlignment(Qt.AlignCenter)
        # section_title.setFixedHeight(50)
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
        horizontal_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Display current voltage and current
        voltage_out = QLCDNumber()
        voltage_out.setDigitCount(7)  # Adjust digit count to accommodate 3 decimals
        voltage_out.setSegmentStyle(QLCDNumber.Flat)
        voltage_out.display("0.000")
        voltage_out.setFixedSize(190, 65)  # Set fixed size for larger display

        current_out = QLCDNumber()
        current_out.setDigitCount(7)  # Adjust digit count to accommodate 3 decimals
        current_out.setSegmentStyle(QLCDNumber.Flat)
        current_out.display("0.000")
        current_out.setFixedSize(190, 65)  # Set fixed size for larger display

        plot_button = QPushButton(f"Open plot")
        plot_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        plot_button.setStyleSheet("font-size: 14px; min-height: 45px;")
        plot_button.clicked.connect(
            lambda checked, ch=channel: self.open_plot_window(ch)
        )

        settings_button = QPushButton("Settings")
        settings_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        settings_button.setStyleSheet(
            "font-size: 14px; min-height: 45px; background-color: #2196F3; color: white;"
        )
        settings_button.clicked.connect(
            lambda checked, ch=channel: self.open_settings_dialog(ch)
        )

        # Layout for output values
        left_layout.addWidget(QLabel("Voltage Out (V):"))
        left_layout.addWidget(voltage_out)
        left_layout.addWidget(QLabel("Current Max Out (A):"))
        left_layout.addWidget(current_out)
        right_layout.addWidget(settings_button)
        right_layout.addWidget(plot_button)

        # ON/OFF toggle button
        on_off_button = QPushButton("OFF")
        on_off_button.setCheckable(True)
        on_off_button.setStyleSheet(
            "font-size: 18px; font-weight: bold; min-height: 50px;"
        )
        on_off_button.setEnabled(False)  # Set to disabled by default
        on_off_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        on_off_button.toggled.connect(
            lambda checked, voltage_out=voltage_out, current_out=current_out: self.on_on_off_toggled(
                checked, voltage_out, current_out
            )
        )
        right_layout.addWidget(on_off_button)

        horizontal_layout.addLayout(left_layout)
        horizontal_layout.addLayout(right_layout)
        layout.addLayout(horizontal_layout)

        # Container widget for the section
        container = QWidget()
        container.setObjectName("outerContainer")
        container.setLayout(layout)
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
                self.power_supply.enable_output(output_index)
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
            self.power_supply.disable_output(output_index)

        if checked and not self.voltage_monitor_thread.isRunning():
            self.voltage_monitor_thread.start()
        elif self.power_supply.get_num_enabled_channels() == 0:
            self.voltage_monitor_thread.stop()
            self.voltage_monitor_thread.wait()
            print("Voltage monitor thread stopped.")

        if not checked:
            voltage_out.display(
                f"{self.power_supply.get_programmed_voltage(output_index):.3f}"
            )
            current_out.display(
                f"{self.power_supply.get_programmed_current_limit(output_index):.3f}"
            )

    def set_on_off_buttons_enabled(self, enabled):
        """Enable or disable all ON/OFF buttons."""
        for output in self.outputs:
            output["on_off_button"].setEnabled(enabled)

    def on_connection_toggled(self, checked):
        """Handle the toggling of the connection button."""
        if checked:
            serial_port = self.serial_port_input.currentText()
            baud_rate = self.baud_rate_input.currentText()
            instrument_id = self.instrument_id_input.text()
            # Implement the logic to open the connection
            print(
                f"Opening connection to {serial_port} at {baud_rate} baud with instrument ID {instrument_id}"
            )
            try:
                self.power_supply.connect(serial_port, int(baud_rate), instrument_id)

                self.connection_button.setText("Close Connection")
                self.terminal.log_debug(
                    f"Connected to {serial_port} at {baud_rate} baud with instrument ID {instrument_id}"
                )
                self.set_on_off_buttons_enabled(True)
                # make connect button grren
                self.connection_button.setStyleSheet("background-color: green;")

                if config:
                    for i, output in enumerate(self.outputs, start=1):
                        output_config = config.get(f"output_{i}", {})
                        self.power_supply.set_voltage(
                            i, output_config.get("voltage", 0)
                        )
                        self.power_supply.set_current_limit(
                            i, output_config.get("current", 0)
                        )

            except Exception as e:
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
            self.set_on_off_buttons_enabled(False)

    def on_send_clicked(self):
        """Handle the send button click event."""
        command = self.input_field.text()
        if command:
            try:
                self.terminal.log_debug(f"SEND: {command}")
                response = self.power_supply._query_command(command)
                self.terminal.log_debug(f"RECV: {response}")
            except PowerSupplyError as e:
                self.terminal.log_error(str(e))
            self.input_field.clear()

    def open_plot_window(self, channel):
        self.plot_windows[channel].show()

    def open_settings_dialog(self, channel):
        """Open the settings dialog for a specific channel."""
        # Get current values
        current_voltage = self.outputs[channel - 1]["voltage_out"].value()
        current_current = self.outputs[channel - 1]["current_out"].value()

        # Create and show dialog
        dialog = InputDialog(self, channel, current_voltage, current_current)
        if dialog.exec_() == QDialog.Accepted:
            voltage, current = dialog.get_values()
            if voltage is not None and current is not None:
                # Update the output values
                self.outputs[channel - 1]["voltage_out"].display(f"{voltage:.3f}")
                self.outputs[channel - 1]["current_out"].display(f"{current:.3f}")

                # Send to power supply if connected
                try:
                    self.power_supply.set_voltage(channel, voltage)
                    self.power_supply.set_current_limit(channel, current)
                except Exception as e:
                    self.terminal.log_error(f"Failed to set values: {str(e)}")


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
        "serial_port": window.serial_port_input.currentText(),
        "baud_rate": window.baud_rate_input.currentText(),
        "instrument_id": window.instrument_id_input.text(),
    }
    for i, output in enumerate(window.outputs, start=1):
        config[f"output_{i}"] = {
            "on": output["on_off_button"].isChecked(),
        }
    for i in range(1, 5):
        config[f"output_{i}"] = {
            "voltage": window.power_supply.get_programmed_voltage(i),
            "current": window.power_supply.get_programmed_current_limit(i),
        }
    print(config)
    save_config(config)


if __name__ == "__main__":
    # Set attributes before creating the QApplication instance
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    # setup stylesheet
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyqt5"))

    config = load_config()
    window = PowerSupplyGUI(config)
    window.show()
    window.showFullScreen()

    # Save current settings when the application is about to quit
    app.aboutToQuit.connect(lambda: save_current_settings(window))

    sys.exit(app.exec_())
