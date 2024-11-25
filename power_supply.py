class PowerSupplyError(Exception):
    """Custom exception for power supply errors."""

    pass


class PowerSupply:
    def __init__(self):
        # Initialize the power supply
        self.outputs = {
            1: False,
            2: False,
            3: False,
            4: False,
        }  # Example state tracking
        self.connection = False

    def connect(self, serial_port, baudrate, instrument_id):
        """
        Connect to the power supply.

        Parameters:
        serial_port (str): The serial port to use (e.g., 'COM3', '/dev/ttyUSB0')
        baudrate (int): The baud rate for the serial communication
        instrument_id (str): The instrument ID to identify the power supply

        Raises:
        PowerSupplyError: If connection fails.
        """
        if not serial_port or not baudrate or not instrument_id:
            raise PowerSupplyError("Failed to connect to power supply.")
        self.connection = True
        print(
            f"Connected to power supply on {serial_port} with baudrate {baudrate} and instrument ID {instrument_id}"
        )

    def disconnect(self):
        """
        Disconnect from the power supply.

        Raises:
        PowerSupplyError: If disconnection fails.
        """
        if not self.connection:
            raise PowerSupplyError("Failed to disconnect from power supply.")
        self.connection = False
        print("Disconnected from power supply")

    def set_voltage(self, output, voltage):
        """
        Set the voltage for a specific output.

        Parameters:
        output (int): The output number (e.g., 1, 2, 3, 4)
        voltage (float): The voltage to set

        Raises:
        PowerSupplyError: If the output is not turned on or communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if not self.outputs.get(output, False):
            raise PowerSupplyError(f"Output {output} is not turned on.")
        if voltage < 0:
            raise PowerSupplyError("Failed to communicate with power supply.")
        print(f"Setting voltage of output {output} to {voltage}V")

    def set_current(self, output, current):
        """
        Set the current for a specific output.

        Parameters:
        output (int): The output number (e.g., 1, 2, 3, 4)
        current (float): The current to set

        Raises:
        PowerSupplyError: If the output is not turned on or communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if not self.outputs.get(output, False):
            raise PowerSupplyError(f"Output {output} is not turned on.")
        if current < 0:
            raise PowerSupplyError("Failed to communicate with power supply.")
        print(f"Setting current of output {output} to {current}A")

    def turn_on(self, output):
        """
        Turn on a specific output.

        Parameters:
        output (int): The output number (e.g., 1, 2, 3, 4)

        Raises:
        PowerSupplyError: If communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if output not in self.outputs:
            raise PowerSupplyError("Failed to communicate with power supply.")
        self.outputs[output] = True
        print(f"Turning on output {output}")

    def turn_off(self, output):
        """
        Turn off a specific output.

        Parameters:
        output (int): The output number (e.g., 1, 2, 3, 4)

        Raises:
        PowerSupplyError: If communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if output not in self.outputs:
            raise PowerSupplyError("Failed to communicate with power supply.")
        self.outputs[output] = False
        print(f"Turning off output {output}")
