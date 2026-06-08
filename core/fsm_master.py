# ==========================================
# FILE: core/fsm_master.py
# ==========================================
import time
from hardware.serial_interface import RobotController
from core.path_planner import PathPlanner
from config import ActuatorConfig
from vision.visual_servoing import SpearheadVisualServo
from core.arena_1 import run_arena_1
from core.arena_2 import run_arena_2
from core.arena_3 import run_arena_3

class AutonomousFSM:
    def __init__(self):
        # Inisialisasi interface komunikasi serial dan pengelola rute
        self.robot = RobotController()
        self.planner = PathPlanner()
        
        # Variabel pemantau status arena aktif (bisa dibaca oleh modul GUI nanti)
        self.current_arena = "STANDBY" 
        self.is_running = True
        
        # Jeda waktu tunggu koneksi USB serial stabil saat program baru dibuka
        time.sleep(3)
        self.robot.set_led(1, 255, 0, 0) # LED Merah Solid = Standby Awal
        print("[FSM] Otak Utama Full Auto berhasil diinisialisasi.")

    # ==========================================
    # STRATEGI ARENA 1: START & AMBIL SPEARHEAD
    # ==========================================
    def run_arena_1(self):
        vision = SpearheadVisualServo()
        return run_arena_1(self.robot, vision, lambda: self.is_running)

    # ==========================================
    # STRATEGI ARENA 2: SEKUENS PNEUMATIK FOREST
    # ==========================================
    def run_arena_2(self):
        return run_arena_2(self.robot, self.planner, lambda: self.is_running)

    # ==========================================
    # STRATEGI ARENA 3: SCORING / DROP OBJEK
    # ==========================================
    def run_arena_3(self):
        return run_arena_3(self.robot, self.planner, lambda: self.is_running)

    # ==========================================
    # LOOP UTAMA PENGENDALI OTOMATIS (RUNNER)
    # ==========================================
    def start_full_auto(self):
        """Fungsi utama pembuka jalannya laga otonom tanpa intervensi keyboard."""
        print("\n=== SYSTEM STANDBY: MENUNGGU SINYAL TOMBOL START DI SASIS ===")
        input("Tekan [ENTER] pada laptop untuk mensimulasikan penekanan tombol START fisik...")
        self.trigger_full_auto()

    def trigger_full_auto(self):
        """Memulai rangkaian full auto dari GUI atau wrapper lain."""
        self.is_running = True
        
        # Reset nilai koordinat odometri di titik awal awal lapangan
        self.robot.zero_odom()
        self.robot.trigger_buzzer(200)
        
        # --- EKSEKUSI BERURUTAN ANTAR ZONA ARENA ---
        
        self.current_arena = "ARENA_1"
        if not self.run_arena_1():
            self.emergency_stop_handler("Gagal navigasi/aktuasi mekanis di Arena 1")
            return

        self.current_arena = "ARENA_2"
        if not self.run_arena_2():
            self.emergency_stop_handler("Gagal memanjat/melewati rintangan di Arena 2")
            return

        self.current_arena = "ARENA_3"
        if not self.run_arena_3():
            self.emergency_stop_handler("Gagal menaruh poin di Arena 3")
            return

        # --- SELESAI TOTAL (VICTORY) ---
        print("\n" + "#"*50)
        print("[VICTORY] ROBOT BERHASIL MENYELESAIKAN GAME FIELD KRAI!")
        print("#"*50)
        self.robot.set_led(2, 0, 255, 0) # LED Berkedip Hijau tanda finish sempurna
        self.robot.trigger_buzzer(1500)

    def trigger_retry_arena(self, arena_id):
        """Menjalankan ulang arena tertentu dari dashboard dan melanjutkan sekuens."""
        self.is_running = True
        
        # --- LANJUTKAN DARI ARENA YANG DIPILIH ---
        if arena_id == 1:
            self.current_arena = "RETRY_ARENA_1"
            if not self.run_arena_1():
                self.emergency_stop_handler("Retry Arena 1 gagal")
                return
            arena_id = 2  # Lanjut ke Arena 2 setelah Arena 1 sukses

        if arena_id == 2:
            self.current_arena = "RETRY_ARENA_2"
            if not self.run_arena_2():
                self.emergency_stop_handler("Retry Arena 2 gagal")
                return
            arena_id = 3  # Lanjut ke Arena 3 setelah Arena 2 sukses

        if arena_id == 3:
            self.current_arena = "RETRY_ARENA_3"
            if not self.run_arena_3():
                self.emergency_stop_handler("Retry Arena 3 gagal")
                return

        # --- SELESAI TOTAL (VICTORY) ---
        print("\n" + "#"*50)
        print("[VICTORY] ROBOT BERHASIL MENYELESAIKAN GAME FIELD KRAI!")
        print("#"*50)
        self.robot.set_led(2, 0, 255, 0) # LED Berkedip Hijau tanda finish sempurna
        self.robot.trigger_buzzer(1500)

    def trigger_stop(self):
        """Callback dashboard untuk menghentikan robot dan FSM."""
        self.is_running = False
        self.current_arena = "EMERGENCY_STOP"
        self.robot.e_stop()

    def trigger_reset(self):
        """Callback dashboard untuk reset odometri dan state aman."""
        self.is_running = False
        self.current_arena = "STANDBY"
        self.robot.e_stop()
        self.robot.zero_odom()

    def emergency_stop_handler(self, alasan_fail):
        """Menghentikan robot seketika jika terdeteksi kegagalan gerak di arena."""
        self.is_running = False
        print(f"\n[FATAL ERROR] {alasan_fail}!")
        print("[RECOVERY] Mengirimkan sinyal rem darurat ke sasis bawah...")
        self.robot.e_stop()
        self.robot.set_led(2, 255, 0, 0) # LED Berkedip Merah tanda intervensi manual diperlukan

    def shutdown(self):
        """Mematikan thread serial background pendukung saat aplikasi di-close."""
        self.is_running = False
        self.robot.close()
