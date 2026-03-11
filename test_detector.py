import cv2
import time
import sys
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, CAMERA_FPS
from detector import ObjectDetector
from navigation import (
    STATE_STRAIGHT, STATE_AVOID_RIGHT, STATE_AVOID_LEFT,
    STATE_ORBIT_BLACK, STATE_FINISH, STATE_IDLE
)


class FakeController:
    #Fakecontroller
    def go_straight(self):    print("[FAKE] == LURUS")
    def steer_right(self):    print("[FAKE] == BELOK KANAN")
    def steer_left(self):     print("[FAKE] == BELOK KIRI")
    def rotate_right(self):   print("[FAKE] == PUTAR KANAN")
    def rotate_left(self):    print("[FAKE] == PUTAR KIRI")
    def stop(self):           print("[FAKE] == STOP")
    def disarm(self):         print("[FAKE] == DISARM")
    def release_rc(self):     pass


def main():
    print("[Test] Mode tes deteksi (tanpa MAVLink)")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    if not cap.isOpened():
        print("[Test] ERROR: Kamera tidak bisa dibuka.")
        sys.exit(1)

    detector = ObjectDetector()

    # Import NavigationFSM dgn fakecontroller
    from navigation import NavigationFSM
    fake_ctrl = FakeController()
    nav = NavigationFSM(fake_ctrl)

    print("[Test] Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        detections = detector.detect(frame)
        state, info = nav.update(detections, FRAME_WIDTH)

        frame_vis = detector.draw(frame.copy(), detections)

        # HUD
        overlay = frame_vis.copy()
        cv2.rectangle(overlay, (0, 0), (500, 70), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame_vis, 0.6, 0, frame_vis)
        cv2.putText(frame_vis, f"STATE: {state}", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 1)
        cv2.putText(frame_vis, info[:65], (8, 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)
        cv2.putText(frame_vis, f"Obj: {len(detections)}", (8, 66),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 0), 1)

        cv2.imshow("ASV - Test Detector", frame_vis)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[Test] Selesai.")


if __name__ == '__main__':
    main()