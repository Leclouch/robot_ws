# ==========================================
# FILE: config.py
# ==========================================

class SerialConfig:
    # --- Konfigurasi Komunikasi ---
    PORT = '/dev/ttyACM0'  # Ganti ke 'COM3' atau menyesuaikan jika pakai Windows
    BAUDRATE = 115200
    TIMEOUT = 0.1          

class HardwareConfig:
    # --- Konfigurasi Channel Motor Driver (Via PCA9685 0x40) ---
    # Jika ada driver atau pin yang terbakar, cukup ubah angkanya di sini.
    M1A = 12  # Depan Kiri
    M1B = 13
    M2A = 7   # Depan Kanan
    M2B = 6
    M3A = 14  # Belakang Kanan
    M3B = 11
    M4A = 5   # Belakang Kiri
    M4B = 8

class KinematicConfig:
    # --- Tuning Kecepatan Trapesium ---
    SPEED_MAX_FWD = 85.0   # Batas kecepatan Maju/Mundur
    SPEED_MAX_STRF = 85.0  # Batas kecepatan Kanan/Kiri (Strafe)
    SPEED_MAX_TURN = 50.0  # Batas kecepatan Rotasi
    
    # --- Toleransi Navigasi (Untuk fungsi wait_until_idle) ---
    DIST_TOLERANCE = 0.02  # Jarak aman sasis dianggap sudah sampai target (meter)
    ANGLE_TOLERANCE = 2.0  # Toleransi kemiringan sudut hadap (derajat)
    IDLE_TIMEOUT = 15.0    # Batas waktu maksimal tunggu target sebelum dianggap nyangkut (detik)
    SETTLE_TIME = 0.4      # Waktu jeda agar sasis stabil/tidak goyang setelah rem mekanik (detik)

class ActuatorConfig:
    # --- Konfigurasi Channel Servo (Via PCA9685 0x60) ---
    PIN_GRIP = 0
    PIN_ARM_SPEAR = 1
    
    # --- Konfigurasi Sudut Gerak Servo ---
    GRIP_OPEN = 120
    GRIP_CLOSE = 30
    ARM_UP = 48         
    ARM_DOWN = 135      
    
    # --- Waktu Mekanik (Jeda Gerak Aman) ---
    # Python akan otomatis menunggu durasi ini agar mekanik tereksekusi sempurna
    DELAY_ARM_SEC = 0.6    # Estimasi lengan turun/naik sempurna
    DELAY_GRIP_SEC = 0.5   # Estimasi capit mengunci kuat
    DELAY_PNEU_SEC = 0.4   # Waktu aktuasi tabung pneumatik memompa/membuang udara

class VisionConfig:
    # --- Konfigurasi Sensor Kamera / OpenCV ---
    CAMERA_INDEX = 0       # 0 untuk webcam bawaan / port USB pertama
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    TARGET_FPS = 30
    
    # --- Toleransi Error Visual ---
    PIXEL_TOLERANCE_X = 15 # Robot berhenti koreksi visual jika error pixel di bawah angka ini
    PIXEL_TOLERANCE_Y = 15