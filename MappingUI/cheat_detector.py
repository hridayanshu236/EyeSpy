# cheat_detector.py (unchanged except minor guard)
import os
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

class CheatDetector:
    """
    Lightweight wrapper around a YOLOv8 model for detecting a single 'cheating' class (class 0).
    """

    def __init__(self, model_path="./weights/bestone.pt", device=None):
        self.model_path = model_path
        self.model = None
        self.device = device
        if YOLO is None:
            raise RuntimeError("ultralytics package not installed. Install ultralytics to use CheatDetector.")
        if os.path.isfile(self.model_path):
            self.load_model(self.model_path, device=device)

    def load_model(self, model_path=None, device=None):
        path = model_path or self.model_path
        self.model = YOLO(path)
        if device:
            try:
                self.model.to(device)
            except Exception:
                pass
        return self.model

    def detect_frame(self, frame_bgr, conf_thresh=0.3):
        """
        Run detection on a single frame (numpy BGR). Returns detections with class==0 and conf>=conf_thresh.
        """
        if self.model is None:
            self.load_model(self.model_path, device=self.device)

        results = self.model(frame_bgr)
        if not results or len(results) == 0:
            return []

        r = results[0]
        boxes = getattr(r, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return []

        data = boxes.data.cpu().numpy() if hasattr(boxes.data, "cpu") else np.array(boxes.data)
        if data.size == 0:
            return []

        keep_mask = (data[:, 5] == 0) & (data[:, 4] >= conf_thresh)
        kept = data[keep_mask]

        detections = []
        for row in kept:
            x1, y1, x2, y2, conf, cls = row
            detections.append({
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "conf": float(conf),
                "cls": int(cls)
            })
        return detections

    @staticmethod
    def draw_detections_on_image(frame_bgr, detections, box_color=(0,0,255), thickness=2):
        """
        Draw boxes + label on a copy of frame_bgr and return annotated image (BGR).
        """
        out = frame_bgr.copy()
        for det in detections:
            x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
            conf = det["conf"]
            label = f"Cheating {conf*100:.1f}%"
            cv2.rectangle(out, (x1, y1), (x2, y2), box_color, thickness)
            cv2.putText(out, label, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
        return out