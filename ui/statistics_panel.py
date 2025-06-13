from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter, QColor, QFont

class StatisticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(5000)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("Exam Monitoring Statistics")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.main_layout.addWidget(self.header)
        self.stats_grid = QGridLayout()
        self.create_stat_box("Total Violations", "0", 0, 0)
        self.create_stat_box("Cheating", "0", 0, 1)
        self.main_layout.addLayout(self.stats_grid)
        self.charts_container = QWidget()
        self.charts_layout = QHBoxLayout(self.charts_container)
        self.violation_chart_view = self.create_violation_type_chart()
        self.charts_layout.addWidget(self.violation_chart_view)
        self.timeline_chart_view = self.create_timeline_chart()
        self.charts_layout.addWidget(self.timeline_chart_view)
        self.main_layout.addWidget(self.charts_container)

    def create_stat_box(self, title, value, row, col):
        box = QFrame()
        box.setFrameShape(QFrame.StyledPanel)
        box.setStyleSheet("""
            QFrame {
                background-color: #383838;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(box)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        layout.addWidget(title_label)
        value_label = QLabel(value)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(value_label)
        self.stats_grid.addWidget(box, row, col)

    def create_violation_type_chart(self):
        series = QPieSeries()
        series.append("Cheating", 0)
        series.slices()[0].setBrush(QColor("#FF6347"))  # Red-ish
        for slice in series.slices():
            slice.setLabelVisible(True)
            slice.setExploded(True)
            slice.setLabelColor(QColor("#FFFFFF"))
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Violation Types")
        title_font = QFont()
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setTitleBrush(QColor("#FFFFFF"))
        chart.setBackgroundBrush(QColor("#383838"))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setLabelColor(QColor("#FFFFFF"))
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        self.violation_pie_series = series
        return chartView

    def create_timeline_chart(self):
        bar_set = QBarSet("Violations")
        bar_set.append([0, 0, 0, 0, 0, 0])
        bar_set.setColor(QColor("#FF6347"))
        series = QBarSeries()
        series.append(bar_set)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Violations Timeline (Last Hour)")
        title_font = QFont()
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setTitleBrush(QColor("#FFFFFF"))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#383838"))
        categories = ["50-60", "40-50", "30-40", "20-30", "10-20", "0-10"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_x.setLabelsColor(QColor("#FFFFFF"))
        axis_y = QValueAxis()
        axis_y.setRange(0, 10)
        axis_y.setTickCount(6)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        axis_y.setLabelsColor(QColor("#FFFFFF"))
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        self.timeline_series = series
        self.timeline_y_axis = axis_y
        return chartView

    def set_camera_widget(self, camera_widget):
        self.camera_widget = camera_widget

    def update_statistics(self):
        if not hasattr(self, 'camera_widget') or not hasattr(self.camera_widget, 'violation_log'):
            return
        logs = self.camera_widget.get_violation_logs()
        total_violations = len(logs)
        self.findChild(QLabel, "total_violations_value").setText(str(total_violations))
        cheating_count = sum(1 for log in logs if log["type"] == "Cheating")
        self.findChild(QLabel, "cheating_value").setText(str(cheating_count))
        if hasattr(self, 'violation_pie_series'):
            self.violation_pie_series.clear()
            if total_violations > 0:
                self.violation_pie_series.append("Cheating", cheating_count)
                if self.violation_pie_series.count() >= 1:
                    self.violation_pie_series.slices()[0].setBrush(QColor("#FF6347"))
                    for slice in self.violation_pie_series.slices():
                        slice.setLabelVisible(True)
                        slice.setExploded(True)
                        slice.setLabelColor(QColor("#FFFFFF"))
        if hasattr(self, 'timeline_series') and hasattr(self, 'timeline_y_axis'):
            import time
            current_time = int(time.time())
            time_buckets = [0, 0, 0, 0, 0, 0]
            for log in logs:
                try:
                    log_time = time.mktime(time.strptime(log["time"], "%Y-%m-%d %H:%M:%S"))
                    time_diff = current_time - log_time
                    if time_diff < 3600:
                        bucket = min(5, int(time_diff / 600))
                        time_buckets[bucket] += 1
                except Exception as e:
                    print(f"Error parsing timestamp: {e}")
            self.timeline_series.clear()
            bar_set = QBarSet("Violations")
            bar_set.append(time_buckets)
            bar_set.setColor(QColor("#FF6347"))
            self.timeline_series.append(bar_set)
            max_violations = max(time_buckets) if time_buckets else 0
            if max_violations > 0:
                self.timeline_y_axis.setRange(0, max(10, max_violations * 1.2))