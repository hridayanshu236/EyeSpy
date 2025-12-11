from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Set size and style
        self.setMinimumWidth(80)
        self.setMaximumWidth(80)
        self.setStyleSheet("""
            QWidget {
                background-color: #222222;
            }
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 15px;
                margin: 5px;
                background-color: transparent;
                color: #c2c2c2;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #333333;
                color: white;
            }
            QPushButton:checked {
                background-color: #444444;
                color: white;
            }
            QLabel {
                color: #c2c2c2;
                font-weight: bold;
                padding: 10px;
                text-align: center;
            }
        """)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 10)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)
        
        # App logo/title
        self.logo_label = QLabel("EyeSpy")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)
        
        # Navigation buttons - placeholder for icons (you'll need to add actual icons)
        self.cameras_btn = QPushButton("👁")
        self.cameras_btn.setCheckable(True)
        self.cameras_btn.setChecked(True)
        self.cameras_btn.setToolTip("Cameras")
        self.cameras_btn.setFont(QFont('Arial', 18))
        self.layout.addWidget(self.cameras_btn)
        
        self.logs_btn = QPushButton("📝")
        self.logs_btn.setCheckable(True)
        self.logs_btn.setToolTip("Logs")
        self.logs_btn.setFont(QFont('Arial', 18))
        self.layout.addWidget(self.logs_btn)
        
        self.stats_btn = QPushButton("📊")
        self.stats_btn.setCheckable(True)
        self.stats_btn.setToolTip("Statistics")
        self.stats_btn.setFont(QFont('Arial', 18))
        self.layout.addWidget(self.stats_btn)
        
        # Add a spacer
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Settings at bottom
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setCheckable(True)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFont(QFont('Arial', 18))
        self.layout.addWidget(self.settings_btn)
        
        # Connect button signals to ensure only one is checked at a time
        self.buttons = [self.cameras_btn, self.logs_btn, self.stats_btn, self.settings_btn]
        for btn in self.buttons:
            btn.clicked.connect(lambda checked, b=btn: self.update_buttons(b))
    
    def update_buttons(self, clicked_button):
        """Ensure only one button is checked at a time"""
        for button in self.buttons:
            if button != clicked_button:
                button.setChecked(False)
            else:
                button.setChecked(True)