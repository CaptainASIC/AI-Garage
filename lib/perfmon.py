import psutil
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
import pynvml

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
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                self.value = utilization.gpu
                pynvml.nvmlShutdown()
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

class PerformanceMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)  # Remove spacing between gauges
        self.cpu_gauge = Gauge("CPU", self)
        self.ram_gauge = Gauge("RAM", self)
        self.gpu_gauge = Gauge("GPU", self)
        layout.addWidget(self.cpu_gauge)
        layout.addWidget(self.ram_gauge)
        layout.addWidget(self.gpu_gauge)