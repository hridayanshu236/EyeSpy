from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

class StatisticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        
        # Header
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("Violation Statistics")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Filter controls
        self.time_filter = QComboBox()
        self.time_filter.addItems(["Today", "Last 7 Days", "This Month", "All Time"])
        self.header_layout.addWidget(QLabel("Time Period:"))
        self.header_layout.addWidget(self.time_filter)
        
        self.room_filter = QComboBox()
        self.room_filter.addItems(["All Rooms", "Room 101", "Room 102", "Room 103"])
        self.header_layout.addWidget(QLabel("Room:"))
        self.header_layout.addWidget(self.room_filter)
        
        self.export_btn = QPushButton("Export Stats")
        self.header_layout.addWidget(self.export_btn)
        
        self.main_layout.addWidget(self.header)
        
        # Statistics grid
        self.stats_grid = QGridLayout()
        self.main_layout.addLayout(self.stats_grid)
        
        # Summary boxes
        self.create_summary_boxes()
        
        # Charts
        self.create_charts()
        
    def create_summary_boxes(self):
        """Create summary statistic boxes"""
        summary_data = [
            {"title": "Total Violations", "value": "42", "change": "+8%"},
            {"title": "Smartphone Usage", "value": "18", "change": "+12%"},
            {"title": "Looking Back", "value": "15", "change": "-5%"},
            {"title": "Communication", "value": "9", "change": "+10%"}
        ]
        
        for i, data in enumerate(summary_data):
            box = QFrame()
            box.setFrameShape(QFrame.StyledPanel)
            box.setStyleSheet("""
                QFrame {
                    background-color: #333333;
                    border-radius: 8px;
                    padding: 10px;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            
            layout = QVBoxLayout(box)
            
            # Title
            title = QLabel(data["title"])
            title.setStyleSheet("font-size: 14px;")
            layout.addWidget(title)
            
            # Value
            value = QLabel(data["value"])
            value.setStyleSheet("font-size: 24px; font-weight: bold;")
            layout.addWidget(value)
            
            # Change
            change = QLabel(data["change"])
            if data["change"].startswith("+"):
                change.setStyleSheet("color: #ff6b6b;")  # Red for increase (bad)
            else:
                change.setStyleSheet("color: #69db7c;")  # Green for decrease (good)
            layout.addWidget(change)
            
            self.stats_grid.addWidget(box, 0, i)
    
    def create_charts(self):
        """Create statistics charts"""
        
        # 1. Violations by Type (Pie Chart)
        pie_chart = QChart()
        pie_chart.setTitle("Violations by Type")
        pie_chart.setAnimationOptions(QChart.SeriesAnimations)
        pie_chart.setTheme(QChart.ChartThemeDark)
        
        pie_series = QPieSeries()
        pie_series.append("Looking Back", 15)
        pie_series.append("Smartphone Usage", 18)
        pie_series.append("Communication", 9)
        
        # Set slice colors and make them exploded
        slices = pie_series.slices()
        for i, slice in enumerate(slices):
            colors = [QColor("#ff9f43"), QColor("#ee5253"), QColor("#0abde3")]
            slice.setBrush(colors[i % len(colors)])
            slice.setLabelVisible(True)
            slice.setExploded(True)
            slice.setExplodeDistanceFactor(0.1)
            slice.setLabelVisible(True)

        
        pie_chart.addSeries(pie_series)
        pie_chart.legend().setVisible(True)
        pie_chart.legend().setAlignment(Qt.AlignBottom)
        
        pie_view = QChartView(pie_chart)
        pie_view.setRenderHint(QPainter.Antialiasing)
        
        # 2. Violations Over Time (Bar Chart)
        bar_chart = QChart()
        bar_chart.setTitle("Violations Over Time")
        bar_chart.setAnimationOptions(QChart.SeriesAnimations)
        bar_chart.setTheme(QChart.ChartThemeDark)
        
        looking_back = QBarSet("Looking Back")
        smartphone = QBarSet("Smartphone")
        communication = QBarSet("Communication")
        
        # Sample data for the past 6 hours
        looking_back.append([1, 3, 2, 4, 3, 2])
        smartphone.append([2, 2, 3, 5, 4, 2])
        communication.append([1, 0, 2, 2, 3, 1])
        
        bar_series = QBarSeries()
        bar_series.append(looking_back)
        bar_series.append(smartphone)
        bar_series.append(communication)
        
        bar_chart.addSeries(bar_series)
        
        categories = ["11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        bar_chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 10)
        bar_chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        bar_chart.legend().setVisible(True)
        bar_chart.legend().setAlignment(Qt.AlignBottom)
        
        bar_view = QChartView(bar_chart)
        bar_view.setRenderHint(QPainter.Antialiasing)
        
        # Add charts to grid
        self.stats_grid.addWidget(pie_view, 1, 0, 1, 2)
        self.stats_grid.addWidget(bar_view, 1, 2, 1, 2)