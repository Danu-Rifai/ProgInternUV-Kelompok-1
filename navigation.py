import time
from config import (
    CLASS_MERAH, CLASS_HIJAU, CLASS_HITAM,
    FRAME_WIDTH, FRAME_HEIGHT,
    BLACK_BALL_RIGHT_THRESHOLD,
    NO_OBJECT_FINISH_SECONDS
)

# State navigasi
STATE_STRAIGHT    = 'STRAIGHT'
STATE_AVOID_RIGHT = 'AVOID_RIGHT'
STATE_AVOID_LEFT  = 'AVOID_LEFT'
STATE_ORBIT_BLACK = 'ORBIT_BLACK'
STATE_FINISH      = 'FINISH'
STATE_IDLE        = 'IDLE'


class NavigationFSM:
    def __init__(self, controller):
        self.ctrl            = controller
        self.state           = STATE_IDLE
        self.no_object_timer = None

    def update(self, detections, frame_w=FRAME_WIDTH, frame_h=FRAME_HEIGHT):
        closest_red   = self._closest(detections, CLASS_MERAH)
        closest_green = self._closest(detections, CLASS_HIJAU)
        closest_black = self._closest(detections, CLASS_HITAM)

        has_red   = closest_red   is not None
        has_green = closest_green is not None
        has_black = closest_black is not None

        info = ""

        # Kumpulkan cy semua objek terdekat per warna
        # cy terbesar = paling bawah di frame = paling dekat ke kapal
        candidates = {}
        if has_red:   candidates[CLASS_MERAH] = closest_red['cy']
        if has_green: candidates[CLASS_HIJAU] = closest_green['cy']
        if has_black: candidates[CLASS_HITAM] = closest_black['cy']

        # nearest_label = warna objek yang PALING DEKAT secara keseluruhan
        nearest_label = max(candidates, key=candidates.get) if candidates else None

        # ORBIT HITAM: hanya jika hitam adalah objek PALING DEKAT
        # Jika merah/hijau lebih dekat dari hitam, abaikan hitam
        if has_black and nearest_label == CLASS_HITAM:
            self._transition(STATE_ORBIT_BLACK)
            info = self._handle_orbit_black(closest_black, frame_w)
            self.no_object_timer = None
            return self.state, info

        # Merah + Hijau keduanya terdeteksi == Lurus
        if has_red and has_green:
            self._transition(STATE_STRAIGHT)
            self.ctrl.go_straight()
            info = f"Lurus — merah(cy={closest_red['cy']}) hijau(cy={closest_green['cy']})"
            self.no_object_timer = None
            return self.state, info

        # Hanya Merah == Belok Kanan
        if has_red and not has_green:
            self._transition(STATE_AVOID_RIGHT)
            self.ctrl.steer_right()
            info = f"Hindari merah == belok kanan (cy={closest_red['cy']})"
            self.no_object_timer = None
            return self.state, info

        # Hanya Hijau == Belok Kiri
        if has_green and not has_red:
            self._transition(STATE_AVOID_LEFT)
            self.ctrl.steer_left()
            info = f"Hindari hijau == belok kiri (cy={closest_green['cy']})"
            self.no_object_timer = None
            return self.state, info

        # Tidak ada objek == countdown FINISH
        now = time.time()
        if self.no_object_timer is None:
            self.no_object_timer = now

        elapsed   = now - self.no_object_timer
        remaining = max(0.0, NO_OBJECT_FINISH_SECONDS - elapsed)
        info = f"Tidak ada objek — FINISH dalam {remaining:.1f}s"

        if elapsed >= NO_OBJECT_FINISH_SECONDS:
            self._transition(STATE_FINISH)
            self.ctrl.stop()
            self.ctrl.disarm()
            return self.state, "FINISH — Kapal berhenti."

        # Sambil menunggu tetap lurus
        self.ctrl.go_straight()
        return self.state, info

    def _handle_orbit_black(self, black_obj, frame_w):
        ratio = black_obj['cx'] / frame_w
        self.ctrl.rotate_right()
        if ratio >= BLACK_BALL_RIGHT_THRESHOLD:
            return f"ORBIT: hitam di kanan ({ratio:.2f}) == putar kanan"
        else:
            return f"ORBIT: hitam ke kiri ({ratio:.2f}) == koreksi kanan"

    def _closest(self, detections, label):
        """Ambil objek dengan cy terbesar (paling bawah = paling dekat)."""
        filtered = [d for d in detections if d['label'] == label]
        if not filtered:
            return None
        return max(filtered, key=lambda d: d['cy'])

    def _transition(self, new_state):
        if new_state != self.state:
            print(f"[FSM] {self.state} == {new_state}")
            self.state = new_state

    @property
    def is_finished(self):
        return self.state == STATE_FINISH
