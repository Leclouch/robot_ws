#!/usr/bin/env python3
"""Interactive Jetson-to-Teensy hardware smoke test.

Run this with the robot raised safely or with wheels clear for the first pass.
Every movement waits for explicit operator confirmation.
"""

import argparse
import os
import sys
import time


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import ActuatorConfig, KinematicConfig
from hardware.serial_interface import RobotController


def ask(prompt, default_yes=False):
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"{prompt} {suffix}: ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "yes")


def wait_connection(robot, timeout_s):
    print(f"[TEST] Waiting for Teensy connection for up to {timeout_s:.1f}s...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if robot.is_connected:
            print("[TEST] Teensy connected.")
            return True
        time.sleep(0.2)
    print("[TEST] Teensy not connected.")
    return False


def run_motion(robot, label, forward=0.0, left=0.0, turn_deg=0.0, timeout=6.0):
    print(f"\n[MOTION] {label}")
    print(f"         forward={forward:.3f}m left={left:.3f}m turn={turn_deg:.1f}deg")
    if not ask("Run this movement?"):
        print("[SKIP] Movement skipped.")
        return True

    robot.move_relative(forward=forward, left=left, turn_deg=turn_deg)
    ok = robot.wait_until_idle(timeout=timeout)
    print("[OK] Movement reached idle." if ok else "[FAIL] Movement failed or timed out.")
    return ok


def run_servo(robot, label, pin, angle, delay_s):
    print(f"\n[SERVO] {label}: pin={pin}, angle={angle}")
    if not ask("Run this servo command?"):
        print("[SKIP] Servo command skipped.")
        return
    robot.set_servo(pin, angle)
    time.sleep(delay_s)


def run_pneumatic(robot, label, front, back, delay_s):
    print(f"\n[PNEUMATIC] {label}: front={front}, back={back}")
    if not ask("Run this pneumatic command?"):
        print("[SKIP] Pneumatic command skipped.")
        return
    robot.set_pneumatics(front_state=front, back_state=back)
    time.sleep(delay_s)


def print_odom(robot):
    print(
        "[ODOM] "
        f"FWD/X={robot.odom_x:.3f}m  "
        f"STRF/Y={robot.odom_y:.3f}m  "
        f"THETA={robot.odom_theta_deg:.2f}deg"
    )


def main():
    parser = argparse.ArgumentParser(description="Interactive Teensy connection and hardware test.")
    parser.add_argument("--move", type=float, default=0.20, help="Small translation test distance in meters.")
    parser.add_argument("--turn", type=float, default=20.0, help="Small turn test angle in degrees.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Connection wait timeout in seconds.")
    args = parser.parse_args()

    print("=========================================")
    print("JETSON <-> TEENSY CONNECTION TEST")
    print("=========================================")
    print("Safety checklist:")
    print("- Put robot on blocks or give it clear floor space.")
    print("- Keep one hand near physical power/E-Stop.")
    print("- Confirm direction visually after every movement.")

    if not ask("\nStart test now?"):
        return 0

    robot = RobotController()
    try:
        if not wait_connection(robot, args.timeout):
            return 1

        robot.set_led(1, 0, 255, 0)
        robot.trigger_buzzer(120)
        time.sleep(0.2)

        print("\n[ZERO] Resetting odometry.")
        robot.zero_odom()
        time.sleep(0.5)
        print_odom(robot)

        print("\n=== MOVEMENT DIRECTION TESTS ===")
        print("Expected convention from Python:")
        print("- forward positive: robot moves forward")
        print("- left positive: robot strafes left")
        print("- turn_deg positive: robot turns positive yaw according to Teensy convention")

        run_motion(robot, "Forward test", forward=args.move)
        print_odom(robot)
        run_motion(robot, "Backward test", forward=-args.move)
        print_odom(robot)
        run_motion(robot, "Left strafe test", left=args.move)
        print_odom(robot)
        run_motion(robot, "Right strafe test", left=-args.move)
        print_odom(robot)
        run_motion(robot, "Turn positive test", turn_deg=args.turn)
        print_odom(robot)
        run_motion(robot, "Turn negative test", turn_deg=-args.turn)
        print_odom(robot)

        print("\n=== SERVO TESTS ===")
        run_servo(robot, "Open gripper", ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN, ActuatorConfig.DELAY_GRIP_SEC)
        run_servo(robot, "Close gripper", ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_CLOSE, ActuatorConfig.DELAY_GRIP_SEC)
        run_servo(robot, "Arm down", ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN, ActuatorConfig.DELAY_ARM_SEC)
        run_servo(robot, "Arm up", ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_UP, ActuatorConfig.DELAY_ARM_SEC)

        print("\n=== PNEUMATIC TESTS ===")
        run_pneumatic(robot, "Both extend", True, True, ActuatorConfig.DELAY_PNEU_SEC)
        run_pneumatic(robot, "Both retract", False, False, ActuatorConfig.DELAY_PNEU_SEC)
        run_pneumatic(robot, "Front only", True, False, ActuatorConfig.DELAY_PNEU_SEC)
        run_pneumatic(robot, "Back only", False, True, ActuatorConfig.DELAY_PNEU_SEC)
        run_pneumatic(robot, "Safe retract", False, False, ActuatorConfig.DELAY_PNEU_SEC)

        print("\n=== DEADWHEEL / FEEDBACK TEST ===")
        if ask("Disable deadwheels briefly?"):
            robot.set_deadwheels(False)
            time.sleep(0.5)
        if ask("Enable deadwheels again?", default_yes=True):
            robot.set_deadwheels(True)
            time.sleep(0.5)

        print("\n=== EMERGENCY STOP TEST ===")
        if ask("Send E-Stop command now?", default_yes=True):
            robot.e_stop()
            robot.set_led(2, 255, 0, 0)

        print("\n[RESULT] Manual verification required:")
        print("- Did forward/backward directions match?")
        print("- Did left/right strafe directions match?")
        print("- Did gripper open/close match config angles?")
        print("- Did arm up/down match config angles?")
        print("- Did pneumatics map front/back correctly?")
        print("\nIf any direction is inverted, update Teensy motor mapping or Python sign config.")
        return 0
    finally:
        robot.e_stop()
        robot.close()


if __name__ == "__main__":
    raise SystemExit(main())
