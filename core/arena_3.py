# ==========================================
# FILE: core/arena_3.py
# ==========================================
import os
import sys
import time

# Add project root to sys.path to allow standalone execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from hardware.serial_interface import RobotController
from core.path_planner import PathPlanner
from config import ActuatorConfig

def run_arena_3(robot, planner, is_running_cb=None):
    """
    STRATEGI ARENA 3: SCORING / DROP OBJEK
    
    Args:
        robot: Instance of RobotController
        planner: Instance of PathPlanner
        is_running_cb: Optional callback function returning a boolean, 
                       used to check if execution is allowed to continue.
    """
    def check_running():
        if is_running_cb is not None:
            return is_running_cb()
        return True

    print("\n" + "="*40)
    print("[FSM] >>> STRATEGI ARENA 3 DIMULAI <<<")
    print("="*40)
    robot.set_led(1, 255, 0, 255) # LED Ungu = Zona Pelepasan Poin

    # 1. Navigasi menuju titik tiang scoring akhir
    fwd, left = planner.get_arena_3_target()
    print(f"[ARENA 3] Navigasi ke Tiang Sasaran -> Fwd: {fwd}m")
    robot.move_relative(forward=fwd, left=left)
    if not robot.wait_until_idle(): return False

    if not check_running(): return False

    # 2. Urutan Mekanis Pelepasan Objek (Scoring)
    print("[ARENA 3] Menurunkan Lengan untuk Meletakkan Objek...")
    robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
    time.sleep(ActuatorConfig.DELAY_ARM_SEC)

    if not check_running(): return False

    print("[ARENA 3] Membuka Gripper...")
    robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
    time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

    print("[FSM] >>> ARENA 3 SELESAI DENGAN SUKSES <<<")
    return True
