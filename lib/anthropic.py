import anthropic
from PyQt6.QtWidgets import QRadioButton, QButtonGroup
from PyQt6.QtCore import Qt
from lib.chat import AIServiceWidget

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