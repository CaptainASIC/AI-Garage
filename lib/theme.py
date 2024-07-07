from PyQt6.QtGui import QColor, QLinearGradient, QBrush, QPalette

def get_color_theme(theme):
    color_map = {
        "Dark Red": ("#8B0000", "#4B0000"),
        "Dark Blue": ("#00008B", "#00004B"),
        "Dark Green": ("#006400", "#003400"),
        "Dark Purple": ("#4B0082", "#250041"),
        "Blackout": ("#000000", "#000000")
    }
    return color_map.get(theme, ("#8B0000", "#4B0000"))  # Default to Dark Red

def set_color_theme(window, theme):
    base_color, gradient_start = get_color_theme(theme)

    # Set gradient background
    gradient = QLinearGradient(0, 0, 0, window.height())
    gradient.setColorAt(0, QColor(gradient_start))
    gradient.setColorAt(1, QColor(0, 0, 0))  # Black at bottom
    
    palette = window.palette()
    palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
    window.setPalette(palette)
    
    # Update StyleSheet
    window.setStyleSheet(f"""
        QMainWindow, QTabWidget, QStatusBar, QWidget, QMessageBox {{
            color: #ffffff;
        }}
        QTabWidget::pane {{
            border: 1px solid {base_color};
        }}
        QTabBar::tab {{
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 8px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }}
        QTabBar::tab:selected {{
            background-color: {base_color};
        }}
        QPushButton {{
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid {base_color};
            padding: 10px;
            margin: 5px;
            border-radius: 15px;
        }}
        QPushButton:hover {{
            background-color: {base_color};
        }}
        QScrollArea {{
            border: none;
        }}
        QLineEdit {{
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3a3a3a;
            padding: 5px;
        }}
        QMessageBox {{
            background-color: #2d2d2d;
            color: #ffffff;
        }}
        QMessageBox QPushButton {{
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #4a4a4a;
            padding: 5px 15px;
            border-radius: 3px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: #4a4a4a;
        }}
    """)