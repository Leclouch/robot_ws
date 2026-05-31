# ==========================================
# FILE: main.py
# ==========================================
import threading
import sys

from core.fsm_master import AutonomousFSM
from ui.dashboard import RobotDashboard
# from vision.visual_servoing import VisionDetector # Uncomment jika kamera sudah siap


def run_fsm_background(fsm_instance):
    """
    Fungsi pembungkus (wrapper) untuk menjalankan urutan Full Auto FSM.
    Berjalan di background thread agar tidak memblokir Main Loop GUI Tkinter.
    """
    try:
        fsm_instance.start_full_auto()
    except Exception as e:
        print(f"\n[FATAL ERROR] Otak FSM Terhenti karena error sistem: {e}")
        fsm_instance.emergency_stop_handler("FSM Crash System")


if __name__ == "__main__":
    print("=========================================")
    print("🚀 INISIALISASI SISTEM ROBOT KRAI 🚀")
    print("=========================================")

    # 1. Inisialisasi Master FSM (Otak Robot & Serial Interface)
    try:
        auto_robot = AutonomousFSM()
    except Exception as e:
        print(f"[FATAL] Gagal menginisialisasi FSM/Serial: {e}")
        sys.exit(1)

    # (Opsional) Inisialisasi Kamera lalu suntikkan ke objek FSM
    # auto_robot.vision = VisionDetector()

    # 2. Pisahkan Eksekusi FSM ke Background Thread
    # Thread daemon akan otomatis mati jika program utama (GUI) ditutup
    fsm_thread = threading.Thread(target=run_fsm_background, args=(auto_robot,))
    fsm_thread.daemon = True
    fsm_thread.start()

    # 3. Inisialisasi & Jalankan GUI (Dashboard) di Main Thread
    print("[SYSTEM] Membuka Antarmuka Dashboard Operator...")
    dashboard = RobotDashboard(auto_robot)

    try:
        # Menahan program utama di sini. GUI akan tampil dan terus ter-update secara visual.
        dashboard.run()
    except KeyboardInterrupt:
        print("\n[OPERATOR] Program dihentikan paksa via Terminal (Ctrl+C).")
    finally:
        # Jika GUI ditutup (tanda X ditekan) atau terjadi interupsi, bersihkan seluruh koneksi
        print("[SYSTEM] Menutup program dan mematikan koneksi robot...")
        auto_robot.shutdown()

        # Uncomment baris di bawah ini jika modul vision sudah dipakai
        # if hasattr(auto_robot, 'vision'): auto_robot.vision.close()

        print("[SYSTEM] Selesai. Have a good rest!")
        sys.exit(0)
