"""
Central configuration for the autonomous KRAI robot.

This file is intentionally data-only: tune values here, keep robot logic in
FSM and hardware modules.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Serial / Teensy link
# ---------------------------------------------------------------------------

SERIAL_BAUDRATE = 115_200
SERIAL_TIMEOUT_S = 0.05
SERIAL_RECONNECT_INTERVAL_S = 1.0

# Jetson/Linux autodetect candidates. The serial layer should scan these
# prefixes and prefer ports whose USB description matches TEENSY_USB_HINTS.
SERIAL_PORT_PREFIXES = (
    "/dev/ttyACM",
    "/dev/ttyUSB",
    "/dev/serial/by-id/",
)

TEENSY_USB_HINTS = (
    "Teensy",
    "PJRC",
    "USB Serial",
)


# ---------------------------------------------------------------------------
# Motion tuning
# ---------------------------------------------------------------------------

ODOMETRY_REPORT_PERIOD_S = 0.1
CONTROL_LOOP_PERIOD_S = 0.02

# All distances are meters, angles are degrees.
POSITION_TOLERANCE_M = 0.02
STRAFE_TOLERANCE_M = 0.02
HEADING_TOLERANCE_DEG = 1.5

MOVE_IDLE_CONFIRM_COUNT = 3
MOVE_TIMEOUT_MARGIN_S = 1.5
MOVE_MIN_TIMEOUT_S = 2.0


@dataclass(frozen=True)
class SpeedLimit:
    max_fwd: float
    max_strf: float
    max_turn: float


DEFAULT_SPEED_LIMIT = SpeedLimit(
    max_fwd=0.65,
    max_strf=0.55,
    max_turn=120.0,
)

SLOW_SPEED_LIMIT = SpeedLimit(
    max_fwd=0.25,
    max_strf=0.20,
    max_turn=45.0,
)


# ---------------------------------------------------------------------------
# Servo geometry
# ---------------------------------------------------------------------------

SERVO_GRIPPER_PIN = 0
SERVO_ARM_PIN = 1

GRIPPER_OPEN_DEG = 75
GRIPPER_CLOSED_DEG = 12

ARM_UP_DEG = 35
ARM_PICKUP_DEG = 118
ARM_SCORE_DEG = 95

SERVO_SETTLE_S = 0.35


# ---------------------------------------------------------------------------
# Pneumatic actuator states
# ---------------------------------------------------------------------------

PNEUMATIC_RETRACT = 0
PNEUMATIC_EXTEND = 1

PNEUMATIC_FRONT_DEFAULT = PNEUMATIC_RETRACT
PNEUMATIC_BACK_DEFAULT = PNEUMATIC_RETRACT

PNEUMATIC_FRONT_FIRE_S = 0.25
PNEUMATIC_BACK_FIRE_S = 0.25
PNEUMATIC_SEQUENCE_GAP_S = 0.15


# ---------------------------------------------------------------------------
# LED / buzzer feedback
# ---------------------------------------------------------------------------

LED_MODE_SOLID = 1
LED_MODE_BLINK = 2
LED_MODE_BREATH = 3

LED_RED = (255, 0, 0)
LED_GREEN = (0, 255, 0)
LED_BLUE = (0, 60, 255)
LED_YELLOW = (255, 180, 0)
LED_PURPLE = (160, 0, 255)
LED_OFF = (0, 0, 0)

BUZZER_START_MS = 120
BUZZER_DONE_MS = 500
BUZZER_ERROR_MS = 1_000


# ---------------------------------------------------------------------------
# PCA9685 motor channel mapping
# ---------------------------------------------------------------------------

# Format follows command:
# K <m1a> <m1b> <m2a> <m2b> <m3a> <m3b> <m4a> <m4b>
#
# Replace these with the real PCA9685 channels after wiring is finalized.
MOTOR_PCA_CHANNELS = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
)


# ---------------------------------------------------------------------------
# Match flow defaults
# ---------------------------------------------------------------------------

WAIT_FOR_ENTER_START = True
ZERO_ODOMETRY_ON_START = True
ENABLE_DEADWHEEL_ON_START = True
STOP_ON_EXIT = True

