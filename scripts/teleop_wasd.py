#!/usr/bin/env python3
"""Interactive Terminal Keyboard Teleoperation for the robot.

Allows directional WASD movement, rotation, arm/gripper control, 
and displays real-time odometry feedback.
"""

import os
import sys
import time
import select
import termios
import tty

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from hardware.serial_interface import RobotController
from config import ActuatorConfig


def getch_nonblocking():
    """Read a single character from terminal non-blockingly."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        # Wait up to 50ms for keypress
        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
        if rlist:
            return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None


def print_ui(robot, dist_step, angle_step, front_pneu, back_pneu, last_action):
    """Draw a beautiful real-time dashboard in the terminal."""
    # ANSI escape code: clear screen and move cursor to top-left
    sys.stdout.write("\033[2J\033[H")
    
    status_str = "CONNECTED" if robot.is_connected else "DISCONNECTED"
    status_color = "\033[92m" if robot.is_connected else "\033[91m"
    
    print("\033[95m" + "=" * 55 + "\033[0m")
    print("      \033[1m🤖 ROBOT KEYBOARD TELEOP CONTROLLER 🤖\033[0m")
    print("\033[95m" + "=" * 55 + "\033[0m")
    print(f" Status: {status_color}{status_str}\033[0m")
    print(f" Step Distance: \033[96m{dist_step:.2f} m\033[0m  (Adjust with [ and ])")
    print(f" Step Angle:    \033[96m{angle_step:.1f} °\033[0m  (Adjust with ; and ')")
    print("\033[95m" + "-" * 55 + "\033[0m")
    
    # Live Odometry
    print(" 📍 \033[1mLIVE ODOMETRY FEEDBACK\033[0m")
    print(f"   X (Forward): \033[93m{robot.odom_x:7.3f} m\033[0m")
    print(f"   Y (Strafe):  \033[93m{-robot.odom_y:7.3f} m\033[0m")
    print(f"   Yaw Angle:   \033[93m{robot.odom_theta_deg:7.2f} °\033[0m")
    print("\033[95m" + "-" * 55 + "\033[0m")
    
    # Actuator State Visualizer
    front_str = "\033[92mEXT\033[0m" if front_pneu else "\033[91mRET\033[0m"
    back_str = "\033[92mEXT\033[0m" if back_pneu else "\033[91mRET\033[0m"
    
    print(" 🔧 \033[1mACTUATORS & UTILITIES\033[0m")
    print("   [O] Open Gripper   |  [C] Close Gripper")
    print("   [U] Arm UP         |  [J] Arm DOWN")
    print(f"   [F] Front Pneu ({front_str}) |  [B] Back Pneu ({back_str})")
    print("   [T] Extend Both    |  [R] Retract Both")
    print("   [N] Trigger Macro N|  [Z] Zero Odometry")
    print("   [Space / X] E-STOP")
    print("\033[95m" + "-" * 55 + "\033[0m")
    
    # Movement Legend
    print(" 🎮 \033[1mMOVEMENT CONTROLS\033[0m")
    print("          [W] Forward")
    print("   [A] Left   [S] Back   [D] Right")
    print("       (Rotate: [Q] Left / [E] Right)")
    print("\033[95m" + "=" * 55 + "\033[0m")
    print(f" Last Command: \033[94m\033[1m{last_action}\033[0m")
    print(" Press \033[91m[ESC]\033[0m or \033[91m[Ctrl+C]\033[0m to safely exit.")
    sys.stdout.flush()


def main():
    print("[SYSTEM] Connecting to Teensy Serial Controller...")
    robot = RobotController()
    
    # Wait for the serial connection to stabilize
    time.sleep(2.0)
    
    dist_step = 0.05  # Default: 5cm step
    angle_step = 10.0  # Default: 10 degrees turn
    front_pneu = False
    back_pneu = False
    last_action = "None"
    
    try:
        while True:
            print_ui(robot, dist_step, angle_step, front_pneu, back_pneu, last_action)
            key = getch_nonblocking()
            
            if key is None:
                continue
                
            key_lower = key.lower()
            
            # --- QUIT ---
            if key == "\x1b" or key_lower == "q" and key != "q":  # Escape Key or standard quit checks
                break
            if key_lower == "\x03":  # Ctrl+C
                break
                
            # --- MOVEMENT ---
            if key_lower == "w":
                robot.move_relative(forward=dist_step)
                last_action = f"Move Forward {dist_step:.2f}m"
            elif key_lower == "s":
                robot.move_relative(forward=-dist_step)
                last_action = f"Move Backward {dist_step:.2f}m"
            elif key_lower == "a":
                robot.move_relative(left=dist_step)
                last_action = f"Strafe Left {dist_step:.2f}m"
            elif key_lower == "d":
                robot.move_relative(left=-dist_step)
                last_action = f"Strafe Right {dist_step:.2f}m"
            elif key_lower == "q":
                robot.move_relative(turn_deg=angle_step)
                last_action = f"Rotate Left {angle_step:.1f}°"
            elif key_lower == "e":
                robot.move_relative(turn_deg=-angle_step)
                last_action = f"Rotate Right {angle_step:.1f}°"
                
            # --- ACTUATORS ---
            elif key_lower == "o":
                robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
                last_action = "Open Gripper"
            elif key_lower == "c":
                robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_CLOSE)
                last_action = "Close Gripper"
            elif key_lower == "u":
                robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_UP)
                last_action = "Raise Arm (UP)"
            elif key_lower == "j":
                robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
                last_action = "Lower Arm (DOWN)"
            elif key_lower == "n":
                last_action = "Running Macro N..."
                print_ui(robot, dist_step, angle_step, front_pneu, back_pneu, last_action)
                if robot.run_macro_n():
                    last_action = "Macro N Completed Successfully"
                    robot.set_deadwheels(True)
                    front_pneu = False
                    back_pneu = False
                else:
                    last_action = "Macro N Failed / Timeout"
            elif key_lower == "f":
                front_pneu = not front_pneu
                robot.set_pneumatics(front=front_pneu, back=back_pneu)
                last_action = f"Toggled Front Pneumatic to {'EXT' if front_pneu else 'RET'}"
            elif key_lower == "b":
                back_pneu = not back_pneu
                robot.set_pneumatics(front=front_pneu, back=back_pneu)
                last_action = f"Toggled Back Pneumatic to {'EXT' if back_pneu else 'RET'}"
            elif key_lower == "t":
                front_pneu = True
                back_pneu = True
                robot.set_pneumatics(front=True, back=True)
                last_action = "Extended Both Pneumatics"
            elif key_lower == "r":
                front_pneu = False
                back_pneu = False
                robot.set_pneumatics(front=False, back=False)
                last_action = "Retracted Both Pneumatics"
                
            # --- UTILITIES ---
            elif key_lower == "z":
                robot.zero_odom()
                last_action = "Zeroed Odometry"
            elif key == " " or key_lower == "x":
                robot.e_stop()
                last_action = "🚨 EMERGENCY STOP (E-STOP) SENT 🚨"
                
            # --- ADJUST STEP SIZES ---
            elif key == "[":
                dist_step = max(0.01, dist_step - 0.01)
                last_action = "Decreased distance step size"
            elif key == "]":
                dist_step = min(1.0, dist_step + 0.01)
                last_action = "Increased distance step size"
            elif key == ";":
                angle_step = max(1.0, angle_step - 1.0)
                last_action = "Decreased rotation angle step size"
            elif key == "'":
                angle_step = min(90.0, angle_step + 1.0)
                last_action = "Increased rotation angle step size"
                
    except KeyboardInterrupt:
        pass
    finally:
        # Safely shut down Teensy connection and restore terminal
        print("\n[SYSTEM] Safely terminating Teensy connection...")
        robot.e_stop()
        robot.close()
        print("[SYSTEM] Done.")


if __name__ == "__main__":
    main()
