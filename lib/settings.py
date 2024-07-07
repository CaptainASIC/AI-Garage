import subprocess
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QLabel, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class ColorSwatch(QPushButton):
    def __init__(self, color, size=30):
        super().__init__()
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: {size // 2}px;
                border: 2px solid #ffffff;
            }}
            QPushButton:checked {{
                border: 3px solid #ff0000;
            }}
        """)
        self.setCheckable(True)

class SettingsPage(QWidget):
    save_and_reload = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        main_layout = QGridLayout(self)

        # Color Theme Section
        color_theme_widget = QWidget()
        color_theme_layout = QHBoxLayout(color_theme_widget)
        color_theme_layout.addWidget(QLabel("Color Theme:"))
        
        self.color_swatches = {
            "Dark Red": ColorSwatch("#8B0000"),
            "Dark Blue": ColorSwatch("#00008B"),
            "Dark Green": ColorSwatch("#006400"),
            "Dark Purple": ColorSwatch("#4B0082"),
            "Blackout": ColorSwatch("#000000")
        }
        
        for name, swatch in self.color_swatches.items():
            color_theme_layout.addWidget(swatch)
            swatch.clicked.connect(lambda checked, n=name: self.select_color_theme(n))

        self.color_swatches[self.config.get('Settings', 'ColorTheme', fallback='Dark Red')].setChecked(True)
        
        main_layout.addWidget(color_theme_widget, 0, 1)

        # Containers Section
        containers_widget = QWidget()
        containers_layout = QVBoxLayout(containers_widget)

        fetch_button = QPushButton("Fetch Running Containers")
        fetch_button.setFixedSize(200, 50)
        fetch_button.clicked.connect(self.fetch_running_containers)
        
        containers_layout.addWidget(fetch_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.setup_input_section(containers_layout, "Containers")
        self.containers_table = self.create_table()
        containers_layout.addWidget(self.containers_table)

        main_layout.addWidget(containers_widget, 0, 0)

        # LLMs Section
        main_layout.addWidget(self.create_section("LLMs"), 1, 0)

        # Stable Diffusion Section
        main_layout.addWidget(self.create_section("StableDiffusion"), 1, 1)

        # TTS Section
        main_layout.addWidget(self.create_section("TTS"), 2, 0)

        # STS Section
        main_layout.addWidget(self.create_section("STS"), 2, 1)

        # Clear Cache Button
        clear_cache_button = QPushButton("Clear Browser Cache")
        clear_cache_button.clicked.connect(self.clear_cache)
        main_layout.addWidget(clear_cache_button, 3, 0)

        # Save and Reload UI Button
        save_reload_button = QPushButton("Save and Reload UI")
        save_reload_button.clicked.connect(self.save_and_reload_ui)
        main_layout.addWidget(save_reload_button, 3, 1)

        self.refresh_tables()

    def create_section(self, section_name):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.setup_input_section(layout, section_name)
        table = self.create_table()
        layout.addWidget(table)
        setattr(self, f"{section_name.lower()}_table", table)
        return widget

    def setup_input_section(self, layout, section_name):
        input_layout = QHBoxLayout()
        name_entry = QLineEdit()
        name_entry.setPlaceholderText(f"{section_name} Name")
        value_entry = QLineEdit()
        value_entry.setPlaceholderText(f"{section_name} Value")
        add_button = QPushButton(f"Add {section_name}")
        input_layout.addWidget(name_entry)
        input_layout.addWidget(value_entry)
        input_layout.addWidget(add_button)
        layout.addLayout(input_layout)
        
        setattr(self, f"{section_name.lower()}_name_entry", name_entry)
        setattr(self, f"{section_name.lower()}_value_entry", value_entry)
        add_button.clicked.connect(lambda: self.add_item(section_name))

    def create_table(self):
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Name", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setFixedHeight(200)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                gridline-color: #3a3a3a;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #2d2d2d;
            }
        """)
        return table

    def fetch_running_containers(self):
        try:
            result = subprocess.run(["podman", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=True)
            containers = result.stdout.strip().split('\n')
            message = "Running Containers:\n" + "\n".join(containers)
            self.show_themed_message_box("Running Containers", message, QMessageBox.Icon.Information)
        except subprocess.CalledProcessError as e:
            self.show_themed_message_box("Error", f"Failed to fetch running containers: {e}", QMessageBox.Icon.Warning)

    def add_item(self, section):
        name_entry = getattr(self, f"{section.lower()}_name_entry")
        value_entry = getattr(self, f"{section.lower()}_value_entry")
        name = name_entry.text() or f"New {section}"
        value = value_entry.text() or "default_value"
        
        if name and value:
            self.config[section][name] = value
            self.refresh_tables()
            name_entry.clear()
            value_entry.clear()
        else:
            self.show_themed_message_box("Error", "Both name and value must be provided", QMessageBox.Icon.Warning)

    def refresh_tables(self):
        for section in ["Containers", "LLMs", "StableDiffusion", "TTS", "STS"]:
            table = getattr(self, f"{section.lower()}_table")
            self.refresh_table(table, section)

    def refresh_table(self, table, section):
        table.setRowCount(0)
        for name, value in self.config[section].items():
            row_position = table.rowCount()
            table.insertRow(row_position)
            name_item = QTableWidgetItem(name)
            value_item = QTableWidgetItem(value)
            name_item.setForeground(QColor("#ffffff"))
            value_item.setForeground(QColor("#ffffff"))
            table.setItem(row_position, 0, name_item)
            table.setItem(row_position, 1, value_item)

        table.cellChanged.connect(lambda row, column: self.update_item(row, column, table, section))

    def update_item(self, row, column, table, section):
        name = table.item(row, 0).text()
        value = table.item(row, 1).text()
        old_name = list(self.config[section].keys())[row]

        if column == 0:  # Name changed
            del self.config[section][old_name]
            self.config[section][name] = value
        else:  # Value changed
            self.config[section][name] = value

        # Disconnect and reconnect to prevent recursive calls
        table.cellChanged.disconnect()
        self.refresh_table(table, section)

    def select_color_theme(self, theme):
        for name, swatch in self.color_swatches.items():
            swatch.setChecked(name == theme)
        self.config['Settings']['ColorTheme'] = theme

    def clear_cache(self):
        if hasattr(self.parent(), 'persistent_profile'):
            self.parent().persistent_profile.clearHttpCache()
            self.show_themed_message_box("Cache Cleared", "The browser cache has been cleared.", QMessageBox.Icon.Information)
        else:
            self.show_themed_message_box("Error", "Unable to clear cache. Persistent profile not found.", QMessageBox.Icon.Warning)

    def save_and_reload_ui(self):
        selected_theme = next(name for name, swatch in self.color_swatches.items() if swatch.isChecked())
        self.config['Settings']['ColorTheme'] = selected_theme
        with open('cfg/config.ini', 'w') as configfile:
            self.config.write(configfile)
        self.save_and_reload.emit(selected_theme)

    def show_themed_message_box(self, title, message, icon):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        msg_box.exec()