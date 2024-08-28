# lib/menu.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

class MenuPanel(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self, theme_color):
        super().__init__()
        self.theme_color = theme_color
        self.setup_ui()
        self.current_index = 0  # Track the current selected index

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.buttons = [
            self.create_button("Home", 0),
            self.create_button("LLMs", 1),
            self.create_button("Generative AI", 2),
            self.create_button("Text-To-Speech", 3),
            self.create_button("Speech-To-Speech", 4),
            self.create_button("Settings", 5)
        ]
        
        for button in self.buttons:
            button.setFixedSize(150, 50)
            layout.addWidget(button)
        
        layout.addStretch()

        # Add ASIC.png image
        asic_label = QLabel()
        asic_pixmap = QPixmap("img/ASIC.png")
        asic_label.setPixmap(asic_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        asic_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(asic_label)

        # Set initial selection
        self.set_selected(0)

    def create_button(self, text, index):
        button = QPushButton(text)
        button.clicked.connect(lambda: self.button_clicked(index))
        return button

    def button_clicked(self, index):
        self.set_selected(index)
        self.page_changed.emit(index)

    def set_selected(self, index):
        for i, button in enumerate(self.buttons):
            if i == index:
                button.setStyleSheet(f"""
                    QPushButton {{
                        color: white;
                        background-color: rgba(255, 255, 255, 30);
                        border: 3px solid white;
                        border-radius: 15px;
                        padding: 5px;
                    }}
                """)
            else:
                button.setStyleSheet(f"""
                    QPushButton {{
                        color: white;
                        background-color: rgba(255, 255, 255, 30);
                        border: 1px solid {self.theme_color};
                        border-radius: 15px;
                        padding: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(255, 255, 255, 45);
                    }}
                """)
        self.current_index = index