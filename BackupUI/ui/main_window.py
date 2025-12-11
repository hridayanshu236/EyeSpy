from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from ui.sidebar import Sidebar
from ui.camera_dashboard import CameraDashboard
from ui.logs_panel import LogsPanel
from ui.statistics_panel import StatisticsPanel
from ui.settings_panel import SettingsPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("EyeSpy - Examination Monitoring System")
        self.setWindowIcon(QIcon("assets/logo_icon.png")) 
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        # Create stacked widget for different panels
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Set layout ratio (sidebar:content)
        self.main_layout.setStretch(0, 1)  # Sidebar takes 1 part
        self.main_layout.setStretch(1, 5)  # Content takes 5 parts
        
        # Initialize panels
        self.camera_dashboard = CameraDashboard()
        self.logs_panel = LogsPanel()
        self.statistics_panel = StatisticsPanel()
        self.settings_panel = SettingsPanel()
        
        # Add panels to stacked widget
        self.stacked_widget.addWidget(self.camera_dashboard)
        self.stacked_widget.addWidget(self.logs_panel)
        self.stacked_widget.addWidget(self.statistics_panel)
        self.stacked_widget.addWidget(self.settings_panel)
        
        # Connect sidebar signals
        self.sidebar.cameras_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.sidebar.logs_btn.clicked.connect(self.show_logs_panel)
        self.sidebar.stats_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.sidebar.settings_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # Connect camera widget to logs panel
        self.logs_panel.set_camera_widget(self.camera_dashboard.camera)
        
        # Set default panel
        self.stacked_widget.setCurrentIndex(0)
        
        # Set stylesheet
        self.setup_stylesheet()
        
    def show_logs_panel(self):
        """Show logs panel and refresh logs"""
        self.stacked_widget.setCurrentIndex(1)
        self.logs_panel.refresh_logs()
        
    def setup_stylesheet(self):
        """Set application stylesheet"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #383838;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                border-bottom: 2px solid #007bff;
            }
            QScrollArea {
                border: none;
                background-color: #2d2d2d;
            }
        """)