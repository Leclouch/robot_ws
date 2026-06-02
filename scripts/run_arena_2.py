#!/usr/bin/env python3
# ==========================================
# FILE: scripts/run_arena_2.py
# ==========================================
import os
import sys
import time

# Resolve project root path dynamically
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from hardware.serial_interface import RobotController
from core.path_planner import PathPlanner
from core.arena_2 import run_arena_2

def main():
    print("=========================================")
    print("STANDALONE RUNNER: ARENA 2 (PNEUMATIC FOREST)")
    print("=========================================")
    print("Safety Check: Make sure pneumatic air pressure is ON and path is clear.")
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

    print("[SYSTEM] Initializing Path Planner...")
    planner = PathPlanner()

    # Optional: Configure KFS target coordinate
    kfs_coord = input("Enter KFS R2 grid coordinate (e.g. '1,2') or press ENTER to use default: ").strip()
    if kfs_coord:
        try:
            row, col = map(int, kfs_coord.split(","))
            planner.set_kfs_grid("R2", row, col)
        except ValueError:
            print("[WARNING] Invalid format. Proceeding with defaults.")

    try:
        # Zero odometry before starting
        print("[SYSTEM] Resetting Robot Odometry...")
        robot.zero_odom()
        robot.trigger_buzzer(150)
        
        # Run Arena 2 strategy
        success = run_arena_2(robot, planner)
        
        if success:
            print("\n=========================================")
            print("[SUCCESS] Arena 2 completed successfully!")
            print("=========================================")
            robot.trigger_buzzer(500)
        else:
            print("\n=========================================")
            print("[FAILED] Arena 2 failed or was interrupted.")
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
