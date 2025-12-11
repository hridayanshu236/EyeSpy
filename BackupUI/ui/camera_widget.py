import os
import glob
import cv2
import torch
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QColor, QPainter, QImage
import torchvision.transforms as transforms

from models import (
    ObjectDetectionCNN,
    ObjectDetectionResNet,
    ObjectDetectionDenseNet121,
    ObjectDetectionMobileNetV2
)

def draw_boxes(image, boxes, labels, color=(0, 0, 255), label_prefix=""):
    image = image.copy()
    h, w = image.shape[:2]
    for box, label in zip(boxes, labels):
        x1, y1, x2, y2 = map(int, box)
        if x2 > x1 and y2 > y1 and 0 <= x1 < w and 0 <= x2 <= w and 0 <= y1 < h and 0 <= y2 <= h:
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, f"{label_prefix}{label}", (x1, max(0, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return image

class CameraWidget(QWidget):
    def __init__(self, camera_name, model_type="cnn", parent=None):
        super().__init__(parent)
        self.camera_name = camera_name
        self.camera = None
        self.camera_id = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.model_type = model_type  # "cnn", "resnet", "densenet", "mobilenet"
        self.violation_count = 0
        self.last_violation_time = 0
        self.violation_cooldown = 3000
        self.violation_log = []
        self.max_log_entries = 100
        self.save_dir = "violation_captures"
        os.makedirs(self.save_dir, exist_ok=True)
        self.confidence_threshold = 0.5

        self.frame_skip = 2
        self._frame_counter = 0
        cv2.setNumThreads(1)
        torch.set_num_threads(1)

        self.setup_ui()
        self.setup_detection_model()

    def setup_ui(self):
        self.setMinimumHeight(480)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)
        self.model_selector = QComboBox()
        self.model_selector.addItems(["cnn", "resnet", "densenet", "mobilenet"])
        self.model_selector.setCurrentText(self.model_type)
        self.model_selector.currentTextChanged.connect(self.on_model_type_changed)
        top_layout.addWidget(QLabel("Model:"))
        top_layout.addWidget(self.model_selector)
        self.reload_btn = QPushButton("Reload Model")
        self.reload_btn.clicked.connect(self.setup_detection_model)
        top_layout.addWidget(self.reload_btn)
        self.main_layout.addWidget(top_bar)

        self.camera_feed = QLabel()
        self.camera_feed.setAlignment(Qt.AlignCenter)
        self.camera_feed.setStyleSheet("background-color: #191919; border-radius: 4px;")
        self.camera_feed.setMinimumHeight(360)
        self.placeholder_pixmap = QPixmap(640, 480)
        self.placeholder_pixmap.fill(QColor("#191919"))
        painter = QPainter(self.placeholder_pixmap)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.placeholder_pixmap.rect(), Qt.AlignCenter, f"Camera Feed\n{self.camera_name}\n(Click Start Camera to begin)")
        painter.end()
        self.camera_feed.setPixmap(self.placeholder_pixmap.scaled(
            640, 480, Qt.KeepAspectRatio
        ))
        self.main_layout.addWidget(self.camera_feed)
        self.info_bar = QWidget()
        self.info_layout = QHBoxLayout(self.info_bar)
        self.info_layout.setContentsMargins(5, 5, 5, 5)
        self.name_label = QLabel(self.camera_name)
        self.name_label.setStyleSheet("font-weight: bold;")
        self.info_layout.addWidget(self.name_label)
        self.info_layout.addStretch()
        self.status_indicator = QLabel("Status: Not Running")
        self.info_layout.addWidget(self.status_indicator)
        self.violation_indicator = QLabel("🟢")
        self.info_layout.addWidget(self.violation_indicator)
        self.main_layout.addWidget(self.info_bar)
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)

    def on_model_type_changed(self, new_type):
        self.model_type = new_type
        self.setup_detection_model()

    def setup_detection_model(self):
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {self.device}")
            if self.model_type == "cnn":
                self.model = ObjectDetectionCNN(input_channels=3, num_predictions=2).to(self.device)
                model_path = "models/CNN37.pth"
            elif self.model_type == "resnet":
                self.model = ObjectDetectionResNet(num_predictions=2).to(self.device)
                resnet_files = glob.glob("models/ResNet*.pth")
                if resnet_files:
                    model_path = resnet_files[0]
                else:
                    print("No ResNet model file found in models/.")
                    self.model_loaded = False
                    self.status_indicator.setText("Status: No ResNet model file found")
                    return
            elif self.model_type == "densenet":
                self.model = ObjectDetectionDenseNet121(num_predictions=2).to(self.device)
                densenet_files = glob.glob("models/DenseNet*.pth")
                if densenet_files:
                    model_path = densenet_files[0]
                else:
                    print("No DenseNet model file found in models/.")
                    self.model_loaded = False
                    self.status_indicator.setText("Status: No DenseNet model file found")
                    return
            elif self.model_type == "mobilenet":
                self.model = ObjectDetectionMobileNetV2(num_predictions=2).to(self.device)
                mobilenet_files = glob.glob("models/MobileNet*.pth")
                if mobilenet_files:
                    model_path = mobilenet_files[0]
                else:
                    print("No MobileNet model file found in models/.")
                    self.model_loaded = False
                    self.status_indicator.setText("Status: No MobileNet model file found")
                    return
            else:
                print(f"Unknown model type: {self.model_type}")
                self.model_loaded = False
                self.status_indicator.setText("Status: Unknown model type")
                return

            if not os.path.exists(model_path):
                print(f"Model file not found: {model_path}")
                self.model_loaded = False
                self.status_indicator.setText("Status: Model file not found")
                return
            checkpoint = torch.load(model_path, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            self.model.eval()
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((320, 320)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            self.model_loaded = True
            self.status_indicator.setText(f"Status: Model '{self.model_type}' loaded")
            print(f"{self.model_type} model initialized successfully")
        except Exception as e:
            self.model_loaded = False
            self.status_indicator.setText(f"Status: Model Load Error")
            print(f"Error loading detection model: {str(e)}")

    def start_camera(self):
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            if not self.camera.isOpened():
                self.status_indicator.setText("Status: Failed to open camera")
                print("Failed to open camera.")
                return
            self.timer.start(30)
            self.status_indicator.setText("Status: Running")
        except Exception as e:
            self.status_indicator.setText(f"Status: Error - {str(e)}")
            print(f"Error starting camera: {str(e)}")

    def stop_camera(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.camera and self.camera.isOpened():
            self.camera.release()
            self.camera = None
        self.status_indicator.setText("Status: Stopped")
        self.camera_feed.setPixmap(self.placeholder_pixmap.scaled(
            640, 480, Qt.KeepAspectRatio
        ))

    def detect_cheating(self, frame):
        """
        Detects cheating in a frame using the object detection model.
        Uses only the first box's objectness as in your evaluation.
        1 = not cheating, 0 = cheating.
        Returns: (output_frame, is_cheating, pred_objectness)
        Only draws box and writes "Cheat" if cheating is detected.
        """
        if not getattr(self, 'model_loaded', False):
            return frame, False, 0.0
        try:
            input_tensor = self.transform(frame)
            input_tensor = input_tensor.unsqueeze(0).to(self.device)
            with torch.inference_mode():
                outputs = self.model(input_tensor)[0]  # Shape: [2, 5]
            pred_objectness = torch.sigmoid(outputs[0, 0]).item()
            pred_class = 1 if pred_objectness > self.confidence_threshold else 0
            is_cheating = (pred_class == 0)

            drawn_boxes = []
            box_labels = []
            if is_cheating:
                x_min = int(round(outputs[0, 1].item()))
                y_min = int(round(outputs[0, 2].item()))
                x_max = int(round(outputs[0, 3].item()))
                y_max = int(round(outputs[0, 4].item()))
                drawn_boxes.append([x_min, y_min, x_max, y_max])
                box_labels.append("Cheat")

            output_frame = draw_boxes(frame, drawn_boxes, box_labels)
            return output_frame, is_cheating, pred_objectness
        except Exception as e:
            print(f"Error in cheating detection: {str(e)}")
            import traceback
            traceback.print_exc()
            return frame, False, 0.0

    def log_violation(self, score, frame):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
        violation_type = "Cheating"
        filename = f"{violation_type}_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        try:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filepath, frame_bgr)
        except Exception as e:
            print(f"Error saving violation image: {str(e)}")
        log_entry = {
            "time": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "room": "Exam Room",
            "camera": self.camera_name,
            "type": "Cheating",
            "score": score,
            "action": "Flagged",
            "image_path": filepath
        }
        self.violation_log.append(log_entry)
        if len(self.violation_log) > self.max_log_entries:
            self.violation_log.pop(0)
        print(f"Violation logged: {log_entry}")

    def update_frame(self):
        try:
            if self.camera and self.camera.isOpened():
                self._frame_counter = (self._frame_counter + 1) % self.frame_skip
                if self._frame_counter != 0:
                    return

                ret, frame = self.camera.read()
                if not ret or frame is None:
                    print("Frame read failed or returned None.")
                    self.camera_feed.setPixmap(self.placeholder_pixmap.scaled(
                        640, 480, Qt.KeepAspectRatio
                    ))
                    return
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (320, 320))
                processed_frame, is_cheating, score = self.detect_cheating(frame_resized)
                processed_frame = cv2.resize(processed_frame, (frame.shape[1], frame.shape[0]))

                current_time = time.time() * 1000
                if is_cheating and (current_time - self.last_violation_time > self.violation_cooldown):
                    self.show_violation()
                    self.log_violation(score, processed_frame)
                    self.last_violation_time = current_time
                    self.violation_count += 1
                h, w, ch = processed_frame.shape
                try:
                    img = QImage(processed_frame.data, w, h, ch * w, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(img)
                    self.camera_feed.setPixmap(pixmap.scaled(
                        self.camera_feed.width(),
                        self.camera_feed.height(),
                        Qt.KeepAspectRatio
                    ))
                except Exception as e:
                    print("Failed to create QImage/QPixmap:", e)
            else:
                print("Camera not initialized or not open.")
        except Exception as e:
            print(f"Error in update_frame: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_violation(self):
        self.violation_indicator.setText("🔴")
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 2px solid #ff3333;
                border-radius: 4px;
            }
        """)
        QTimer.singleShot(3000, self.reset_violation)

    def reset_violation(self):
        self.violation_indicator.setText("🟢")
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)

    def get_violation_logs(self):
        return self.violation_log