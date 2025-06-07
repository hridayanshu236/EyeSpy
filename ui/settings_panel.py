from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget
)
from PyQt5.QtCore import Qt

class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main vertical layout for the panel
        self.main_layout = QVBoxLayout(self)

        # --- Header Section ---
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)

        self.title_label = QLabel("System Settings")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
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
        self.header_layout.addWidget(self.save_btn)

        self.main_layout.addWidget(self.header)

        # --- Tabs Section ---
        self.settings_tabs = QTabWidget()

        # Add empty tabs as placeholders
        self.settings_tabs.addTab(QWidget(), "General")
        self.settings_tabs.addTab(QWidget(), "Detection")
        self.settings_tabs.addTab(QWidget(), "Cameras")
        self.settings_tabs.addTab(QWidget(), "Notifications")

        self.main_layout.addWidget(self.settings_tabs)
