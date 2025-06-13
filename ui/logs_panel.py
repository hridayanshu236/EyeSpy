from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class LogsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("Violation Logs")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.room_filter = QComboBox()
        self.room_filter.addItems(["All Rooms", "Exam Room"])
        self.header_layout.addWidget(QLabel("Room:"))
        self.header_layout.addWidget(self.room_filter)
        self.violation_filter = QComboBox()
        self.violation_filter.addItems(["All Violations", "Cheating"])
        self.header_layout.addWidget(QLabel("Violation Type:"))
        self.header_layout.addWidget(self.violation_filter)
        self.export_btn = QPushButton("Export Logs")
        self.header_layout.addWidget(self.export_btn)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        self.header_layout.addWidget(self.refresh_btn)
        self.main_layout.addWidget(self.header)
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(["Time", "Room", "Camera", "Violation Type", "Action"])
        self.logs_table.setColumnWidth(0, 180)
        self.logs_table.setColumnWidth(1, 100)
        self.logs_table.setColumnWidth(2, 150)
        self.logs_table.setColumnWidth(3, 200)
        self.logs_table.setColumnWidth(4, 150)
        self.main_layout.addWidget(self.logs_table)
        self.logs = []

    def set_camera_widget(self, camera_widget):
        self.camera_widget = camera_widget

    def refresh_logs(self):
        if hasattr(self, 'camera_widget'):
            self.logs = self.camera_widget.get_violation_logs()
            self.update_logs_table()

    def update_logs_table(self):
        room_filter = self.room_filter.currentText()
        violation_filter = self.violation_filter.currentText()
        filtered_logs = self.logs
        if room_filter != "All Rooms":
            filtered_logs = [log for log in filtered_logs if log["room"] == room_filter]
        if violation_filter != "All Violations":
            filtered_logs = [log for log in filtered_logs if log["type"] == violation_filter]
        self.logs_table.setRowCount(len(filtered_logs))
        for row, log in enumerate(filtered_logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(log["time"]))
            self.logs_table.setItem(row, 1, QTableWidgetItem(log["room"]))
            self.logs_table.setItem(row, 2, QTableWidgetItem(log["camera"]))
            type_item = QTableWidgetItem(log["type"])
            if log["type"] == "Cheating":
                type_item.setBackground(QColor(255, 200, 200))
            self.logs_table.setItem(row, 3, type_item)
            self.logs_table.setItem(row, 4, QTableWidgetItem(log["action"]))

    def export_logs(self):
        import csv
        from PyQt5.QtWidgets import QFileDialog
        import os
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Logs", os.path.expanduser("~/violations_log.csv"), "CSV Files (*.csv)"
        )
        if not filename:
            return
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['Time', 'Room', 'Camera', 'Violation Type', 'Action', 'Score']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for log in self.logs:
                    writer.writerow({
                        'Time': log['time'],
                        'Room': log['room'],
                        'Camera': log['camera'],
                        'Violation Type': log['type'],
                        'Action': log['action'],
                        'Score': f"{log['score']:.2f}" if 'score' in log else "N/A"
                    })
            print(f"Logs exported to {filename}")
        except Exception as e:
            print(f"Error exporting logs: {str(e)}")