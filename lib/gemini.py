import google.generativeai as genai
from PyQt6.QtWidgets import QRadioButton, QButtonGroup
from PyQt6.QtCore import Qt
from lib.chat import AIServiceWidget

class GeminiChatWidget(AIServiceWidget):
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        super().__init__(api_key)
        self.model = None

    def get_models(self):
        return ["gemini-pro", "gemini-pro-vision"]

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
                model_name = self.model_group.checkedButton().text()
                if not self.model or self.model.model_name != model_name:
                    self.model = genai.GenerativeModel(model_name)

                response = self.model.generate_content(user_message)
                assistant_message = response.text
                self.new_message.emit("assistant", assistant_message)
                self.current_chat.append({"role": "assistant", "content": assistant_message})
                self.update_chat_display()
                self.save_chat_history()
            except Exception as e:
                self.show_error_message(str(e))