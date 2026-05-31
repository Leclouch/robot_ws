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
    SHOW_DEBUG_WINDOW = True
    
    # --- Toleransi Error Visual ---
    PIXEL_TOLERANCE_X = 15 # Robot berhenti koreksi visual jika error pixel di bawah angka ini
    PIXEL_TOLERANCE_Y = 15

    # --- Konfigurasi Spearhead YOLO --- "fist_gray","palm_gray"
    SPEARHEAD_MODEL_PATH = "vision/assets/best.pt"
    SPEARHEAD_CLASS_NAMES = ("grey spear",)
    SPEARHEAD_CONF_THRESHOLD = 0.2
    SPEARHEAD_IMGSZ = 960

    # Garis target di frame kamera. Vision hanya menyamakan X objek dengan garis ini.
    SPEARHEAD_TARGET_X_RATIO = 0.52
    # Y tetap disimpan untuk normalisasi tracking/debug, bukan syarat alignment.
    SPEARHEAD_TARGET_Y_RATIO = 0.85

    # Tracking multi-frame agar centroid tidak loncat-loncat.
    SPEARHEAD_BUFFER_SIZE = 5
    SPEARHEAD_GATE_THRESHOLD = 0.35
    SPEARHEAD_MAX_MISSED_FRAMES = 5

    # Vision hanya melakukan koreksi kiri-kanan. Nilai positif berarti geser kiri.
    SPEARHEAD_STRAFE_M_PER_NORM_ERROR = 0.30
    SPEARHEAD_MIN_STRAFE_M = 0.01
    SPEARHEAD_MAX_STRAFE_M = 0.10
    SPEARHEAD_STRAFE_SIGN = 1.0
    SPEARHEAD_ACTION_DELAY_SEC = 0.20
    SPEARHEAD_ALIGN_TIMEOUT_SEC = 20.0

    # Setelah target lock, FSM maju buta sejauh ini untuk masuk posisi ambil.
    SPEARHEAD_FINAL_APPROACH_M = 1.0
