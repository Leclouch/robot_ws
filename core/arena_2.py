# ==========================================
# FILE: core/arena_2.py
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

    # 2. Urutan Manjat Hutan Berbasis Waktu & Sensor (Pindahan Macro N C++)
    print("[ARENA 2] Mengembangkan Kedua Pneumatik (HIGH) & Proteksi Deadwheel...")
    robot.set_pneumatics(front_state=True, back_state=True)
    robot.set_deadwheels(False) # Matikan deadwheel agar akumulasi odometri aman
    time.sleep(ActuatorConfig.DELAY_PNEU_SEC)

    if not check_running(): return False

    print("[ARENA 2] Langkah 1: Dorong Maju Sasis Pertama (55cm)...")
    robot.move_relative(forward=0.55)
    if not robot.wait_until_idle(): return False

    if not check_running(): return False

    print("[ARENA 2] Langkah 2: Menarik Naik Pneumatik DEPAN (LOW)...")
    robot.set_pneumatics(front_state=False, back_state=True)
    time.sleep(ActuatorConfig.DELAY_PNEU_SEC)

    if not check_running(): return False

    print("[ARENA 2] Langkah 3: Dorong Maju Sasis Kedua (47cm)...")
    robot.move_relative(forward=0.47)
    if not robot.wait_until_idle(): return False

    if not check_running(): return False

    print("[ARENA 2] Langkah 4: Menarik Naik Pneumatik BELAKANG (LOW)...")
    robot.set_pneumatics(front_state=False, back_state=False)
    time.sleep(ActuatorConfig.DELAY_PNEU_SEC)

    if not check_running(): return False

    print("[ARENA 2] Langkah 5: Dorong Akhir Melewati Batas Keluar Hutan (17cm)...")
    robot.move_relative(forward=0.17)
    if not robot.wait_until_idle(): return False

    print("[FSM] >>> ARENA 2 SELESAI DENGAN SUKSES <<<")
    return True
