import time
from config import (
    CLASS_MERAH, CLASS_HIJAU, CLASS_HITAM,
    FRAME_WIDTH, FRAME_HEIGHT,
    NO_OBJECT_FINISH_SECONDS,
    ORBIT_MAJU_DURATION,
    ORBIT_KIRI_DURATION,
)

# ── State navigasi ───────────────────────────────────────────────────────────
STATE_STRAIGHT    = 'STRAIGHT'      # Normal: lurus
STATE_AVOID_RIGHT = 'AVOID_RIGHT'   # Normal: hindari merah
STATE_AVOID_LEFT  = 'AVOID_LEFT'    # Normal: hindari hijau
STATE_ORBIT_MAJU  = 'ORBIT_MAJU'    # Orbit step 1: maju lurus
STATE_ORBIT_KIRI  = 'ORBIT_KIRI'    # Orbit step 2: belok kiri
STATE_ORBIT_CW    = 'ORBIT_CW'      # Orbit step 3: putar clockwise terus
STATE_FINISH      = 'FINISH'
STATE_IDLE        = 'IDLE'

# Kumpulan state orbit — dipakai untuk cek "apakah sedang orbit?"
ORBIT_STATES = (STATE_ORBIT_MAJU, STATE_ORBIT_KIRI, STATE_ORBIT_CW)


class NavigationFSM:
    """
    Aturan sederhana:

    1. Ada merah/hijau          → FASE NORMAL (selalu menang)
    2. Lihat hitam pertama kali → MASUK ORBIT (3 step)
    3. Sudah di orbit           → TETAP ORBIT apapun yang terjadi
                                  (hitam hilang = tetap putar)
    4. Satu-satunya exit orbit  → lihat merah/hijau → kembali FASE NORMAL
    5. Tidak ada objek + tidak orbit → countdown FINISH
    """

    def __init__(self, controller):
        self.ctrl              = controller
        self.state             = STATE_IDLE
        self.no_object_timer   = None
        self._orbit_step_start = None

    # ────────────────────────────────────────────────────────────────────────
    def update(self, detections, frame_w=FRAME_WIDTH, frame_h=FRAME_HEIGHT):
        closest_red   = self._closest(detections, CLASS_MERAH)
        closest_green = self._closest(detections, CLASS_HIJAU)
        closest_black = self._closest(detections, CLASS_HITAM)

        has_red   = closest_red   is not None
        has_green = closest_green is not None
        has_black = closest_black is not None

        # ════════════════════════════════════════════════════════════════════
        # PRIORITAS 1 — MERAH/HIJAU terdeteksi
        # Satu-satunya pintu keluar dari orbit
        # ════════════════════════════════════════════════════════════════════
        if has_red or has_green:
            return self._fase_normal(closest_red, closest_green, has_red, has_green)

        # ════════════════════════════════════════════════════════════════════
        # PRIORITAS 2 — Sedang dalam orbit
        # Tetap jalankan orbit MESKIPUN hitam tidak terdeteksi
        # Hitam hilang dari frame = lanjut putar, tidak keluar orbit
        # ════════════════════════════════════════════════════════════════════
        if self.state in ORBIT_STATES:
            return self._fase_orbit()

        # ════════════════════════════════════════════════════════════════════
        # PRIORITAS 3 — Baru lihat hitam (belum pernah orbit sebelumnya)
        # Trigger masuk orbit
        # ════════════════════════════════════════════════════════════════════
        if has_black:
            return self._fase_orbit()

        # ════════════════════════════════════════════════════════════════════
        # PRIORITAS 4 — Tidak ada objek, tidak sedang orbit
        # Countdown FINISH
        # ════════════════════════════════════════════════════════════════════
        return self._fase_kosong()

    # ────────────────────────────────────────────────────────────────────────
    # FASE NORMAL
    # ────────────────────────────────────────────────────────────────────────
    def _fase_normal(self, closest_red, closest_green, has_red, has_green):
        # Keluar dari orbit → reset semua variabel orbit
        if self.state in ORBIT_STATES:
            print("[FSM] EXIT ORBIT → FASE NORMAL")
            self._orbit_step_start = None

        self.no_object_timer = None

        # jika ada merah sekaligus ada ijo → Lurus
        if has_red and has_green:
            self._transition(STATE_STRAIGHT)
            self.ctrl.go_straight()
            return self.state, (f"Lurus — merah(cy={closest_red['cy']}) "
                                f"hijau(cy={closest_green['cy']})")

        # Hanya Merah → Belok Kanan
        if has_red:
            self._transition(STATE_AVOID_RIGHT)
            self.ctrl.steer_right()
            return self.state, f"Hindari merah → belok kanan (cy={closest_red['cy']})"

        # Hanya Hijau → Belok Kiri
        if has_green:
            self._transition(STATE_AVOID_LEFT)
            self.ctrl.steer_left()
            return self.state, f"Hindari hijau → belok kiri (cy={closest_green['cy']})"

    # ────────────────────────────────────────────────────────────────────────
    # FASE ORBIT — 3 step berurutan, bertahan sampai exit
    # ────────────────────────────────────────────────────────────────────────
    def _fase_orbit(self):
        self.no_object_timer = None   # timer FINISH tidak jalan selama orbit
        now = time.time()

        # Baru masuk orbit (dari IDLE / STRAIGHT / AVOID_*)
        if self.state not in ORBIT_STATES:
            self._transition(STATE_ORBIT_MAJU)
            self._orbit_step_start = now
            print("[FSM] ORBIT dimulai — Step 1: maju lurus")

        # ── Step 1: ORBIT_MAJU ───────────────────────────────────────────
        if self.state == STATE_ORBIT_MAJU:
            elapsed   = now - self._orbit_step_start
            remaining = ORBIT_MAJU_DURATION - elapsed
            if remaining > 0:
                self.ctrl.go_straight()
                return self.state, f"ORBIT Step 1/3: maju — {remaining:.1f}s lagi"
            # Selesai → lanjut step 2
            self._transition(STATE_ORBIT_KIRI)
            self._orbit_step_start = now
            print("[FSM] ORBIT Step 2 — belok kiri")

        # ── Step 2: ORBIT_KIRI ───────────────────────────────────────────
        if self.state == STATE_ORBIT_KIRI:
            elapsed   = now - self._orbit_step_start
            remaining = ORBIT_KIRI_DURATION - elapsed
            if remaining > 0:
                self.ctrl.steer_left()
                return self.state, f"ORBIT Step 2/3: belok kiri — {remaining:.1f}s lagi"
            # Selesai → lanjut step 3
            self._transition(STATE_ORBIT_CW)
            self._orbit_step_start = now
            print("[FSM] ORBIT Step 3 — rotate clockwise (sampai lihat merah/hijau)")

        # ── Step 3: ORBIT_CW — putar terus, hitam boleh hilang ───────────
        elapsed = now - self._orbit_step_start
        self.ctrl.rotate_right()
        return self.state, f"ORBIT Step 3/3: CW {elapsed:.1f}s — menunggu merah/hijau..."

    # ────────────────────────────────────────────────────────────────────────
    # FASE KOSONG — tidak ada objek, tidak sedang orbit
    # ────────────────────────────────────────────────────────────────────────
    def _fase_kosong(self):
        now = time.time()
        if self.no_object_timer is None:
            self.no_object_timer = now

        elapsed   = now - self.no_object_timer
        remaining = max(0.0, NO_OBJECT_FINISH_SECONDS - elapsed)

        if elapsed >= NO_OBJECT_FINISH_SECONDS:
            self._transition(STATE_FINISH)
            self.ctrl.stop()
            self.ctrl.disarm()
            return self.state, "FINISH — Kapal berhenti."

        self.ctrl.go_straight()
        return self.state, f"Tidak ada objek — FINISH dalam {remaining:.1f}s"

    # ────────────────────────────────────────────────────────────────────────
    # Helper
    # ────────────────────────────────────────────────────────────────────────
    def _closest(self, detections, label):
        filtered = [d for d in detections if d['label'] == label]
        if not filtered:
            return None
        return max(filtered, key=lambda d: d['cy'])

    def _transition(self, new_state):
        if new_state != self.state:
            print(f"[FSM] {self.state} → {new_state}")
            self.state = new_state

    @property
    def is_finished(self):
        return self.state == STATE_FINISH