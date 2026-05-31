# ==========================================
# FILE: core/fsm_master.py
# ==========================================
import time
from hardware.serial_interface import RobotController
from core.path_planner import PathPlanner
from config import ActuatorConfig
from vision.visual_servoing import SpearheadVisualServo

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
        print("\n" + "="*40)
        print("[FSM] >>> STRATEGI ARENA 1 DIMULAI <<<")
        print("="*40)
        self.robot.set_led(1, 0, 255, 0) # LED Hijau 

        # 1. Visual Servoing (Koreksi Kanan/Kiri Pas)
        print("[ARENA 1] Mengaktifkan Visual Servoing...")
        self.robot.set_led(3, 255, 255, 0) # Bernapas Kuning
        vision = SpearheadVisualServo()
        
        # Fungsi align() ini membaca kamera dan menggerakkan sasis kanan/kiri
        # sampai centroid target sejajar dengan garis target vertikal.
        if not vision.align(self.robot):
            return False
        print("[ARENA 1] Target Terkunci Presisi!")

        # 2. Gerakan Sequence Makro Ambil
        print("[ARENA 1] Menurunkan Arm...")
        self.robot.set_led(1, 0, 0, 255) # Biru
        self.robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_DOWN)
        time.sleep(ActuatorConfig.DELAY_ARM_SEC)

        print("[ARENA 1] Mundur 0.85m...")
        self.robot.move_relative(forward=-0.85)
        if not self.robot.wait_until_idle(): return False

        print("[ARENA 1] Menutup Gripper...")
        self.robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_CLOSE)
        time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

        print("[ARENA 1] Mengangkat Arm...")
        self.robot.set_servo(ActuatorConfig.PIN_ARM_SPEAR, ActuatorConfig.ARM_UP)
        time.sleep(ActuatorConfig.DELAY_ARM_SEC)

        print("[ARENA 1] Maju 0.5m...")
        self.robot.move_relative(forward=0.50)
        if not self.robot.wait_until_idle(): return False

        print("[ARENA 1] Rotate 180 Derajat...")
        self.robot.move_relative(turn_deg=180.0)
        if not self.robot.wait_until_idle(): return False

        # 3. Logika Deteksi AprilTag
        print("[ARENA 1] Mencari AprilTag...")
        apriltag_detected = False
        
        # Loop sampai AprilTag terlihat
        while not apriltag_detected:
            apriltag_detected, tag_id = vision.detect_apriltag()
            
            if not self.is_running: return False # Proteksi jika E-Stop ditekan
            time.sleep(0.1)

        print("[ARENA 1] AprilTag Terlihat! Membuka Gripper...")
        self.robot.set_servo(ActuatorConfig.PIN_GRIP, ActuatorConfig.GRIP_OPEN)
        time.sleep(ActuatorConfig.DELAY_GRIP_SEC)

        print("[ARENA 1] Menunggu AprilTag menghilang dari pantauan kamera...")
        # Loop menahan FSM sampai AprilTag hilang (diambil/tertutup)
        while apriltag_detected:
            apriltag_detected, tag_id = vision.detect_apriltag()
            
            if not self.is_running: return False 
            time.sleep(0.1)

        print("[ARENA 1] AprilTag menghilang. Lanjut pindah state ke R2!")
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
        """Menjalankan ulang arena tertentu dari dashboard."""
        self.is_running = True
        if arena_id == 1:
            self.current_arena = "RETRY_ARENA_1"
            if not self.run_arena_1():
                self.emergency_stop_handler("Retry Arena 1 gagal")
        elif arena_id == 2:
            self.current_arena = "RETRY_ARENA_2"
            if not self.run_arena_2():
                self.emergency_stop_handler("Retry Arena 2 gagal")
        elif arena_id == 3:
            self.current_arena = "RETRY_ARENA_3"
            if not self.run_arena_3():
                self.emergency_stop_handler("Retry Arena 3 gagal")
        else:
            print(f"[WARNING] Arena retry tidak dikenal: {arena_id}")

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
