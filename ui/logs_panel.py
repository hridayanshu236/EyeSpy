from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QComboBox,
                             QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class LogsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        
        # Header
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("Violation Logs")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Filter controls
        self.room_filter = QComboBox()
        self.room_filter.addItems(["All Rooms", "Room 101", "Room 102", "Room 103"])
        self.header_layout.addWidget(QLabel("Room:"))
        self.header_layout.addWidget(self.room_filter)
        
        self.violation_filter = QComboBox()
        self.violation_filter.addItems(["All Violations", "Looking Back", "Smartphone", "Communication"])
        self.header_layout.addWidget(QLabel("Violation Type:"))
        self.header_layout.addWidget(self.violation_filter)
        
        self.export_btn = QPushButton("Export Logs")
        self.header_layout.addWidget(self.export_btn)
        
        self.main_layout.addWidget(self.header)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(["Time", "Room", "Camera", "Violation Type", "Action"])
        
        # Set column widths
        self.logs_table.setColumnWidth(0, 180)  # Time
        self.logs_table.setColumnWidth(1, 100)  # Room
        self.logs_table.setColumnWidth(2, 150)  # Camera
        self.logs_table.setColumnWidth(3, 200)  # Violation Type
        self.logs_table.setColumnWidth(4, 150)  # Action
        
        # Add some sample data
        self.add_sample_logs()
        
        self.main_layout.addWidget(self.logs_table)
        
    def add_sample_logs(self):
        """Add sample log entries for demonstration"""
        logs = [
            ["2025-06-07 04:15:10", "Room 101", "Camera 1", "Looking Back", "Flagged"],
            ["2025-06-07 04:12:45", "Room 102", "Camera 2", "Smartphone Usage", "Warning Issued"],
            ["2025-06-07 04:10:22", "Room 101", "Camera 3", "Communication", "Flagged"],
            ["2025-06-07 04:05:17", "Room 103", "Camera 1", "Looking Back", "Warning Issued"],
            ["2025-06-07 04:03:56", "Room 102", "Camera 3", "Smartphone Usage", "Supervisor Notified"],
            ["2025-06-07 04:01:30", "Room 103", "Camera 2", "Communication", "Flagged"],
            ["2025-06-07 03:58:12", "Room 101", "Camera 2", "Looking Back", "Warning Issued"],
            ["2025-06-07 03:55:43", "Room 103", "Camera 1", "Smartphone Usage", "Supervisor Notified"],
            ["2025-06-07 03:53:21", "Room 102", "Camera 1", "Communication", "Flagged"],
            ["2025-06-07 03:50:09", "Room 101", "Camera 3", "Looking Back", "Warning Issued"]
        ]
        
        self.logs_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            for col, value in enumerate(log):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make non-editable
                
                # Color-code by violation type
                if col == 3:
                    if value == "Looking Back":
                        item.setBackground(QColor(255, 255, 200))  # Light yellow
                    elif value == "Smartphone Usage":
                        item.setBackground(QColor(255, 200, 200))  # Light red
                    elif value == "Communication":
                        item.setBackground(QColor(200, 255, 200))  # Light green
                
                self.logs_table.setItem(row, col, item)