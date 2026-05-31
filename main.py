# ==========================================
# main.py
# ==========================================
import tkinter as tk
from core.fsm_master import AutonomousFSM
from ui.dashboard import RobotDashboard

if __name__ == "__main__":
    # 1. Bangun Object Otak FSM Robot
    robot_system = AutonomousFSM()

    # 2. Setup Tkinter Window Master GUI
    window_root = tk.Tk()
    app = RobotDashboard(window_root, robot_system)

    try:
        # 3. Jalankan Loop Tampilan Antarmuka (Blocking Thread Utama)
        window_root.mainloop()
    except KeyboardInterrupt:
        print("\n[OPERATOR] Dashboard ditutup paksa.")
    finally:
        # Bersihkan port serial saat aplikasi di-close
        robot_system.shutdown()
        print("[SYSTEM] Sistem Robot Berhasil Dimatikan Bersih.")
