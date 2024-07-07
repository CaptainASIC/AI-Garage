from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

class MenuPanel(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.home_button = self.create_button("Home", 0)
        self.llm_button = self.create_button("LLMs", 1)
        self.sd_button = self.create_button("Stable Diffusion", 2)
        self.tts_button = self.create_button("TTS", 3)
        self.sts_button = self.create_button("STS", 4)
        self.settings_button = self.create_button("Settings", 5)
        
        for button in [self.home_button, self.llm_button, self.sd_button, self.tts_button, self.sts_button, self.settings_button]:
            button.setFixedSize(150, 50)
            layout.addWidget(button)
        
        layout.addStretch()

        # Add ASIC.png image
        asic_label = QLabel()
        asic_pixmap = QPixmap("img/ASIC.png")
        asic_label.setPixmap(asic_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        asic_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(asic_label)

    def create_button(self, text, index):
        button = QPushButton(text)
        button.clicked.connect(lambda: self.page_changed.emit(index))
        return button