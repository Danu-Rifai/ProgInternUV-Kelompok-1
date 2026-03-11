import cv2
import numpy as np
from ultralytics import YOLO
from config import (
    MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD,
    CLASS_NAMES, CLASS_MERAH, CLASS_HIJAU, CLASS_HITAM,
    FRAME_WIDTH, FRAME_HEIGHT,
    CENTER_LINE_X_RATIO, CENTER_LINE_COLOR, CENTER_LINE_THICKNESS
)


class ObjectDetector:
    def __init__(self):
        print("[Detector] Loading model YOLOv5 via ultralytics...")
        self.model = YOLO(MODEL_PATH)
        self.conf  = CONFIDENCE_THRESHOLD
        self.iou   = IOU_THRESHOLD
        print("[Detector] Model berhasil dimuat.")

    def detect(self, frame):
        results = self.model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            verbose=False   # matikan log per frame
        )

        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label  = CLASS_NAMES.get(cls_id, f'class_{cls_id}')
                conf   = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                detections.append({
                    'label': label,
                    'conf':  conf,
                    'x1': x1, 'y1': y1,
                    'x2': x2, 'y2': y2,
                    'cx': cx,  'cy': cy,
                })

        return detections

    def get_closest_by_label(self, detections, label):
        filtered = [d for d in detections if d['label'] == label]
        if not filtered:
            return None
        return max(filtered, key=lambda d: d['cy'])

    def draw(self, frame, detections):
        # Bounding box dan garis segmentasi tengah pada frame
        h, w = frame.shape[:2]

        # Garis tengah vertikal
        cx_line = int(w * CENTER_LINE_X_RATIO)
        cv2.line(frame, (cx_line, 0), (cx_line, h),
                 CENTER_LINE_COLOR, CENTER_LINE_THICKNESS)

        # Label KIRI dan KANAN
        cv2.putText(frame, "KIRI", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        cv2.putText(frame, "KANAN", (cx_line + 5, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Bounding Box per deteksi
        color_map = {
            CLASS_MERAH: (0, 0, 255),
            CLASS_HIJAU: (0, 255, 0),
            CLASS_HITAM: (50, 50, 50),
        }

        for d in detections:
            color = color_map.get(d['label'], (255, 255, 0))
            cv2.rectangle(frame, (d['x1'], d['y1']), (d['x2'], d['y2']),
                          color, 2)
            label_text = f"{d['label']} {d['conf']:.2f}"
            cv2.putText(frame, label_text,
                        (d['x1'], d['y1'] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            # Titik tengah
            cv2.circle(frame, (d['cx'], d['cy']), 4, color, -1)

        return frame