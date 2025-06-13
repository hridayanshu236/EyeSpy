import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QDateTime
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set dark theme for the entire application
    app.setStyle("Fusion")

    main_window = MainWindow()

    # Connect camera control buttons to camera widget
    camera_dashboard = main_window.camera_dashboard
    start_button = camera_dashboard.start_button
    stop_button = camera_dashboard.stop_button
    camera = camera_dashboard.camera
    
    start_button.clicked.connect(camera.start_camera)
    stop_button.clicked.connect(camera.stop_camera)

    # Connect camera widget to logs and statistics panels
    main_window.logs_panel.set_camera_widget(camera)
    main_window.statistics_panel.set_camera_widget(camera)

    # Setup timer to update date/time label
    def update_datetime():
        current_datetime = QDateTime.currentDateTime()
        formatted_datetime = current_datetime.toString("yyyy-MM-dd hh:mm:ss")
        camera_dashboard.date_time.setText(formatted_datetime)
    
    # Update initially
    update_datetime()
    
    # Create timer to update date/time every second
    timer = QTimer()
    timer.timeout.connect(update_datetime)
    timer.start(1000)  # Update every second

    main_window.show()
    sys.exit(app.exec_())