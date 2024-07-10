import psutil
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
import subprocess

class Gauge(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 120)  # Reduced height
        self.value = 0
        self.title = title
        self.initUI()

    def initUI(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateValue)
        self.timer.start(1000)

    def updateValue(self):
        if self.title == "CPU":
            self.value = psutil.cpu_percent()
        elif self.title == "RAM":
            self.value = psutil.virtual_memory().percent
        elif self.title == "GPU":
            try:
                with open('/sys/class/drm/card1/device/gpu_busy_percent', 'r') as f:
                    self.value = float(f.read().strip())
            except:
                self.value = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()
        
        # Set up the gauge area
        gauge_rect = QRectF(15, 15, width - 30, (height - 30) * 2)
        center = gauge_rect.center()
        radius = gauge_rect.width() / 2
        
        # Draw the background arc
        painter.setPen(QPen(Qt.GlobalColor.darkGray, 10))
        painter.drawArc(gauge_rect, 180 * 16, 180 * 16)
        
        # Draw the colored arc
        gradient = QLinearGradient(gauge_rect.topLeft(), gauge_rect.topRight())
        gradient.setColorAt(0, Qt.GlobalColor.green)
        gradient.setColorAt(0.5, Qt.GlobalColor.yellow)
        gradient.setColorAt(1, Qt.GlobalColor.red)
        painter.setPen(QPen(QBrush(gradient), 10))
        span_angle = int(self.value * 1.8 * 16)
        painter.drawArc(gauge_rect, 180 * 16, -span_angle)
        
        # Draw tick marks and labels
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setFont(QFont('Arial', 8))
        for i in range(11):
            angle = math.pi - i * math.pi / 10
            x1 = center.x() + (radius - 15) * math.cos(angle)
            y1 = center.y() - (radius - 15) * math.sin(angle)
            x2 = center.x() + radius * math.cos(angle)
            y2 = center.y() - radius * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
            if i % 2 == 0:
                label = str(i * 10)
                text_width = painter.fontMetrics().horizontalAdvance(label)
                text_x = x1 - text_width / 2
                text_y = y1 + 15
                painter.drawText(QPointF(text_x, text_y), label)
        
        # Draw the value
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        value_text = f"{round(self.value)}%"
        value_rect = QRectF(0, height/2 - 0, width, 30)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, value_text)
        
        # Draw title label
        painter.setFont(QFont('Arial', 12))
        title_rect = QRectF(0, height - 20, width, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)

class TemperatureGauge(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.temperature = 0
        self.setMinimumSize(100, 120)  # Increased height to accommodate text below
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTemperature)
        self.timer.start(1000)

    def updateTemperature(self):
        if self.title == "CPU Temp":
            self.temperature = self.get_cpu_temperature()
        elif self.title == "GPU Temp":
            self.temperature = self.get_gpu_temperature()
        self.update()

    def get_cpu_temperature(self):
        try:
            result = subprocess.run(['sensors'], stdout=subprocess.PIPE, text=True)
            for line in result.stdout.split('\n'):
                if 'Tctl' in line:
                    return float(line.split('+')[1].split('°')[0])
        except:
            return 0

    def get_gpu_temperature(self):
        try:
            result = subprocess.run(['sensors'], stdout=subprocess.PIPE, text=True)
            for line in result.stdout.split('\n'):
                if 'edge' in line:
                    return float(line.split('+')[1].split('°')[0])
        except:
            return 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the bubble
        rect = QRectF(5, 5, self.width() - 10, self.height() - 30)  # Reduced height for text below
        green_value = max(0, min(255, int(255 - self.temperature * 2.55)))
        color = QColor(255, green_value, 0)  # Red to Green based on temperature
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)

        # Draw the temperature text
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPointSize(14)
        painter.setFont(font)
        temp_rect = QRectF(5, 5, self.width() - 10, self.height() - 30)
        painter.drawText(temp_rect, Qt.AlignmentFlag.AlignCenter, f"{self.temperature:.1f}°C")

        # Draw the title below the gauge
        painter.setPen(Qt.GlobalColor.white)
        font.setPointSize(10)
        painter.setFont(font)
        title_rect = QRectF(5, self.height() - 25, self.width() - 10, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)

class PerformanceMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)  # Add a small spacing between gauges

        # Usage gauges
        self.cpu_gauge = Gauge("CPU", self)
        self.ram_gauge = Gauge("RAM", self)
        self.gpu_gauge = Gauge("GPU", self)

        # Temperature gauges
        temp_layout = QHBoxLayout()
        self.cpu_temp_gauge = TemperatureGauge("CPU Temp", self)
        self.gpu_temp_gauge = TemperatureGauge("GPU Temp", self)
        temp_layout.addWidget(self.cpu_temp_gauge)
        temp_layout.addWidget(self.gpu_temp_gauge)

        layout.addWidget(self.cpu_gauge)
        layout.addWidget(self.ram_gauge)
        layout.addWidget(self.gpu_gauge)
        layout.addLayout(temp_layout)

        # Set a fixed height for the temperature gauges
        self.cpu_temp_gauge.setFixedHeight(120)
        self.gpu_temp_gauge.setFixedHeight(120)