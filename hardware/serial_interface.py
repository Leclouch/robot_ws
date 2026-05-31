# ==========================================
# FILE: hardware/serial_interface.py
# ==========================================
import serial
import time
import math
import threading
import re
from config import SerialConfig, HardwareConfig, KinematicConfig

class RobotController:
    def __init__(self):
        self.ser = None
        self.is_connected = False

        # State Odometri Aktual (Ter-update otomatis dari Teensy)
        self.odom_x = 0.0  
        self.odom_y = 0.0  
        self.odom_theta_deg = 0.0 

        # State Target (Digunakan oleh wait_until_idle)
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_theta_deg = 0.0

        # Memulai Thread Background untuk membaca serial tanpa membuat GUI/FSM macet
        self.running = True
        self.worker_thread = threading.Thread(target=self._serial_worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _serial_worker_loop(self):
        """Thread background tunggal untuk membaca data dan proteksi auto-reconnect."""
        # Regex disesuaikan dengan format "ACC -> FWD: 0.00 STRF: 0.00 T: 0.00"
        pos_pattern = re.compile(r"ACC -> FWD:\s*([-\d.]+)\s*STRF:\s*([-\d.]+)\s*T:\s*([-\d.]+)")
        
        while self.running:
            if not self.is_connected:
                self._attempt_connection()
                time.sleep(1.0) # Jeda agar tidak spamming koneksi
                continue
            
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    match = pos_pattern.search(line)
                    if match:
                        self.odom_x = float(match.group(1))
                        self.odom_y = float(match.group(2))
                        self.odom_theta_deg = float(match.group(3))
                    else:
                        # Print pesan dari Teensy yang bukan data odometri (contoh: log debug)
                        if line and not line.startswith("ACC ->"):
                            print(f"[TEENSY]: {line}")
            except (serial.SerialException, OSError):
                print("\n[WARNING] Koneksi serial terputus tiba-tiba! (Kabel lepas / Power drop)")
                self._handle_disconnect()
                
            time.sleep(0.01) # Mencegah CPU usage 100%

    def _attempt_connection(self):
        """Mencoba membuka port serial dan mengirim ulang konfigurasi hardware."""
        print(f"[RECONNECT] Mencoba menghubungkan ke {SerialConfig.PORT}...")
        try:
            self.ser = serial.Serial(
                port=SerialConfig.PORT, 
                baudrate=SerialConfig.BAUDRATE, 
                timeout=SerialConfig.TIMEOUT
            )
            print(f"[SUCCESS] Terhubung dengan {SerialConfig.PORT}! Tunggu bootloader Teensy...")
            time.sleep(2.0) # Wajib jeda 2 detik agar Teensy siap menerima command
            
            self._send_hardware_config() # Tembak config setelah konek
            self.is_connected = True
        except (serial.SerialException, OSError):
            pass # Gagal konek, akan dicoba lagi di iterasi loop selanjutnya

    def _handle_disconnect(self):
        """Menutup port dengan aman jika terdeteksi diskoneksi."""
        self.is_connected = False
        if self.ser:
            try: 
                self.ser.close()
            except Exception: 
                pass
            self.ser = None

    def _send_hardware_config(self):
        """Mengirim parameter Pin Motor dan Speed Limit dari config.py ke Teensy."""
        # Command 'K': Susunan Pin Motor
        pin_cmd = f"K {HardwareConfig.M1A} {HardwareConfig.M1B} {HardwareConfig.M2A} {HardwareConfig.M2B} {HardwareConfig.M3A} {HardwareConfig.M3B} {HardwareConfig.M4A} {HardwareConfig.M4B}"
        self._write_raw(pin_cmd)
        
        # Command 'X': Batas Kecepatan Maksimum
        speed_cmd = f"X {KinematicConfig.SPEED_MAX_FWD} {KinematicConfig.SPEED_MAX_STRF} {KinematicConfig.SPEED_MAX_TURN}"
        self._write_raw(speed_cmd)
        print("[INFO] Parameter Konfigurasi Hardware berhasil disinkronisasi ke Teensy.")

    def _write_raw(self, string_data):
        """Fungsi internal untuk menulis instruksi ke kabel serial."""
        if self.ser and self.is_connected:
            try:
                self.ser.write((string_data + "\n").encode('utf-8'))
                return True
            except (serial.SerialException, OSError):
                self.is_connected = False
        return False

    def send_cmd(self, cmd_str):
        """Fungsi pembungkus aman untuk mengirim command dari modul luar (FSM)."""
        if not self.is_connected:
            print(f"[WARNING] Perintah '{cmd_str}' diabaikan karena koneksi serial terputus!")
            return False
        return self._write_raw(cmd_str)

    # ==========================================
    # PRIMITIF AKTUATOR & FEEDBACK
    # ==========================================
    def set_servo(self, pin, angle): 
        self.send_cmd(f"V {pin} {angle}")
        
    def set_pneumatics(self, front, back): 
        self.send_cmd(f"P {1 if front else 0} {1 if back else 0}")
        
    def set_deadwheels(self, state): 
        self.send_cmd(f"W {1 if state else 0}")
        
    def set_led(self, mode, r=0, g=0, b=0): 
        self.send_cmd(f"L {mode} {r} {g} {b}")
        
    def trigger_buzzer(self, duration): 
        self.send_cmd(f"B {duration}")
        
    def e_stop(self): 
        self.send_cmd("S")
        
    def zero_odom(self): 
        self.send_cmd("Z")
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_theta_deg = 0.0

    # ==========================================
    # PRIMITIF KINEMATIK GERAK
    # ==========================================
    def move_relative(self, forward=0.0, left=0.0, turn_deg=0.0):
        """
        Mengirim delta koordinat relatif ke Teensy.
        Catatan: Kinematika Arduino menganggap nilai 'strafe' positif adalah geser Kanan.
        """
        strafe_arduino = -left  
        
        # Simpan target akumulatif secara lokal untuk pantauan fungsi idle
        self.target_x = self.odom_x + forward
        self.target_y = self.odom_y + strafe_arduino
        self.target_theta_deg = self.odom_theta_deg + turn_deg
        
        # Eksekusi command 'G'
        self.send_cmd(f"G {forward:.3f} {strafe_arduino:.3f} {turn_deg:.2f}")

    def wait_until_idle(self, dist_tol=None, angle_tol=None, timeout=None):
        """
        Memblokir alur FSM sampai sasis mengonfirmasi telah mencapai titik target koordinat.
        Jika kabel putus di tengah jalan, fungsi ini akan langsung menggagalkan instruksi.
        """
        # Gunakan nilai default dari config jika tidak ada parameter khusus yang di-passing
        d_tol = dist_tol if dist_tol is not None else KinematicConfig.DIST_TOLERANCE
        a_tol = angle_tol if angle_tol is not None else KinematicConfig.ANGLE_TOLERANCE
        t_out = timeout if timeout is not None else KinematicConfig.IDLE_TIMEOUT

        start_time = time.time()
        while time.time() - start_time < t_out:
            if not self.is_connected:
                print("[WARNING] Deteksi putus koneksi saat bergerak! Pembatalan antrean gerakan.")
                return False 
            
            d_err = math.hypot(self.target_x - self.odom_x, self.target_y - self.odom_y)
            a_err = abs((self.target_theta_deg - self.odom_theta_deg + 180) % 360 - 180)