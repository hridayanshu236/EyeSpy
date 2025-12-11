from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFormLayout,
                             QTabWidget, QSpinBox, QCheckBox, QSlider,
                             QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt

class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        
        # Header
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("System Settings")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Save button
        self.save_btn = QPushButton("Save Settings")
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
        
        # Settings tabs
        self.settings_tabs = QTabWidget()
        
        # Create settings tabs
        self.create_general_tab()
        self.create_detection_tab()
        self.create_camera_tab()
        self.create_notification_tab()
        
        self.main_layout.addWidget(self.settings_tabs)
        
    def create_general_tab(self):
        """Create general settings tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System settings
        system_group = QGroupBox("System Settings")
        system_layout = QFormLayout()
        
        self.sys_name = QLineEdit("EyeSpy Monitoring System")
        system_layout.addRow("System Name:", self.sys_name)
        
        self.sys_location = QLineEdit("Main Examination Center")
        system_layout.addRow("Location:", self.sys_location)
        
        self.sys_theme = QComboBox()
        self.sys_theme.addItems(["Dark Theme", "Light Theme"])
        system_layout.addRow("UI Theme:", self.sys_theme)
        
        self.sys_language = QComboBox()
        self.sys_language.addItems(["English", "Spanish", "French", "German"])
        system_layout.addRow("Language:", self.sys_language)
        
        self.sys_log_days = QSpinBox()
        self.sys_log_days.setRange(7, 365)
        self.sys_log_days.setValue(30)
        system_layout.addRow("Keep logs for (days):", self.sys_log_days)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # User settings
        user_group = QGroupBox("User Settings")
        user_layout = QFormLayout()
        
        self.user_email = QLineEdit("admin@example.com")
        user_layout.addRow("Admin Email:", self.user_email)
        
        self.user_password = QPushButton("Change Password")
        user_layout.addRow("Password:", self.user_password)
        
        self.user_notifications = QCheckBox("Receive email notifications")
        self.user_notifications.setChecked(True)
        user_layout.addRow("Notifications:", self.user_notifications)
        
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        
        # Add spacer
        layout.addStretch()
        
        scroll.setWidget(tab)
        self.settings_tabs.addTab(scroll, "General")
        
    def create_detection_tab(self):
        """Create detection settings tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Detection settings
        detection_group = QGroupBox("Detection Sensitivity")
        detection_layout = QFormLayout()
        
        # Looking back sensitivity
        self.looking_back_sensitivity = QSlider(Qt.Horizontal)
        self.looking_back_sensitivity.setRange(1, 10)
        self.looking_back_sensitivity.setValue(7)
        self.looking_back_sensitivity.setTickPosition(QSlider.TicksBelow)
        self.looking_back_sensitivity.setTickInterval(1)
        detection_layout.addRow("Looking Back Sensitivity:", self.looking_back_sensitivity)
        
        # Smartphone usage sensitivity
        self.smartphone_sensitivity = QSlider(Qt.Horizontal)
        self.smartphone_sensitivity.setRange(1, 10)
        self.smartphone_sensitivity.setValue(8)
        self.smartphone_sensitivity.setTickPosition(QSlider.TicksBelow)
        self.smartphone_sensitivity.setTickInterval(1)
        detection_layout.addRow("Smartphone Usage Sensitivity:", self.smartphone_sensitivity)
        
        # Communication sensitivity
        self.communication_sensitivity = QSlider(Qt.Horizontal)
        self.communication_sensitivity.setRange(1, 10)
        self.communication_sensitivity.setValue(6)
        self.communication_sensitivity.setTickPosition(QSlider.TicksBelow)
        self.communication_sensitivity.setTickInterval(1)
        detection_layout.addRow("Communication Detection Sensitivity:", self.communication_sensitivity)
        
        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)
        
        # Alert thresholds
        threshold_group = QGroupBox("Alert Thresholds")
        threshold_layout = QFormLayout()
        
        self.alert_threshold = QSpinBox()
        self.alert_threshold.setRange(1, 10)
        self.alert_threshold.setValue(3)
        threshold_layout.addRow("Alert after consecutive detections:", self.alert_threshold)
        
        self.supervisor_threshold = QSpinBox()
        self.supervisor_threshold.setRange(1, 20)
        self.supervisor_threshold.setValue(5)
        threshold_layout.addRow("Notify supervisor after violations:", self.supervisor_threshold)
        
        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)
        
        # False positive reduction
        fp_group = QGroupBox("False Positive Reduction")
        fp_layout = QFormLayout()
        
        self.min_confidence = QSlider(Qt.Horizontal)
        self.min_confidence.setRange(50, 99)
        self.min_confidence.setValue(80)
        self.min_confidence.setTickPosition(QSlider.TicksBelow)
        self.min_confidence.setTickInterval(5)
        fp_layout.addRow("Minimum Confidence (%):", self.min_confidence)
        
        self.min_duration = QSpinBox()
        self.min_duration.setRange(1, 10)
        self.min_duration.setValue(2)
        fp_layout.addRow("Minimum Duration (seconds):", self.min_duration)
        
        fp_group.setLayout(fp_layout)
        layout.addWidget(fp_group)
        
        # Add spacer
        layout.addStretch()
        
        scroll.setWidget(tab)
        self.settings_tabs.addTab(scroll, "Detection")
        
    def create_camera_tab(self):
        """Create camera settings tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Camera settings
        for room_num in range(1, 4):
            room_group = QGroupBox(f"Room 10{room_num} Cameras")
            room_layout = QVBoxLayout()
            
            for cam_num in range(1, 4):
                cam_widget = QWidget()
                cam_layout = QHBoxLayout(cam_widget)
                
                cam_label = QLabel(f"Camera {cam_num}")
                cam_layout.addWidget(cam_label)
                
                cam_url = QLineEdit(f"rtsp://example.com/room10{room_num}_cam{cam_num}")
                cam_layout.addWidget(cam_url)
                
                cam_status = QComboBox()
                cam_status.addItems(["Enabled", "Disabled"])
                cam_layout.addWidget(cam_status)
                
                cam_test = QPushButton("Test")
                cam_layout.addWidget(cam_test)
                
                room_layout.addWidget(cam_widget)
                
            room_group.setLayout(room_layout)
            layout.addWidget(room_group)
        
        # Video settings
        video_group = QGroupBox("Video Settings")
        video_layout = QFormLayout()
        
        self.video_quality = QComboBox()
        self.video_quality.addItems(["Low (640x480)", "Medium (1280x720)", "High (1920x1080)"])
        self.video_quality.setCurrentIndex(1)  # Medium by default
        video_layout.addRow("Resolution:", self.video_quality)
        
        self.video_fps = QComboBox()
        self.video_fps.addItems(["15 fps", "24 fps", "30 fps"])
        video_layout.addRow("Frame Rate:", self.video_fps)
        
        self.record_video = QCheckBox("Record video footage")
        self.record_video.setChecked(True)
        video_layout.addRow("Recording:", self.record_video)
        
        self.record_days = QSpinBox()
        self.record_days.setRange(1, 30)
        self.record_days.setValue(7)
        video_layout.addRow("Keep recordings for (days):", self.record_days)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # Add spacer
        layout.addStretch()
        
        scroll.setWidget(tab)
        self.settings_tabs.addTab(scroll, "Cameras")
        
    def create_notification_tab(self):
        """Create notification settings tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Alert settings
        alert_group = QGroupBox("Alert Settings")
        alert_layout = QFormLayout()
        
        self.alert_sound = QCheckBox("Play sound on violation")
        self.alert_sound.setChecked(True)
        alert_layout.addRow("Sound Alerts:", self.alert_sound)
        
        self.alert_visual = QCheckBox("Show visual indicators")
        self.alert_visual.setChecked(True)
        alert_layout.addRow("Visual Alerts:", self.alert_visual)
        
        self.alert_popup = QCheckBox("Show popup notifications")
        self.alert_popup.setChecked(True)
        alert_layout.addRow("Popup Notifications:", self.alert_popup)
        
        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)
        
        # Email notifications
        email_group = QGroupBox("Email Notifications")
        email_layout = QFormLayout()
        
        self.email_alerts = QCheckBox("Send email on critical violations")
        self.email_alerts.setChecked(True)
        email_layout.addRow("Email Alerts:", self.email_alerts)
        
        self.email_recipients = QLineEdit("admin@example.com, supervisor@example.com")
        email_layout.addRow("Recipients:", self.email_recipients)
        
        self.email_frequency = QComboBox()
        self.email_frequency.addItems(["Immediately", "Hourly Summary", "Daily Summary"])
        email_layout.addRow("Frequency:", self.email_frequency)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        # Report settings
        report_group = QGroupBox("Automatic Reports")
        report_layout = QFormLayout()
        
        self.report_daily = QCheckBox("Generate daily violation reports")
        self.report_daily.setChecked(True)
        report_layout.addRow("Daily Reports:", self.report_daily)
        
        self.report_weekly = QCheckBox("Generate weekly summary reports")
        self.report_weekly.setChecked(True)
        report_layout.addRow("Weekly Reports:", self.report_weekly)
        
        self.report_format = QComboBox()
        self.report_format.addItems(["PDF", "Excel", "CSV", "HTML"])
        report_layout.addRow("Report Format:", self.report_format)
        
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        # Add spacer
        layout.addStretch()
        
        scroll.setWidget(tab)
        self.settings_tabs.addTab(scroll, "Notifications")