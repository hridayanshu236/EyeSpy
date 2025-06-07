from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from ui.camera_widget import CameraWidget
from ui.logs_widget import LogsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EyeSpy - Exam Monitoring")
        self.resize(1200, 700)

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.camera_widget = CameraWidget()
        self.logs_widget = LogsWidget()

        layout.addWidget(self.camera_widget)
        layout.addWidget(self.logs_widget)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)
