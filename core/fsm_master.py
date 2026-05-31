# ==========================================
# FILE: core/fsm_master.py
# ==========================================
import time
from hardware.serial_interface import RobotController
from core.path_planner import PathPlanner
from config import ActuatorConfig, VisionConfig
from vision.visual_servoing import SpearheadVisualServo

class AutonomousFSM:
    def __init__(self):
        # Inisialisasi interface komunikasi serial dan pengelola rute
        self.robot = RobotController()
        self.planner = PathPlanner()
        
        # Variabel pemantau status arena aktif (bisa dibaca oleh modul GUI nanti)
        self.current_arena = "STANDBY" 
        
        # Jeda waktu tunggu koneksi USB serial stabil saat program baru dibuka
        time.sleep(3)
        self.robot.set_led(1, 255, 0, 0) # LED Merah Solid = Standby Awal
        print("[FSM] Otak Utama Full Auto berhasil diinisialisasi.")

    # ==========================================
    # STRATEGI ARENA 1: START & AMBIL SPEARHEAD
    # ==========================================
    def run_arena_1(self):
        print("\n" + "="*40)
        print("[FSM] >>> STRATEGI ARENA 1 DIMULAI <<<")
        print("="*40)
        self.robot.set_led(1, 0, 255, 0) # LED Hijau = Robot sedang berjalan

        # 1. Ambil koordinat tujuan dari planner lalu gerakkan sasis
        fwd, left = self.planner.get_arena_1_target()
        print(f"[ARENA 1] Navigasi ke Rak -> Fwd: {fwd}m, Left: {left}m")
        self.robot.move_relative(forward=fwd, left=left)
        if not self.robot.wait_until_idle(): return False # Berhenti jika kabel putus/timeout

        # 2. Transisi ke Visual Servoing untuk penguncian target tingkat milimeter
        print("[ARENA 1] Mengaktifkan Posisi via Visual Servoing...")
        self.robot.set_led(3, 255, 255, 0) # LED Bernapas Kuning = Mode Tracking Kamera
        vision = SpearheadVisualServo()
        if not vision.align(self.robot):
            return False
        print("[ARENA 1] Target Terkunci Presisi!")

        # 3. Urutan Eksekusi Mekanis Pengambilan Objek (Pindahan Macro M C++)
        print("[ARENA 1] Menurunkan Lengan Mekanik...")
        self.robot.set_led(1, 0, 0, 255) # LED Biru = Aktuator bekerja
        self.robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
        time.sleep(ActuatorConfig.DELAY_ARM_SEC)

        print("[ARENA 1] Sasis Maju Buta ke Posisi Ambil...")
        self.robot.move_relative(forward=VisionConfig.SPEARHEAD_FINAL_APPROACH_M)
        if not self.robot.wait_until_idle(): return False

        print("[ARENA 1] Mengunci Gripper (Capit)...")
        self.robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_CLOSE)
        time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

        print("[ARENA 1] Mengangkat Lengan ke Atas...")
        self.robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_UP)
        time.sleep(ActuatorConfig.DELAY_ARM_SEC)

        print("[ARENA 1] Sasis Mundur Mengamankan Posisi...")
        self.robot.move_relative(forward=0.50)
        if not self.robot.wait_until_idle(): return False

        print("[ARENA 1] Rotasi Sasis 180 Derajat (Balik Kanan)...")
        self.robot.move_relative(turn_deg=180.0)
        if not self.robot.wait_until_idle(): return False

        print("[FSM] >>> ARENA 1 SELESAI DENGAN SUKSES <<<")
        return True

    # ==========================================
    # STRATEGI ARENA 2: SEKUENS PNEUMATIK FOREST
    # ==========================================
    def run_arena_2(self):
        print("\n" + "="*40)
        print("[FSM] >>> STRATEGI ARENA 2 DIMULAI <<<")
        print("="*40)
        self.robot.set_led(1, 255, 165, 0) # LED Oranye = Memasuki Wilayah Hutan

        # 1. Bergerak dari area Rak menuju depan gerbang Hutan
        fwd, left = self.planner.get_arena_2_target()
        print(f"[ARENA 2] Menuju Depan Forest -> Fwd: {fwd}m, Left: {left}m")
        self.robot.move_relative(forward=fwd, left=left)
        if not self.robot.wait_until_idle(): return False

        # 2. Urutan Manjat Hutan Berbasis Waktu & Sensor (Pindahan Macro N C++)
        print("[ARENA 2] Mengembangkan Kedua Pneumatik (HIGH) & Proteksi Deadwheel...")
        self.robot.set_pneumatics(front_state=True, back_state=True)
        self.robot.set_deadwheels(False) # Matikan deadwheel agar akumulasi odometri aman
        time.sleep(ActuatorConfig.DELAY_PNEU_SEC)

        print("[ARENA 2] Langkah 1: Dorong Maju Sasis Pertama (55cm)...")
        self.robot.move_relative(forward=0.55)
        if not self.robot.wait_until_idle(): return False

        print("[ARENA 2] Langkah 2: Menarik Naik Pneumatik DEPAN (LOW)...")
        self.robot.set_pneumatics(front_state=False, back_state=True)
        time.sleep(ActuatorConfig.DELAY_PNEU_SEC)

        print("[ARENA 2] Langkah 3: Dorong Maju Sasis Kedua (47cm)...")
        self.robot.move_relative(forward=0.47)
        if not self.robot.wait_until_idle(): return False

        print("[ARENA 2] Langkah 4: Menarik Naik Pneumatik BELAKANG (LOW)...")
        self.robot.set_pneumatics(front_state=False, back_state=False)
        time.sleep(ActuatorConfig.DELAY_PNEU_SEC)

        print("[ARENA 2] Langkah 5: Dorong Akhir Melewati Batas Keluar Hutan (17cm)...")
        self.robot.move_relative(forward=0.17)
        if not self.robot.wait_until_idle(): return False

        print("[FSM] >>> ARENA 2 SELESAI DENGAN SUKSES <<<")
        return True

    # ==========================================
    # STRATEGI ARENA 3: SCORING / DROP OBJEK
    # ==========================================
    def run_arena_3(self):
        print("\n" + "="*40)
        print("[FSM] >>> STRATEGI ARENA 3 DIMULAI <<<")
        print("="*40)
        self.robot.set_led(1, 255, 0, 255) # LED Ungu = Zona Pelepasan Poin

        # 1. Navigasi menuju titik tiang scoring akhir
        fwd, left = self.planner.get_arena_3_target()
        print(f"[ARENA 3] Navigasi ke Tiang Sasaran -> Fwd: {fwd}m")
        self.robot.move_relative(forward=fwd, left=left)
        if not self.robot.wait_until_idle(): return False

        # 2. Urutan Mekanis Pelepasan Objek (Scoring)
        print("[ARENA 3] Menurunkan Lengan untuk Meletakkan Objek...")
        self.robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
        time.sleep(ActuatorConfig.DELAY_ARM_SEC)

        print("[ARENA 3] Membuka Gripper...")
        self.robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
        time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

        print("[FSM] >>> ARENA 3 SELESAI DENGAN SUKSES <<<")
        return True

    # ==========================================
    # LOOP UTAMA PENGENDALI OTOMATIS (RUNNER)
    # ==========================================
    def start_full_auto(self):
        """Fungsi utama pembuka jalannya laga otonom tanpa intervensi keyboard."""
        print("\n=== SYSTEM STANDBY: MENUNGGU SINYAL TOMBOL START DI SASIS ===")
        input("Tekan [ENTER] pada laptop untuk mensimulasikan penekanan tombol START fisik...")
        
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

    def emergency_stop_handler(self, alasan_fail):
        """Menghentikan robot seketika jika terdeteksi kegagalan gerak di arena."""
        print(f"\n[FATAL ERROR] {alasan_fail}!")
        print("[RECOVERY] Mengirimkan sinyal rem darurat ke sasis bawah...")
        self.robot.e_stop()
        self.robot.set_led(2, 255, 0, 0) # LED Berkedip Merah tanda intervensi manual diperlukan

    def shutdown(self):
        """Mematikan thread serial background pendukung saat aplikasi di-close."""
        self.robot.close()
