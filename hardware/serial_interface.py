"""Serial communication bridge between Python and Teensy."""


class SerialInterface:
    """Placeholder for autodetect, reconnect, commands, and telemetry parsing."""

    def connect(self) -> None:
        raise NotImplementedError
