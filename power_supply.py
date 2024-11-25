import pyvisa


class PowerSupplyError(Exception):
    """Custom exception for power supply errors."""

    pass


class PowerSupply:
    def __init__(self):
        # Initialize the power supply
        self.channels = {
            1: False,
            2: False,
            3: False,
            4: False,
        }  # Example state tracking
        self.connection = False
        self.rm = pyvisa.ResourceManager()
        print(self.rm.list_resources())

    def _send_command(self, command):
        """
        Prepends the module prefix to all commands and sends them.
        :param command: The SCPI command to send (without the module prefix).
        """
        full_command = f"OUTPUT {self.module_id}; {command}"
        self.instrument.write(full_command)

    def _query_command(self, command):
        """
        Prepends the module prefix to a query command and sends it.
        :param command: The SCPI query to send (without the module prefix).
        :return: The response from the instrument.
        """
        full_command = f"OUTPUT {self.module_id}; {command}"
        return self.instrument.query(full_command)

    def list_resources(self):
        """
        List available resources.

        Returns:
        list: A list of available resources
        """
        return self.rm.list_resources()

    def connect(self, serial_port, baudrate, instrument_id, timeout=5000):
        """
        Connect to the power supply.

        Parameters:
        serial_port (str): The serial port to use (e.g., 'COM3', '/dev/ttyUSB0')
        baudrate (int): The baud rate for the serial communication
        instrument_id (str): The instrument ID to identify the power supply
        param timeout (int): Timeout for communication in milliseconds (default: 5000)

        Raises:
        PowerSupplyError: If connection fails.
        """
        if not serial_port or not baudrate or not instrument_id:
            raise PowerSupplyError("Invalid connection parameters.")

        self.instrument = self.rm.open_resource(serial_port)
        self.instrument.baud_rate = baudrate
        self.instrument.timeout = timeout
        self.module_id = instrument_id
        # TODO handle error
        print(f"Connected to: {self.instrument.query('*IDN?')}")
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
        self.instrument.close()
        self.connection = False
        print("Disconnected from power supply")

    def set_voltage(self, channel, voltage):
        """
        Set the voltage for a specific channel.

        Parameters:
        channel (int): The channel number (e.g., 1, 2, 3, 4)
        voltage (float): The voltage to set

        Raises:
        PowerSupplyError: If the channel is not turned on or communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if not self.channels.get(channel, False):
            raise PowerSupplyError(f"Channel {channel} is not turned on.")
        if voltage < 0:
            raise PowerSupplyError("Failed to communicate with power supply.")
        print(f"Setting voltage of channel {channel} to {voltage}V")
        self._send_command(f"VSET {channel},{voltage}")

    def set_current_limit(self, channel, current):
        """
        Set the current for a specific channel.

        Parameters:
        channel (int): The channel number (e.g., 1, 2, 3, 4)
        current (float): The current to set

        Raises:
        PowerSupplyError: If the channel is not turned on or communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if not self.channels.get(channel, False):
            raise PowerSupplyError(f"Channel {channel} is not turned on.")
        if current < 0:
            raise PowerSupplyError("Failed to communicate with power supply.")
        print(f"Setting current limit of channel {channel} to {current}A")
        self._send_command(f"ISET {channel},{current}")

    def set_voltage_range(self, channel, voltage_range):
        """
        Sets the voltage programming resolution range for the specified channel and voltage.
        The power supply will automatically pick the range that the value sent will fit into.
        :param channel: Output channel number
        :param voltage_range: Voltage
        """
        self._send_command(f"VRSET {channel},{voltage_range}")

    def set_current_range(self, channel, current_range):
        """
        Sets the current programming resolution range for the specified channel and current.
        The power supply will automatically pick the range that the value sent will fit into.
        :param channel: Output channel number
        :param current_range: Current Amperes
        """
        self._send_command(f"IRSET {channel},{current_range}")

    def enable_output(self, channel):
        """
        Turn on a specific channel.

        Parameters:
        channel (int): The channel number (e.g., 1, 2, 3, 4)

        Raises:
        PowerSupplyError: If communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if channel not in self.channels:
            raise PowerSupplyError("Failed to communicate with power supply.")
        self.channels[channel] = True
        print(f"Turning on channel {channel}")
        self._send_command(f"OUT {channel},ON")

    def disable_output(self, channel):
        """
        Turn off a specific channel.

        Parameters:
        channel (int): The channel number (e.g., 1, 2, 3, 4)

        Raises:
        PowerSupplyError: If communication fails.
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if channel not in self.channels:
            raise PowerSupplyError("Failed to communicate with power supply.")
        self.channels[channel] = False
        print(f"Turning off channel {channel}")
        self._send_command(f"OUT {channel},OFF")

    def set_overvoltage_protection(self, channel, voltage):
        """
        Configures the overvoltage protection trip point for the specified channel.
        :param channel: Output channel number
        :param voltage: OVP trip point in volts
        """
        self._send_command(f"OVSET {channel},{voltage}")

    def enable_overcurrent_protection(self, channel):
        """
        Enables the overcurrent protection for the specified channel.
        :param channel: Output channel number
        """
        self._send_command(f"OCP {channel},ON")

    def disable_overcurrent_protection(self, channel):
        """
        Disables the overcurrent protection for the specified channel.
        :param channel: Output channel number
        """
        self._send_command(f"OCP {channel},OFF")

    def get_output_voltage(self, channel):
        """
        Queries the output voltage of the specified channel.
        :param channel: Output channel number
        :return: Measured output voltage in volts
        """
        return float(self._query_command(f"VOUT? {channel}"))

    def get_output_current(self, channel):
        """
        Queries the output current of the specified channel.
        :param channel: Output channel number
        :return: Measured output current in amperes
        """
        return float(self._query_command(f"IOUT? {channel}"))

    def get_programmed_voltage(self, channel):
        """
        Queries the programmed voltage for the specified channel.
        :param channel: Output channel number
        :return: Programmed voltage in volts
        """
        return float(self._query_command(f"VSET? {channel}"))

    def get_programmed_current_limit(self, channel):
        """
        Queries the programmed current limit for the specified channel.
        :param channel: Output channel number
        :return: Programmed current limit in amperes
        """
        return float(self._query_command(f"ISET? {channel}"))

    def send_raw_command(self, command):
        """
        Send a command to the power supply and return the response.

        Parameters:
        command (str): The command to send

        Raises:
        PowerSupplyError: If communication fails.

        Returns:
        str: The response from the power supply
        """
        if not self.connection:
            raise PowerSupplyError("Power supply is not connected.")
        if not command:
            raise PowerSupplyError("Command is empty.")

        # Simulate sending command and receiving response
        print(f"Sending command: {command}")
        self.instrument.write(command)
        # response = "OK"  # Simulated response
        # print(f"Received response: {response}")
        return "TODO: Implement response"
