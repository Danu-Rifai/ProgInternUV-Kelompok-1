import time
from config import (
    CLASS_MERAH, CLASS_HIJAU, CLASS_HITAM,
    FRAME_WIDTH, FRAME_HEIGHT,
    CENTER_LINE_X_RATIO,
    BLACK_BALL_RIGHT_THRESHOLD,
    CENTER_TOLERANCE,
    NO_OBJECT_FINISH_SECONDS
)


# State navigasi
STATE_STRAIGHT      = 'STRAIGHT'       # Kedua bola merah+hijau terlihat
STATE_AVOID_RIGHT   = 'AVOID_RIGHT'    # Hanya bola merah == belok kanan
STATE_AVOID_LEFT    = 'AVOID_LEFT'     # Hanya bola hijau == belok kiri
STATE_ORBIT_BLACK   = 'ORBIT_BLACK'    # Bola hitam terlihat == putar
STATE_FINISH        = 'FINISH'         # Tidak ada objek == selesai
STATE_IDLE          = 'IDLE'           # Awal sebelum mulai


class NavigationFSM:
    def __init__(self, controller):
        self.ctrl = controller
        self.state = STATE_IDLE
        self.no_object_timer = None   # timestamp saat objek pertama kali hilang
        self._prev_state = None

    # Update utama (dipanggil setiap frame)
    def update(self, detections, frame_w=FRAME_WIDTH, frame_h=FRAME_HEIGHT):
        # Ambil objek paling dekat per warna
        closest_red   = self._closest(detections, CLASS_MERAH)
        closest_green = self._closest(detections, CLASS_HIJAU)
        closest_black = self._closest(detections, CLASS_HITAM)

        has_red   = closest_red   is not None
        has_green = closest_green is not None
        has_black = closest_black is not None

        info = ""

        # PRIORITAS = Bola Hitam (manuver berputar)
        if has_black:
            self._transition(STATE_ORBIT_BLACK)
            info = self._handle_orbit_black(closest_black, frame_w)
            self.no_object_timer = None
            return self.state, info

        # Bola Merah + Hijau == Lurus
        if has_red and has_green:
            self._transition(STATE_STRAIGHT)
            self.ctrl.go_straight()
            info = "Lurus (merah + hijau terdeteksi)"
            self.no_object_timer = None
            return self.state, info

        # Hanya Merah == manuver Kanan
        if has_red and not has_green:
            self._transition(STATE_AVOID_RIGHT)
            self.ctrl.steer_right()
            info = f"Hindari merah == belok kanan (cy={closest_red['cy']})"
            self.no_object_timer = None
            return self.state, info

        # Hanya Hijau == Manucver Kiri
        if has_green and not has_red:
            self._transition(STATE_AVOID_LEFT)
            self.ctrl.steer_left()
            info = f"Hindari hijau == belok kiri (cy={closest_green['cy']})"
            self.no_object_timer = None
            return self.state, info

        # Tidak ada objek == countdown Finish
        now = time.time()
        if self.no_object_timer is None:
            self.no_object_timer = now

        elapsed = now - self.no_object_timer
        remaining = max(0.0, NO_OBJECT_FINISH_SECONDS - elapsed)
        info = f"Tidak ada objek — Finish dalam {remaining:.1f}s"

        if elapsed >= NO_OBJECT_FINISH_SECONDS:
            self._transition(STATE_FINISH)
            self.ctrl.stop()
            self.ctrl.disarm()
            return self.state, "FINISH — Kapal berhenti."

        # Sambil menunggu, tetap lurus
        self.ctrl.go_straight()
        return self.state, info

    # Manuver bola hitam
    def _handle_orbit_black(self, black_obj, frame_w):
        cx_black = black_obj['cx']
        ratio = cx_black / frame_w
        threshold = BLACK_BALL_RIGHT_THRESHOLD

        if ratio >= threshold:
            # Bola hitam sudah di kanan == putar kanan 
            self.ctrl.rotate_right()
            return f"ORBIT: bola hitam di kanan ({ratio:.2f}) == putar kanan"
        else:
            # Bola hitam ke kiri == putar lebih kencang ke kanan agar bola
            # kembali ke sisi kanan
            self.ctrl.rotate_right()
            return f"ORBIT: bola hitam di kiri ({ratio:.2f}) == koreksi kanan"

    # Helper
    def _closest(self, detections, label):
        # Objek dengan cy terbesar (paling bawah frame = paling dekat)
        filtered = [d for d in detections if d['label'] == label]
        if not filtered:
            return None
        return max(filtered, key=lambda d: d['cy'])

    def _transition(self, new_state):
        if new_state != self.state:
            print(f"[FSM] {self.state} == {new_state}")
            self._prev_state = self.state
            self.state = new_state

    @property
    def is_finished(self):
        return self.state == STATE_FINISH
