# Koneksi MAVLink
MAVLINK_CONNECTION = 'udp:127.0.0.1:14550'
# MAVLINK_CONNECTION = 'COMX'

# Kamera
CAMERA_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_FPS = 30

# Model YOLOv5
MODEL_PATH = 'best.pt'
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# Label Class
CLASS_NAMES = {
    0: 'hijau',   # bola_hijau
    1: 'hitam',   # bola_hitam
    2: 'merah',   # bola_merah
}
CLASS_MERAH = 'merah'
CLASS_HIJAU = 'hijau'
CLASS_HITAM = 'hitam'

# Frame Segmentation
CENTER_LINE_X_RATIO = 0.5
CENTER_LINE_COLOR = (200, 200, 200)
CENTER_LINE_THICKNESS = 1

# Zona deteksi "paling dekat" = objek dengan koordinat Y paling bawah di frame
# (Y besar = bawah frame = lebih dekat ke kapal)

# Parameter Navigasi
# Throttle dasar kapal (0-100)
BASE_THROTTLE = 1550       # PWM microseconds (1500 = netral, 1900 = maju penuh)
STOP_THROTTLE = 1500       # PWM netral / berhenti

# Steering (kanal rudder/servo)
STEER_CENTER = 1500        # PWM tengah (lurus)
STEER_RIGHT = 1600         # PWM belok kanan sedikit
STEER_LEFT = 1400          # PWM belok kiri sedikit
STEER_HARD_RIGHT = 1700    # PWM putar kanan (manuver bola hitam)
STEER_HARD_LEFT = 1300     # PWM putar kiri

# Channel MAVLink
THROTTLE_CHANNEL = 3       # Channel throttle
STEERING_CHANNEL = 1       # Channel steering/rudder

# Logic Navigasi
BLACK_BALL_RIGHT_THRESHOLD = 0.55   # 55% dari lebar frame ke kanan

# Toleransi tengah untuk bola merah+hijau 
CENTER_TOLERANCE = 50

# Finish Detection
NO_OBJECT_FINISH_SECONDS = 5.0