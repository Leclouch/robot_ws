#!/usr/bin/env python3
# ==========================================
# FILE: scripts/run_arena_1.py
# ==========================================
import os
import sys
import time

# Resolve project root path dynamically
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from hardware.serial_interface import RobotController
from vision.visual_servoing import SpearheadVisualServo
from core.arena_1 import run_arena_1

def main():
    print("=========================================")
    print("STANDALONE RUNNER: ARENA 1 (START & GRAB)")
    print("=========================================")
    print("Safety Check: Make sure wheels are clear or robot has space.")
    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("[CANCELLED] Standalone run aborted.")
        return 0

    print("[SYSTEM] Connecting to Teensy Serial Controller...")
    robot = RobotController()
    
    # Wait for the serial port connection to stabilize
    print("[SYSTEM] Waiting for connection to stabilize (3s)...")
    time.sleep(3)
    
    if not robot.is_connected:
        print("[ERROR] Failed to connect to Teensy. Make sure it is plugged in.")
        return 1

    print("[SYSTEM] Initializing Vision System...")
    vision = SpearheadVisualServo()
    
    try:
        # Zero odometry before starting
        print("[SYSTEM] Resetting Robot Odometry...")
        robot.zero_odom()
        robot.trigger_buzzer(150)
        
        # Run Arena 1 strategy
        success = run_arena_1(robot, vision)
        
        if success:
            print("\n=========================================")
            print("[SUCCESS] Arena 1 completed successfully!")
            print("=========================================")
            robot.trigger_buzzer(500)
        else:
            print("\n=========================================")
            print("[FAILED] Arena 1 failed or was interrupted.")
            print("=========================================")
            robot.set_led(2, 255, 0, 0)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Standalone run cancelled by operator (Ctrl+C).")
    finally:
        print("[SYSTEM] Safely terminating Teensy connection...")
        robot.e_stop()
        robot.close()
        print("[SYSTEM] Run ended.")

if __name__ == "__main__":
    sys.exit(main())
