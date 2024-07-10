import json
from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidget, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import QTimer
from lib.chat import AIServiceWidget
import requests

class OllamaWidget(AIServiceWidget):
    def __init__(self, config, server_address):
        self.config = config
        self.server_address = server_address
        super().__init__(None)  # Ollama doesn't need an API key

    def get_models(self):
        try:
            response = requests.get(f"{self.server_address}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except requests.RequestException:
            pass
        return []

    def setup_model_selection(self, layout):
        self.model_group = QButtonGroup(self)
        models = self.get_models()
        for i, model in enumerate(models):
            radio = QRadioButton(model)
            radio.setStyleSheet("""
                QRadioButton {
                    color: white;
                }
                QRadioButton::indicator:checked {
                    background-color: black;
                    border: 2px solid white;
                }
            """)
            self.model_group.addButton(radio, i)
            layout.addWidget(radio)
        if models:
            self.model_group.button(0).setChecked(True)
        else:
            layout.addWidget(QLabel("No models available"))

    def send_message(self):
        user_message = self.message_input.text()
        if user_message:
            if not self.current_chat_id:
                self.new_chat()

            self.new_message.emit("user", user_message)
            self.current_chat.append({"role": "user", "content": user_message})
            self.update_chat_display()
            self.message_input.clear()

            try:
                model = self.model_group.checkedButton().text()
                response = self.get_ollama_response(model, user_message)
                self.new_message.emit("assistant", response)
                self.current_chat.append({"role": "assistant", "content": response})
                self.update_chat_display()
                self.save_chat_history()
            except Exception as e:
                self.show_error_message(str(e))

    def get_ollama_response(self, model, message):
        url = f"{self.server_address}/api/chat"
        data = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": True
        }
        try:
            response = requests.post(url, json=data, stream=True)
            response.raise_for_status()
            full_response = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'message' in json_response:
                        content = json_response['message'].get('content', '')
                        full_response += content
            return full_response.strip()
        except requests.RequestException as e:
            return f"Error: {str(e)}"
        except json.JSONDecodeError as e:
            return f"Error parsing response: {str(e)}"

def setup_ollama_section(config, parent):
    ollama_group = QWidget()
    ollama_layout = QVBoxLayout(ollama_group)

    # Server address input
    server_layout = QHBoxLayout()
    server_layout.addWidget(QLabel("Server:"))
    ollama_server_input = QLineEdit(config['Settings'].get('OllamaServer', ''))
    ollama_server_input.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
    server_layout.addWidget(ollama_server_input)
    ollama_layout.addLayout(server_layout)

    # Model list
    ollama_model_list = QListWidget()
    ollama_model_list.setStyleSheet("""
        QListWidget {
            background-color: rgba(255, 255, 255, 10);
            color: white;
        }
        QListWidget::item {
            padding: 5px;
        }
    """)
    ollama_layout.addWidget(ollama_model_list)

    refresh_button = QPushButton("Refresh Models")
    refresh_button.clicked.connect(lambda: refresh_ollama_models(config, ollama_model_list))
    refresh_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
    ollama_layout.addWidget(refresh_button)

    refresh_ollama_models(config, ollama_model_list)

    return ollama_group, ollama_model_list

def refresh_ollama_models(config, model_list):
    model_list.clear()
    server_address = config['Settings'].get('OllamaServer', '')
    try:
        response = requests.get(f"{server_address}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                item = QListWidgetItem(model["name"])
                model_list.addItem(item)
    except requests.RequestException:
        pass

def show_download_popup(model_name, parent):
    popup = QMessageBox(parent)
    popup.setWindowTitle("Downloading Model")
    popup.setText(f"Downloading {model_name}...")
    popup.setIcon(QMessageBox.Icon.Information)
    popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
    popup.setStyleSheet("color: white; background-color: #2d2d2d;")
    popup.show()

    # Simulate download progress
    for i in range(101):
        QTimer.singleShot(50 * i, lambda i=i: popup.setText(f"Downloading {model_name}... {i}%"))
    
    QTimer.singleShot(5100, lambda: popup.setText(f"{model_name} downloaded successfully!"))
    QTimer.singleShot(5100, lambda: popup.setStandardButtons(QMessageBox.StandardButton.Ok))