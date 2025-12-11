from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PyQt5.QtCore import Qt, QDateTime

from ui.camera_widget import CameraWidget

class CameraDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("Examination Monitoring")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setMinimumHeight(40)
        self.header_layout.addWidget(self.title_label)
        
        self.header_layout.addStretch()
        
        # Current date and time
        self.date_time = QLabel(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))
        self.header_layout.addWidget(self.date_time)
        
        self.main_layout.addWidget(self.header)
        
        # Camera section
        self.camera_section = QWidget()
        self.camera_layout = QVBoxLayout(self.camera_section)
        
        # Add camera access instructions
        self.instruction_label = QLabel(
            "This application needs access to your camera. Please grant permission when prompted."
        )
        self.instruction_label.setStyleSheet("color: #ffd700; margin-bottom: 10px;")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.camera_layout.addWidget(self.instruction_label)
        
        # Add single camera widget
        self.camera = CameraWidget("Webcam Camera")
        
        self.camera_layout.addWidget(self.camera)
        
        # Add camera control buttons
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        
        self.start_button = QPushButton("Start Camera")
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Camera")
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
                
            }
        """)
        self.button_layout.addWidget(self.stop_button)
        
        self.camera_layout.addWidget(self.button_container)
        
        self.main_layout.addWidget(self.camera_section)