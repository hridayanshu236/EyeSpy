import os
import cv2
import torch
import torchvision.transforms as transforms
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QColor, QPainter, QImage

def draw_boxes(image, boxes, labels, color=(0, 0, 255), label_prefix="Cheating: "):
    image = image.copy()
    h, w = image.shape[:2]
    for box, label in zip(boxes, labels):
        x1, y1, x2, y2 = map(int, box)
        if x2 > x1 and y2 > y1 and 0 <= x1 < w and 0 <= x2 <= w and 0 <= y1 < h and 0 <= y2 <= h:
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, f"{label_prefix}{label}", (x1, max(0, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return image

class ObjectDetectionCNN(torch.nn.Module):
    def __init__(self, input_channels=3, num_predictions=2):
        super().__init__()
        def conv_block(in_channels, out_channels, num_convs, pool=True):
            layers = []
            for _ in range(num_convs):
                layers.append(torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1))
                layers.append(torch.nn.ReLU(inplace=True))
                in_channels = out_channels
            if pool:
                layers.append(torch.nn.MaxPool2d(kernel_size=2, stride=2))
            return torch.nn.Sequential(*layers)
        self.features = torch.nn.Sequential(
            conv_block(input_channels, 64, num_convs=2),
            conv_block(64, 128, num_convs=2),
            conv_block(128, 256, num_convs=4),
            conv_block(256, 512, num_convs=4),
            conv_block(512, 512, num_convs=4),
        )
        self.adapt_pool = torch.nn.AdaptiveAvgPool2d((7, 7))
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(512 * 7 * 7, 4096),
            torch.nn.ReLU(inplace=True),
            torch.nn.Linear(4096, 4096),
            torch.nn.ReLU(inplace=True),
            torch.nn.Linear(4096, num_predictions * 5)
        )
        self.num_predictions = num_predictions

    def forward(self, x):
        x = self.features(x)
        x = self.adapt_pool(x)
        x = self.classifier(x)
        x = x.view(x.shape[0], self.num_predictions, 5)
        return x

class CameraWidget(QWidget):
    def __init__(self, camera_name, parent=None):
        super().__init__(parent)
        self.camera_name = camera_name
        self.camera = None
        self.camera_id = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.setup_detection_model()
        self.violation_count = 0
        self.last_violation_time = 0
        self.violation_cooldown = 3000
        self.violation_log = []
        self.max_log_entries = 100
        self.save_dir = "violation_captures"
        os.makedirs(self.save_dir, exist_ok=True)
        self.setup_ui()

    def setup_detection_model(self):
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {self.device}")
            self.model = ObjectDetectionCNN(input_channels=3, num_predictions=2).to(self.device)
            model_path = "models/object_detection_model_20250612_152341.pth"
            if not os.path.exists(model_path):
                print(f"Model file not found: {model_path}")
                self.model_loaded = False
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
            self.confidence_threshold = 0.2
            self.model_loaded = True
            print("Cheating detection model initialized successfully")
        except Exception as e:
            self.model_loaded = False
            print(f"Error loading detection model: {str(e)}")

    def setup_ui(self):
        self.setMinimumHeight(480)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
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
        if not getattr(self, 'model_loaded', False):
            return frame, False, 0.0
        try:
            input_tensor = self.transform(frame)
            input_tensor = input_tensor.unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.model(input_tensor)[0]
            drawn_boxes = []
            box_labels = []
            any_cheating = False
            for pred in outputs:
                score = torch.sigmoid(pred[0]).item()
                x_min = int(round(pred[1].item()))
                y_min = int(round(pred[2].item()))
                x_max = int(round(pred[3].item()))
                y_max = int(round(pred[4].item()))
                print(f"Model score: {score:.4f} | Box: ({x_min}, {y_min}, {x_max}, {y_max})")
                if score < self.confidence_threshold:
                    # Flag cheating even if box is tiny
                    drawn_boxes.append([x_min, y_min, x_max, y_max])
                    box_labels.append(f"{score:.2f}")
                    any_cheating = True
            output_frame = draw_boxes(frame, drawn_boxes, box_labels)
            min_score = min([torch.sigmoid(pred[0]).item() for pred in outputs], default=1.0)
            return output_frame, any_cheating, min_score
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
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    print("Frame read failed or returned None.")
                    self.camera_feed.setPixmap(self.placeholder_pixmap.scaled(
                        640, 480, Qt.KeepAspectRatio
                    ))
                    return
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                processed_frame, is_cheating, score = self.detect_cheating(frame_rgb)
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