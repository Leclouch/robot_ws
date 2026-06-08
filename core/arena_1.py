# ==========================================
# FILE: core/arena_1.py
# ==========================================
import os
import sys
import time

# Add project root to sys.path to allow standalone execution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from hardware.serial_interface import RobotController
from config import ActuatorConfig, VisionConfig
from vision.visual_servoing import SpearheadVisualServo

def run_arena_1(robot, vision, is_running_cb=None):
    """
    STRATEGI ARENA 1: START & AMBIL SPEARHEAD
    
    Args:
        robot: Instance of RobotController
        vision: Instance of SpearheadVisualServo
        is_running_cb: Optional callback function returning a boolean, 
                       used to check if execution is allowed to continue.
    """
    def check_running():
        if is_running_cb is not None:
            return is_running_cb()
        return True

    def ensure_connection(stage):
        if robot.is_connected:
            return True

        print(f"[ARENA 1] Koneksi serial putus saat {stage}. Menunggu reconnect...")
        if not robot.wait_for_connection():
            print("[ARENA 1] Reconnect gagal. Arena 1 dihentikan.")
            return False

        print("[ARENA 1] Serial reconnect berhasil. Memberi indikator kuning.")
        robot.set_led(1, 255, 255, 0)
        robot.trigger_buzzer(150)
        time.sleep(0.3)
        return True

    print("\n" + "="*40)
    print("[FSM] >>> STRATEGI ARENA 1 DIMULAI <<<")
    print("="*40)
    if not ensure_connection("start arena"): return False
    robot.set_led(1, 0, 255, 0) # LED Hijau 
    # robot.move_relative(left=0.3)
    # if not robot.wait_until_idle(): return False

    print("[ARENA 1] Menurunkan Arm...")
    if not ensure_connection("turun arm"): return False
    robot.set_led(1, 0, 0, 255) # Biru
    # robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
    # time.sleep(ActuatorConfig.DELAY_ARM_SEC)

    print("[ARENA 1] Menunggu sasis stabil sebelum Visual Servoing...")
    time.sleep(VisionConfig.PRE_VISUAL_SERVOING_SETTLE_SEC)


    # # 1. Visual Servoing (Koreksi Kanan/Kiri Pas)
    # print("[ARENA 1] Mengaktifkan Visual Servoing...")
    # if not ensure_connection("visual servoing"): return False
    # robot.set_led(3, 255, 255, 0) # Bernapas Kuning
    
    # # Fungsi align() ini membaca kamera dan menggerakkan sasis kanan/kiri
    # # sampai centroid target sejajar dengan garis target vertikal.
    # if not vision.align(robot):
    #     return False
    # print("[ARENA 1] Target Terkunci Presisi!")

    # # print("[ARENA 1] Mengangkat Arm...")
    # # if not ensure_connection("angkat arm"): return False
    # # robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_UP)
    # # time.sleep(ActuatorConfig.DELAY_ARM_SEC)

    # # 2. Gerakan Sequence Makro Ambil
    # print("[ARENA 1] Membuka Gripper...")
    # if not ensure_connection("buka gripper"): return False
    # robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
    # time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

    # print("[ARENA 1] Menurunkan Arm...")
    # if not ensure_connection("turun arm"): return False
    # robot.set_led(1, 0, 0, 255) # Biru
    # robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
    # time.sleep(ActuatorConfig.DELAY_ARM_SEC)

    # print("[ARENA 1] Mundur 0.85m...")
    # if not ensure_connection("mundur ambil spearhead"): return False
    # robot.move_relative(forward=-0.93)
    # if not robot.wait_until_idle(): return False

    # print("[ARENA 1] Menutup Gripper...")
    # if not ensure_connection("tutup gripper"): return False
    # robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_CLOSE)
    # time.sleep(1.0)

    # print("[ARENA 1] Mundur 0.3m...")
    # robot.move_relative(left=0.03)
    # if not robot.wait_until_idle(): return False

    print("[ARENA 1] Mengangkat Arm...")
    if not ensure_connection("angkat arm setelah grip"): return False
    robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_UP)
    time.sleep(4.0)

    print("[ARENA 1] Maju 0.5m...")
    if not ensure_connection("maju keluar rack"): return False
    robot.move_relative(forward=0.50)
    if not robot.wait_until_idle(): return False

    print("[ARENA 1] Rotate 180 Derajat...")
    if not ensure_connection("rotasi 180"): return False
    robot.move_relative(turn_deg=190.0)
    if not robot.wait_until_idle(): return False

    print("[ARENA 1] Memulai deteksi kilatan cahaya hijau redup...")
    baseline_brightness = None
    # Kumpulkan beberapa frame untuk menstabilkan auto-exposure (fokus pada channel Hijau)
    for _ in range(15):
        if not check_running(): return False
        ret, frame = vision.read_latest_frame()
        if ret and frame is not None:
            brightness = float(frame[:, :, 1].mean())  # Index 1 = Green channel
            if baseline_brightness is None:
                baseline_brightness = brightness
            else:
                baseline_brightness = 0.8 * baseline_brightness + 0.2 * brightness
        time.sleep(0.05)

    if baseline_brightness is None:
        baseline_brightness = 100.0  # fallback
    print(f"[ARENA 1] Baseline brightness (Hijau): {baseline_brightness:.2f}")

    print("[ARENA 1] Menunggu kilatan cahaya hijau untuk membuka gripper...")
    flash_detected = False
    try:
        while not flash_detected:
            if not check_running(): return False
            if not ensure_connection("tunggu kilatan cahaya"): return False
            
            ret, frame = vision.read_latest_frame()
            if not ret or frame is None:
                time.sleep(0.05)
                continue
            
            blue_mean = float(frame[:, :, 0].mean())
            green_mean = float(frame[:, :, 1].mean())
            red_mean = float(frame[:, :, 2].mean())
            
            # Kriteria kilatan hijau redup:
            # 1. Kecerahan hijau naik minimal 15 poin dibanding baseline hijau
            # 2. Nilai hijau lebih dominan daripada merah dan biru
            if (green_mean - baseline_brightness > 15.0) and (green_mean > max(blue_mean, red_mean) + 8.0):
                print(f"[ARENA 1] KILATAN HIJAU TERDETEKSI! Green: {green_mean:.2f} (Baseline: {baseline_brightness:.2f}, Blue: {blue_mean:.2f}, Red: {red_mean:.2f})")
                flash_detected = True
            else:
                # Update baseline secara perlahan (slow drift adaptation)
                baseline_brightness = 0.99 * baseline_brightness + 0.01 * green_mean
            
            if VisionConfig.SHOW_DEBUG_WINDOW:
                import cv2
                cv2.imshow("Flash Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            time.sleep(0.02)
    finally:
        vision.close()
        if VisionConfig.SHOW_DEBUG_WINDOW:
            try:
                import cv2
                cv2.destroyWindow("Flash Detection")
            except Exception:
                pass

    print("[ARENA 1] Membuka Gripper...")
    if not ensure_connection("buka gripper"): return False
    robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
    time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

    # # 3. Logika Deteksi AprilTag
    # print("[ARENA 1] Mencari AprilTag...")
    # apriltag_detected = False
    
    # # Loop sampai AprilTag terlihat
    # while not apriltag_detected:
    #     if not ensure_connection("deteksi apriltag"): return False
    #     apriltag_detected, tag_id = vision.detect_apriltag()
        
    #     if not check_running(): return False # Proteksi jika E-Stop ditekan
    #     time.sleep(0.1)

    # print("[ARENA 1] AprilTag Terlihat! Membuka Gripper...")
    # if not ensure_connection("buka gripper apriltag"): return False
    # robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
    # time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

    # print("[ARENA 1] Menunggu AprilTag menghilang dari pantauan kamera...")
    # # Loop menahan FSM sampai AprilTag hilang (diambil/tertutup)
    # while apriltag_detected:
    #     if not ensure_connection("menunggu apriltag hilang"): return False
    #     apriltag_detected, tag_id = vision.detect_apriltag()
        
    #     if not check_running(): return False 
    #     time.sleep(0.1)

    # print("[ARENA 1] AprilTag menghilang. Lanjut pindah state ke R2!")
    # return True
