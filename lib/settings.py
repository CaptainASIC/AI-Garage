import subprocess
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QLabel, QMessageBox, QGridLayout,
                             QCheckBox, QGroupBox, QListWidget, QListWidgetItem, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
import requests

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
        self.main_layout = QGridLayout(self)

        # Top section (Color Theme and AI Services)
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        # Color Theme Section
        color_theme_group = QGroupBox("Color Theme")
        color_theme_layout = QHBoxLayout(color_theme_group)
        
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
        
        top_layout.addWidget(color_theme_group)

        # AI Services Section
        ai_services_group = QGroupBox("AI Services")
        ai_services_layout = QVBoxLayout(ai_services_group)

        self.service_checkboxes = {}
        self.api_key_inputs = {}

        for service in ["ChatGPT", "Claude"]:
            service_layout = QHBoxLayout()
            checkbox = QCheckBox(service)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: white;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                    border: 1px solid white;
                }
                QCheckBox::indicator:unchecked {
                    background-color: transparent;
                }
                QCheckBox::indicator:checked {
                    background-color: green;
                }
                QCheckBox::indicator:checked::after {
                    content: '✓';
                    color: black;
                    position: absolute;
                    top: -3px;
                    left: 1px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            api_key_input = QLineEdit()
            api_key_input.setPlaceholderText(f"{service} API Key")
            api_key_input.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
            
            self.service_checkboxes[service] = checkbox
            self.api_key_inputs[service] = api_key_input

            service_layout.addWidget(checkbox)
            service_layout.addWidget(api_key_input)
            ai_services_layout.addLayout(service_layout)

            # Load saved settings
            if service in self.config['Settings']:
                checkbox.setChecked(self.config['Settings'].getboolean(service, fallback=False))
                api_key_input.setText(self.config['Settings'].get(f"{service}_API_Key", fallback=""))

        top_layout.addWidget(ai_services_group)
        self.main_layout.addWidget(top_widget, 0, 0, 1, 2)

        # Containers Section
        containers_group = self.create_section("Containers")
        containers_layout = containers_group.layout()
        
        # Add Fetch Running Containers button
        fetch_button = QPushButton("Fetch Running Containers")
        fetch_button.clicked.connect(self.fetch_running_containers)
        fetch_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        containers_layout.addWidget(fetch_button)
        
        self.main_layout.addWidget(containers_group, 1, 0)

        # Ollama Section
        self.main_layout.addWidget(self.setup_ollama_section(), 1, 1)

        # LLMs Section
        self.main_layout.addWidget(self.create_section("LLMs"), 2, 0)

        # Stable Diffusion Section
        self.main_layout.addWidget(self.create_section("StableDiffusion"), 2, 1)

        # TTS Section
        self.main_layout.addWidget(self.create_section("TTS"), 3, 0)

        # STS Section
        self.main_layout.addWidget(self.create_section("STS"), 3, 1)

        # Bottom buttons
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        clear_cache_button = QPushButton("Clear Browser Cache")
        clear_cache_button.clicked.connect(self.clear_cache)
        clear_cache_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        bottom_layout.addWidget(clear_cache_button)

        save_reload_button = QPushButton("Save and Reload UI")
        save_reload_button.clicked.connect(self.save_and_reload_ui)
        save_reload_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        bottom_layout.addWidget(save_reload_button)

        self.main_layout.addWidget(bottom_widget, 4, 0, 1, 2)

        self.refresh_tables()

    def create_section(self, section_name):
        group = QGroupBox(section_name)
        group.setStyleSheet("QGroupBox { color: white; }")
        layout = QVBoxLayout(group)
        self.setup_input_section(layout, section_name)
        table = self.create_table()
        layout.addWidget(table)
        setattr(self, f"{section_name.lower()}_table", table)
        return group

    def setup_input_section(self, layout, section_name):
        input_layout = QHBoxLayout()
        name_entry = QLineEdit()
        name_entry.setPlaceholderText(f"{section_name} Name")
        name_entry.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        value_entry = QLineEdit()
        value_entry.setPlaceholderText(f"{section_name} Value")
        value_entry.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        add_button = QPushButton(f"Add {section_name}")
        add_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
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

    def setup_ollama_section(self):
        ollama_group = QGroupBox("Ollama")
        ollama_layout = QVBoxLayout(ollama_group)

        # Enable/Disable checkbox
        self.ollama_checkbox = QCheckBox("Enable Ollama")
        self.ollama_checkbox.setChecked(self.config['Settings'].getboolean('Ollama', fallback=False))
        self.ollama_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid white;
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
            }
            QCheckBox::indicator:checked {
                background-color: green;
            }
            QCheckBox::indicator:checked::after {
                content: '✓';
                color: black;
                position: absolute;
                top: -3px;
                left: 1px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        ollama_layout.addWidget(self.ollama_checkbox)
        
        # Server address input
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        self.ollama_server_input = QLineEdit(self.config['Settings'].get('OllamaServer', 'http://127.0.0.1:11434'))
        self.ollama_server_input.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        server_layout.addWidget(self.ollama_server_input)
        ollama_layout.addLayout(server_layout)

        # Model list
        self.ollama_model_list = QListWidget()
        self.ollama_model_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 10);
                color: white;
            }
            QListWidget::item {
                padding: 5px;
            }
        """)
        ollama_layout.addWidget(self.ollama_model_list)

        refresh_button = QPushButton("Refresh Models")
        refresh_button.clicked.connect(self.refresh_ollama_models)
        refresh_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        ollama_layout.addWidget(refresh_button)

        self.refresh_ollama_models()

        return ollama_group

    def refresh_ollama_models(self):
        self.ollama_model_list.clear()
        server_address = self.ollama_server_input.text()
        try:
            response = requests.get(f"{server_address}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    item = QListWidgetItem(model["name"])
                    self.ollama_model_list.addItem(item)
        except requests.RequestException:
            self.show_themed_message_box("Error", "Failed to fetch Ollama models", QMessageBox.Icon.Warning)

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
        self.config['Settings']['Ollama'] = str(self.ollama_checkbox.isChecked())
        self.config['Settings']['OllamaServer'] = self.ollama_server_input.text()

        for service, checkbox in self.service_checkboxes.items():
            self.config['Settings'][service] = str(checkbox.isChecked())
            self.config['Settings'][f"{service}_API_Key"] = self.api_key_inputs[service].text()

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

