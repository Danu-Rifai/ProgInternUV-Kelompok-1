import cv2
import time
import sys

from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, CAMERA_FPS
)
from detector import ObjectDetector
from mavlink_controller import MAVLinkController
from navigation import NavigationFSM


def main():
    # Inisialisasi Kamera
    print("[Main] Membuka kamera...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    if not cap.isOpened():
        print("[Main] ERROR: Kamera tidak dapat dibuka.")
        sys.exit(1)
    print("[Main] Kamera OK.")

    # Inisialisasi Komponen
    detector  = ObjectDetector()
    controller = MAVLinkController()
    nav       = NavigationFSM(controller)

    # Set mode MANUAL
    controller.set_mode('MANUAL')

    print("[Main] Sistem siap. Tekan 'q' untuk berhenti paksa.")
    print("[Main] Memulai loop navigasi...\n")

    fps_counter = 0
    fps_start   = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Main] Frame tidak terbaca, mencoba lagi...")
                time.sleep(0.05)
                continue

            # Deteksi Objek
            detections = detector.detect(frame)

            # Navigasi
            state, info = nav.update(detections, FRAME_WIDTH, FRAME_HEIGHT)

            # Visualisasi
            frame_vis = detector.draw(frame.copy(), detections)
            _draw_hud(frame_vis, state, info, fps_counter)

            cv2.imshow("ASV - Object Detection", frame_vis)

            # FPS hitung
            fps_counter += 1
            if time.time() - fps_start >= 1.0:
                fps_counter = 0
                fps_start   = time.time()

            # Cek Finish
            if nav.is_finished:
                print("[Main] FINISH tercapai. Program selesai.")
                break

            # Tombol keluar manual
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("[Main] User menekan 'q'. Berhenti...")
                controller.stop()
                controller.disarm()
                break

    except KeyboardInterrupt:
        print("\n[Main] Keyboard Interrupt. Menghentikan kapal...")
        controller.stop()
        controller.disarm()

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[Main] Program selesai.")


def _draw_hud(frame, state, info, fps):
    # informasi state
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (420, 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    state_color = {
        'STRAIGHT'    : (0, 255, 0),
        'AVOID_RIGHT' : (0, 165, 255),
        'AVOID_LEFT'  : (255, 165, 0),
        'ORBIT_BLACK' : (180, 0, 180),
        'FINISH'      : (0, 255, 255),
        'IDLE'        : (200, 200, 200),
    }.get(state, (255, 255, 255))

    cv2.putText(frame, f"STATE: {state}", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, state_color, 1)
    cv2.putText(frame, info[:60], (8, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)


if __name__ == '__main__':
    main()
