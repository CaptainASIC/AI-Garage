import anthropic
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, 
                             QLineEdit, QPushButton, QSplitter, QFileDialog, QLabel, 
                             QTabWidget, QStackedWidget, QMessageBox, QInputDialog, QListWidgetItem,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPalette, QColor
from lib.browser import create_web_tab
import json
import uuid

class TransparentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

class AIServiceWidget(TransparentWidget):
    new_message = pyqtSignal(str, str)  # (role, content)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key
        self.current_chat_id = None
        self.current_chat = []
        self.chat_history = {}
        self.setup_ui()
        self.load_chat_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Select Model:"))
        self.setup_model_selection(model_layout)
        layout.addLayout(model_layout)

        chat_layout = QHBoxLayout()

        # Chat History (1/5 width)
        history_widget = TransparentWidget()
        history_layout = QVBoxLayout(history_widget)
        new_chat_button = QPushButton("New Chat")
        new_chat_button.clicked.connect(self.new_chat)
        new_chat_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_chat)
        self.history_list.setStyleSheet("color: white; background-color: transparent;")
        history_layout.addWidget(new_chat_button)
        history_layout.addWidget(self.history_list)

        # Chat Area (4/5 width)
        chat_area = TransparentWidget()
        chat_area_layout = QVBoxLayout(chat_area)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 10);")

        input_area = TransparentWidget()
        input_layout = QHBoxLayout(input_area)

        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")

        self.attach_button = QPushButton(QIcon("img/attach.png"), "")
        self.attach_button.clicked.connect(self.attach_file)
        self.attach_button.setStyleSheet("background-color: rgba(255, 255, 255, 30);")

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 30);")

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.attach_button)
        input_layout.addWidget(self.send_button)

        chat_area_layout.addWidget(self.chat_display)
        chat_area_layout.addWidget(input_area)

        # Add widgets to chat layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(history_widget)
        splitter.addWidget(chat_area)
        splitter.setStretchFactor(0, 1)  # History column (1/5 width)
        splitter.setStretchFactor(1, 4)  # Chat area (4/5 width)

        chat_layout.addWidget(splitter)
        layout.addLayout(chat_layout)

    def setup_model_selection(self, layout):
        raise NotImplementedError("Subclasses must implement setup_model_selection method")

    def get_models(self):
        raise NotImplementedError("Subclasses must implement get_models method")

    def send_message(self):
        raise NotImplementedError("Subclasses must implement send_message method")

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach File")
        if file_path:
            self.message_input.setText(f"Attached file: {file_path}")

    def update_chat_display(self):
        self.chat_display.clear()
        for message in self.current_chat:
            role = message["role"].capitalize()
            content = message["content"]
            self.chat_display.append(f"<font color='white'><b>{role}:</b> {content}</font><br><br>")

    def load_chat(self, item):
        self.current_chat_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_chat = self.chat_history[self.current_chat_id]['messages']
        self.update_chat_display()

    def new_chat(self):
        chat_name, ok = QInputDialog.getText(self, "New Chat", "Enter a name for the new chat:")
        if ok and chat_name:
            self.current_chat_id = str(uuid.uuid4())
            self.chat_history[self.current_chat_id] = {'name': chat_name, 'messages': []}
            self.current_chat = []
            self.update_chat_display()
            self.update_history_list()
            self.save_chat_history()

    def update_history_list(self):
        self.history_list.clear()
        for chat_id, chat_data in self.chat_history.items():
            item = QListWidgetItem(chat_data['name'])
            item.setData(Qt.ItemDataRole.UserRole, chat_id)
            self.history_list.addItem(item)

    def load_chat_history(self):
        try:
            with open(f'history/{self.__class__.__name__}_history.json', 'r') as f:
                self.chat_history = json.load(f)
            self.update_history_list()
        except FileNotFoundError:
            self.chat_history = {}

    def save_chat_history(self):
        if self.current_chat_id:
            self.chat_history[self.current_chat_id]['messages'] = self.current_chat
        with open(f'history/{self.__class__.__name__}_history.json', 'w') as f:
            json.dump(self.chat_history, f)
        self.update_history_list()

    def show_error_message(self, message):
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Icon.Warning)
        error_box.setText("An error occurred")
        error_box.setInformativeText(message)
        error_box.setWindowTitle("Error")
        error_box.exec()

class ClaudeChatWidget(AIServiceWidget):
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        super().__init__(api_key)

    def get_models(self):
        return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-2.1", "claude-2.0"]

    def setup_model_selection(self, layout):
        self.model_group = QButtonGroup(self)
        for i, model in enumerate(self.get_models()):
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
        self.model_group.button(0).setChecked(True)

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
                response = self.client.messages.create(
                    model=model,
                    max_tokens=1000,
                    messages=self.current_chat
                )
                assistant_message = response.content[0].text
                self.new_message.emit("assistant", assistant_message)
                self.current_chat.append({"role": "assistant", "content": assistant_message})
                self.update_chat_display()
                self.save_chat_history()
            except Exception as e:
                self.show_error_message(str(e))

class ChatGPTWidget(AIServiceWidget):
    def __init__(self, api_key):
        self.client = None  # Initialize OpenAI client here
        super().__init__(api_key)

    def get_models(self):
        return ["gpt-4-1106-preview", "gpt-4", "gpt-3.5-turbo-1106", "gpt-3.5-turbo"]

    def setup_model_selection(self, layout):
        self.model_group = QButtonGroup(self)
        for i, model in enumerate(self.get_models()):
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
        self.model_group.button(0).setChecked(True)

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
                # Implement ChatGPT API call here
                assistant_message = "ChatGPT response not implemented yet."
                self.new_message.emit("assistant", assistant_message)
                self.current_chat.append({"role": "assistant", "content": assistant_message})
                self.update_chat_display()
                self.save_chat_history()
            except Exception as e:
                self.show_error_message(str(e))

class LLMPage(TransparentWidget):
    def __init__(self, config, theme_color):
        super().__init__()
        self.config = config
        self.theme_color = theme_color
        self.current_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # AI Service Buttons
        button_layout = QHBoxLayout()
        self.ollama_button = QPushButton("Ollama")
        self.local_services_button = QPushButton("Local Services")
        self.claude_button = QPushButton("Claude")
        self.chatgpt_button = QPushButton("ChatGPT")
        for button in [self.ollama_button, self.local_services_button, self.claude_button, self.chatgpt_button]:
            button.setStyleSheet(f"color: white; background-color: rgba(255, 255, 255, 30); border: 1px solid {self.theme_color}; border-radius: 15px; padding: 5px;")
        button_layout.addWidget(self.ollama_button)
        button_layout.addWidget(self.local_services_button)
        button_layout.addWidget(self.claude_button)
        button_layout.addWidget(self.chatgpt_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Connect button clicks
        self.ollama_button.clicked.connect(lambda: self.set_selected_service("Ollama"))
        self.local_services_button.clicked.connect(lambda: self.set_selected_service("Local Services"))
        self.claude_button.clicked.connect(lambda: self.set_selected_service("Claude"))
        self.chatgpt_button.clicked.connect(lambda: self.set_selected_service("ChatGPT"))

        # Tab widget for local services
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 1px solid white; }"
                                      "QTabBar::tab { color: white; background-color: rgba(255, 255, 255, 30); }"
                                      "QTabBar::tab:selected { background-color: rgba(255, 255, 255, 60); }")
        layout.addWidget(self.tab_widget)

        # Stacked widget for AI services
        self.ai_services_stack = QStackedWidget()
        layout.addWidget(self.ai_services_stack)

        # Add Ollama widget
        from lib.ollama import OllamaWidget
        ollama_server = self.config['Settings'].get('OllamaServer', '')
        self.ollama_chat = OllamaWidget(self.config, ollama_server)
        self.ai_services_stack.addWidget(self.ollama_chat)

        # Add Claude widget
        claude_api_key = self.config['Settings'].get('Claude_API_Key', '')
        if self.config['Settings'].getboolean('Claude', fallback=False) and claude_api_key:
            self.claude_chat = ClaudeChatWidget(claude_api_key)
            self.ai_services_stack.addWidget(self.claude_chat)
        else:
            self.ai_services_stack.addWidget(QLabel("Claude is not enabled or API key is missing."))

        # Add ChatGPT widget
        chatgpt_api_key = self.config['Settings'].get('ChatGPT_API_Key', '')
        if self.config['Settings'].getboolean('ChatGPT', fallback=False) and chatgpt_api_key:
            self.chatgpt_chat = ChatGPTWidget(chatgpt_api_key)
            self.ai_services_stack.addWidget(self.chatgpt_chat)
        else:
            self.ai_services_stack.addWidget(QLabel("ChatGPT is not enabled or API key is missing."))

        # Show Ollama by default
        self.set_selected_service("Ollama")

    def set_selected_service(self, service):
        self.current_service = service
        buttons = [self.ollama_button, self.local_services_button, self.claude_button, self.chatgpt_button]
        for button in buttons:
            if button.text() == service:
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
        
        # Call the appropriate show method based on the selected service
        if service == "Ollama":
            self.show_ollama()
        elif service == "Local Services":
            self.show_local_services()
        elif service == "Claude":
            self.show_claude()
        elif service == "ChatGPT":
            self.show_chatgpt()

    def load_local_services(self):
        # Clear existing tabs first
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # Add tabs for each LLM service
        for key, url in self.config['LLMs'].items():
            create_web_tab(self, key, url, self.tab_widget)

        # Set the first tab as active if it exists
        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(0)

    def show_ollama(self):
        self.tab_widget.hide()
        self.ai_services_stack.setCurrentWidget(self.ollama_chat)
        self.ai_services_stack.show()

    def show_claude(self):
        self.tab_widget.hide()
        self.ai_services_stack.setCurrentIndex(1)  # Assuming Claude is the second widget
        self.ai_services_stack.show()

    def show_chatgpt(self):
        self.tab_widget.hide()
        self.ai_services_stack.setCurrentIndex(2)  # Assuming ChatGPT is the third widget
        self.ai_services_stack.show()

    def show_local_services(self):
        self.ai_services_stack.hide()
        self.tab_widget.show()

    def get_tab_data(self):
        tab_data = []
        for i in range(self.tab_widget.count()):
            browser = self.tab_widget.widget(i)
            tab_data.append((self.tab_widget.tabText(i), browser.url().toString()))
        return tab_data

    def load_tabs(self, saved_tabs):
        self.tab_widget.clear()
        for name, url in saved_tabs:
            create_web_tab(self, name, url, self.tab_widget)