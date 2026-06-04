# ==========================================
# FILE: core/arena_2.py
# ==========================================
import os
import sys

# Add project root to sys.path to allow standalone execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from hardware.serial_interface import RobotController
from core.path_planner import PathPlanner

def run_arena_2(robot, planner, is_running_cb=None):
    """
    STRATEGI ARENA 2: SEKUENS PNEUMATIK FOREST
    
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
    print("[FSM] >>> STRATEGI ARENA 2 DIMULAI <<<")
    print("="*40)
    robot.set_led(1, 255, 165, 0) # LED Oranye = Memasuki Wilayah Hutan

    # 1. Bergerak dari area Rak menuju depan gerbang Hutan
    fwd, left = planner.get_arena_2_target()
    print(f"[ARENA 2] Menuju Depan Forest -> Fwd: {fwd}m, Left: {left}m")
    robot.move_relative(forward=fwd, left=left)
    if not robot.wait_until_idle(): return False

    if not check_running(): return False

    # 2. Seluruh urutan manjat hutan dijalankan secara atomik oleh Teensy.
    print("[ARENA 2] Mengirim command Macro N ke Teensy...")
    if not robot.run_macro_n(): return False

    if not check_running(): return False

    # Macro N mematikan deadwheel. Aktifkan kembali untuk navigasi arena berikutnya.
    print("[ARENA 2] Macro N selesai. Mengaktifkan kembali deadwheel...")
    robot.set_deadwheels(True)

    print("[FSM] >>> ARENA 2 SELESAI DENGAN SUKSES <<<")
    return True
