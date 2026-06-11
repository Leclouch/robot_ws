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
    import time

    # ============================================================
    # Go Up 1
    MOVE_1_FORWARD = 0.51   # Initial orward oveent
    MOVE_2_FORWARD = 0.49   # after front retracted)
    MOVE_3_FORWARD = 0.6    # after back retracted)
    TURN_RIGHT_DEG = -90.0  # degrees: turn right (negative = CW / right)
    
    # Go Up 2
    MOVE_4_FORWARD = 0.35   # both pneumatics UP)
    MOVE_5_FORWARD = 0.55   # after front retracted)
    MOVE_6_FORWARD = 0.60   # after back retracted)
    
    # Go Down 1
    MOVE_7_FORWARD = 0.35   # edge keeping
    MOVE_8_FORWARD = 0.55   # after front extended)
    MOVE_9_FORWARD = 0.60   # after back extended)
    
    PNEU_SETTLE_SEC = 1.0  # seconds: wait after each pneumatic action
    # ============================================================

    ## --- STEP 1: Extend both pneumatics UP ---
    #print("[ARENA 2] Step 1: Extending both pneumatics...")
    #robot.set_pneumatics(front=True, back=True)
    #time.sleep(PNEU_SETTLE_SEC)
    #if not check_running(): return False
#
    ## --- STEP 2: Move forward (first segment) ---
    #print(f"[ARENA 2] Step 2: Moving forward {MOVE_1_FORWARD}m...")
    #robot.move_relative(forward=MOVE_1_FORWARD)
    #if not robot.wait_until_idle(): return False
    #if not check_running(): return False
#
    ## --- STEP 3: Retract FRONT pneumatic ---
    #print("[ARENA 2] Step 3: Retracting front pneumatic...")
    #robot.set_pneumatics(front=False, back=True)
    #time.sleep(PNEU_SETTLE_SEC)
    #if not check_running(): return False
#
    ## --- STEP 4: Move forward again (second segment) ---
    #print(f"[ARENA 2] Step 4: Moving forward {MOVE_2_FORWARD}m...")
    #robot.move_relative(forward=MOVE_2_FORWARD)
    #if not robot.wait_until_idle(): return False
    #if not check_running(): return False
#
    ## --- STEP 5: Retract BACK pneumatic ---
    #print("[ARENA 2] Step 5: Retracting back pneumatic...")
    #robot.set_pneumatics(front=False, back=False)
    #time.sleep(PNEU_SETTLE_SEC)
    #if not check_running(): return False
#
    ## --- STEP 6: Move forward (third segment) ---
    #print(f"[ARENA 2] Step 6: Moving forward {MOVE_3_FORWARD}m...")
    #robot.move_relative(forward=MOVE_3_FORWARD)
    #if not robot.wait_until_idle(): return False
    #if not check_running(): return False
#
#
    ## --- STEP 7: Turn 90° to the RIGHT ---
    #print(f"[ARENA 2] Step 7: Turning {abs(TURN_RIGHT_DEG):.0f}° RIGHT...")
    #robot.move_relative(turn_deg=TURN_RIGHT_DEG)
    #if not robot.wait_until_idle(): return False
    #if not check_running(): return False











    # --- STEP 8: Extend both pneumatics UP ---
    print("[ARENA 2] Step 8: Extending both pneumatics (UP)...")
    robot.set_pneumatics(front=True, back=True)
    time.sleep(PNEU_SETTLE_SEC)
    if not check_running(): return False

    # --- STEP 9: Move forward (2nd cycle, first segment) ---
    print(f"[ARENA 2] Step 9: Moving forward {MOVE_4_FORWARD}m...")
    robot.move_relative(forward=MOVE_4_FORWARD)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False

    # --- STEP 10: Retract FRONT pneumatic ---
    print("[ARENA 2] Step 10: Retracting front pneumatic...")
    robot.set_pneumatics(front=False, back=True)
    time.sleep(2)
    if not check_running(): return False

    # --- STEP 11: Move forward (2nd cycle, second segment) ---
    print(f"[ARENA 2] Step 11: Moving forward {MOVE_5_FORWARD}m...")
    robot.move_relative(forward=MOVE_5_FORWARD)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False

    # --- STEP 12: Retract BACK pneumatic ---
    print("[ARENA 2] Step 12: Retracting back pneumatic...")
    robot.set_pneumatics(front=False, back=False)
    time.sleep(PNEU_SETTLE_SEC)
    if not check_running(): return False

    # --- STEP 13: Move forward (2nd cycle, third segment) ---
    print(f"[ARENA 2] Step 13: Moving forward {MOVE_6_FORWARD}m...")
    robot.move_relative(forward=MOVE_6_FORWARD)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False

    # --- STEP 14: Turn 90° to the RIGHT (2nd turn, now facing DOWN) ---
    print(f"[ARENA 2] Step 14: Turning {abs(TURN_RIGHT_DEG):.0f}° RIGHT (facing DOWN)...")
    robot.move_relative(turn_deg=90.0)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False















    # --- STEP 15: Move forward/DOWN (3rd cycle, first segment) ---
    print(f"[ARENA 2] Step 15: Moving DOWN {MOVE_7_FORWARD}m...")
    robot.move_relative(forward=MOVE_7_FORWARD)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False

    # --- STEP 16: Extend FRONT pneumatic ---
    print("[ARENA 2] Step 16: Extending front pneumatic...")
    robot.set_pneumatics(front=True, back=False)
    time.sleep(PNEU_SETTLE_SEC)
    if not check_running(): return False

    # --- STEP 17: Move forward/DOWN (3rd cycle, second segment) ---
    print(f"[ARENA 2] Step 17: Moving DOWN {MOVE_8_FORWARD}m...")
    robot.move_relative(forward=MOVE_8_FORWARD)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False

    # --- STEP 18: Extend BACK pneumatic ---
    print("[ARENA 2] Step 18: Extending back pneumatic...")
    robot.set_pneumatics(front=True, back=True)
    time.sleep(PNEU_SETTLE_SEC)
    if not check_running(): return False

    # --- STEP 19: Move forward/DOWN (3rd cycle, third segment) ---
    print(f"[ARENA 2] Step 19: Moving DOWN {MOVE_9_FORWARD}m...")
    robot.move_relative(forward=MOVE_9_FORWARD)
    if not robot.wait_until_idle(): return False
    if not check_running(): return False

    # --- STEP 20: Retract BOTH pneumatics ---
    print("[ARENA 2] Step 20: Retracting both pneumatics...")
    robot.set_pneumatics(front=False, back=False)
    time.sleep(PNEU_SETTLE_SEC)
    if not check_running(): return False

    print("[FSM] >>> ARENA 2 SELESAI DENGAN SUKSES <<<")
    return True

    # # 1. Bergerak dari area Rak menuju depan gerbang Hutan
    # fwd, left = planner.get_arena_2_target()
    # print(f"[ARENA 2] Menuju Depan Forest -> Fwd: {fwd}m, Left: {left}m")
    # robot.move_relative(forward=fwd, left=left)
    # if not robot.wait_until_idle(): return False

    # if not check_running(): return False

    # # 2. Seluruh urutan manjat hutan dijalankan secara atomik oleh Teensy.
    # print("[ARENA 2] Mengirim command Macro N ke Teensy...")
    # if not robot.run_macro_n(): return False

    # if not check_running(): return False

    # # Macro N mematikan deadwheel. Aktifkan kembali untuk navigasi arena berikutnya.
    # print("[ARENA 2] Macro N selesai. Mengaktifkan kembali deadwheel...")
    # robot.set_deadwheels(True)

    print("[FSM] >>> ARENA 2 SELESAI DENGAN SUKSES <<<")
    return True
