import time
from pymavlink import mavutil
from config import (
    MAVLINK_CONNECTION,
    THROTTLE_CHANNEL, STEERING_CHANNEL,
    BASE_THROTTLE, STOP_THROTTLE,
    STEER_CENTER, STEER_RIGHT, STEER_LEFT,
    STEER_HARD_RIGHT, STEER_HARD_LEFT
)

class MAVLinkController:
    def __init__(self):
        print(f"[MAVLink] Menghubungkan ke {MAVLINK_CONNECTION} ...")
        self.conn = mavutil.mavlink_connection(MAVLINK_CONNECTION)
        self.conn.wait_heartbeat()
        print(f"[MAVLink] Heartbeat diterima dari system {self.conn.target_system}, "
              f"component {self.conn.target_component}")
        self._arm()

    # ARM / DISARM
    def _arm(self):
        print("[MAVLink] Arming...")
        self.conn.arducopter_arm()
        self.conn.motors_armed_wait()
        print("[MAVLink] Armed.")

    def disarm(self):
        print("[MAVLink] Disarming...")
        self.conn.arducopter_disarm()
        self.conn.motors_disarmed_wait()
        print("[MAVLink] Disarmed.")

    # Set Mode
    def set_mode(self, mode_name='MANUAL'):
        mode_id = self.conn.mode_mapping().get(mode_name)
        if mode_id is None:
            print(f"[MAVLink] Mode '{mode_name}' tidak ditemukan.")
            return
        self.conn.set_mode(mode_id)
        print(f"[MAVLink] Mode diset ke {mode_name}")

    # RC Override — kirim perintah steering & throttle
    def send_rc(self, steering_pwm: int, throttle_pwm: int):
        """
        Kirim RC override ke kapal.
        steering_pwm : 1000-2000 us
        throttle_pwm : 1000-2000 us
        """
        # array 8 channel (nilai 0 = abaikan channel)
        channels = [0] * 8
        channels[STEERING_CHANNEL - 1] = int(steering_pwm)
        channels[THROTTLE_CHANNEL - 1] = int(throttle_pwm)

        self.conn.mav.rc_channels_override_send(
            self.conn.target_system,
            self.conn.target_component,
            *channels
        )

    # Perintah navigasi tingkat tinggi
    def go_straight(self):
        # Jalan lurus
        self.send_rc(STEER_CENTER, BASE_THROTTLE)

    def steer_right(self):
        # Belok kanan sedikit (hindari bola merah)
        self.send_rc(STEER_RIGHT, BASE_THROTTLE)

    def steer_left(self):
        # Belok kiri sedikit (hindari bola hijau)
        self.send_rc(STEER_LEFT, BASE_THROTTLE)

    def rotate_right(self):
        # Putar kanan keras (manuver bola hitam)
        self.send_rc(STEER_HARD_RIGHT, BASE_THROTTLE)

    def rotate_left(self):
        # Putar kiri keras
        self.send_rc(STEER_HARD_LEFT, BASE_THROTTLE)

    def stop(self):
        # Stop kapal
        self.send_rc(STEER_CENTER, STOP_THROTTLE)
        print("[MAVLink] Kapal berhenti.")

    def release_rc(self):
        """
        Lepas RC override — kembalikan kontrol ke autopilot/remote.
        Kirim nilai 0 di semua channel.
        """
        self.conn.mav.rc_channels_override_send(
            self.conn.target_system,
            self.conn.target_component,
            0, 0, 0, 0, 0, 0, 0, 0
        )
