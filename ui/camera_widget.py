from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor, QPainter, QImage
import cv2
import numpy as np

class CameraWidget(QWidget):
    def __init__(self, camera_name, parent=None):
        super().__init__(parent)
        self.camera_name = camera_name
        
        # Camera properties
        self.camera = None
        self.camera_id = 0  # Default camera (usually laptop webcam)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Set size policy
        self.setMinimumHeight(480)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Camera feed
        self.camera_feed = QLabel()
        self.camera_feed.setAlignment(Qt.AlignCenter)
        self.camera_feed.setStyleSheet("background-color: #191919; border-radius: 4px;")
        self.camera_feed.setMinimumHeight(360)
        
        # Create a placeholder pixmap (in real app, this would be video feed)
        self.placeholder_pixmap = QPixmap(640, 480)
        self.placeholder_pixmap.fill(QColor("#191919"))
        
        # Add some text to the pixmap
        painter = QPainter(self.placeholder_pixmap)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.placeholder_pixmap.rect(), Qt.AlignCenter, f"Camera Feed\n{self.camera_name}\n(Click Start Camera to begin)")
        painter.end()
        
        # Set the placeholder
        self.camera_feed.setPixmap(self.placeholder_pixmap.scaled(
            640, 480, Qt.KeepAspectRatio
        ))
        self.main_layout.addWidget(self.camera_feed)
        
        # Bottom bar with camera info
        self.info_bar = QWidget()
        self.info_layout = QHBoxLayout(self.info_bar)
        self.info_layout.setContentsMargins(5, 5, 5, 5)
        
        # Camera name and status
        self.name_label = QLabel(self.camera_name)
        self.name_label.setStyleSheet("font-weight: bold;")
        self.info_layout.addWidget(self.name_label)
        
        # Space between
        self.info_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("Status: Not Running")
        self.info_layout.addWidget(self.status_indicator)
        
        # Violation indicator
        self.violation_indicator = QLabel("🟢")  # Green dot for no violations
        self.info_layout.addWidget(self.violation_indicator)
        
        self.main_layout.addWidget(self.info_bar)
        
        # Add border and styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)
    
    def start_camera(self):
        """Start the camera feed"""
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            if not self.camera.isOpened():
                self.status_indicator.setText("Status: Failed to open camera")
                return
                
            self.timer.start(30)  # Update every 30ms (approx 30 fps)
            self.status_indicator.setText("Status: Running")
        except Exception as e:
            self.status_indicator.setText(f"Status: Error - {str(e)}")
    
    def stop_camera(self):
        """Stop the camera feed"""
        if self.timer.isActive():
            self.timer.stop()
            
        if self.camera and self.camera.isOpened():
            self.camera.release()
            self.camera = None
            
        self.status_indicator.setText("Status: Stopped")
        
        # Reset to placeholder
        self.camera_feed.setPixmap(self.placeholder_pixmap.scaled(
            640, 480, Qt.KeepAspectRatio
        ))
    
    def update_frame(self):
        """Update the camera frame"""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Convert to RGB format
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # TODO: Here you would add your detection logic
                # For example:
                # detected_violations = detect_violations(frame)
                # if detected_violations:
                #     self.show_violation()
                
                # Convert to QImage
                h, w, ch = frame.shape
                img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                
                # Convert to QPixmap and display
                pixmap = QPixmap.fromImage(img)
                self.camera_feed.setPixmap(pixmap.scaled(
                    self.camera_feed.width(), 
                    self.camera_feed.height(), 
                    Qt.KeepAspectRatio
                ))
    
    def show_violation(self):
        """Indicate a violation"""
        self.violation_indicator.setText("🔴")  # Red dot for violation
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 2px solid #ff3333;
                border-radius: 4px;
            }
        """)
        
        # Reset after 3 seconds
        QTimer.singleShot(3000, self.reset_violation)
        
    def reset_violation(self):
        """Reset violation indicator"""
        self.violation_indicator.setText("🟢")  # Green dot for no violations
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)