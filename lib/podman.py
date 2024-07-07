import subprocess
from PyQt6.QtWidgets import QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal

class ClickableStatusIndicator(QLabel):
    clicked = pyqtSignal(str)  # Signal to emit the container name when clicked

    def __init__(self, name):
        super().__init__(name)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(100, 30)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ff4d4d;
                border-radius: 10px;
                padding: 2px;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.text())

def create_status_indicator(name):
    print(f"Creating status indicator for: {name}")  # Debug print
    return ClickableStatusIndicator(name)

def update_podman_status(status_widget):
    try:
        subprocess.run(["podman", "info"], check=True, capture_output=True)
        set_status_color(status_widget, "green")
    except subprocess.CalledProcessError:
        set_status_color(status_widget, "red")

def update_container_status(container_name, container_id, status_widget):
    try:
        print(f"Checking status for container: {container_name}")  # Debug print
        result = subprocess.run(["podman", "inspect", "-f", "{{.State.Status}}", container_id], 
                                check=True, capture_output=True, text=True)
        status = result.stdout.strip()
        print(f"Status for {container_name}: {status}")  # Debug print
        if status == "running":
            set_status_color(status_widget, "green")
        elif status == "exited":
            set_status_color(status_widget, "red")
        else:
            set_status_color(status_widget, "yellow")
    except subprocess.CalledProcessError as e:
        print(f"Error checking status for {container_name}: {e}")  # Debug print
        # Check if the exit status is 125
        if e.returncode == 125:
            set_status_color(status_widget, "red")
        else:
            set_status_color(status_widget, "yellow")

def set_status_color(widget, color):
    widget.setStyleSheet(f"""
        QLabel {{
            background-color: {color};
            color: black;
            border: 2px solid #ff4d4d;
            border-radius: 10px;
            padding: 2px;
        }}
    """)

def container_action(container_id, action):
    try:
        if action == "start":
            subprocess.run(["podman", "start", container_id], check=True)
        elif action == "stop":
            subprocess.run(["podman", "stop", container_id], check=True)
        elif action == "restart":
            subprocess.run(["podman", "restart", container_id], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error performing {action} on container {container_id}: {e}")
        return False

def show_container_action_dialog(parent, container_name, container_id):
    status = get_container_status(container_id)
    
    if status == "running":
        actions = ["Stop", "Restart"]
    elif status == "exited":
        actions = ["Start", "Restart"]
    else:
        actions = ["Start", "Stop", "Restart"]

    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(f"Container: {container_name}")
    msg_box.setText(f"Current status: {status}\nWhat action would you like to perform?")
    
    for action in actions:
        msg_box.addButton(action, QMessageBox.ButtonRole.ActionRole)
    
    cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
    
    msg_box.exec()
    
    clicked_button = msg_box.clickedButton()
    
    if clicked_button != cancel_button:
        action = clicked_button.text().lower()
        success = container_action(container_id, action)
        if success:
            QMessageBox.information(parent, "Success", f"Successfully performed {action} on {container_name}")
        else:
            QMessageBox.warning(parent, "Error", f"Failed to {action} {container_name}")

def get_container_status(container_id):
    try:
        result = subprocess.run(["podman", "inspect", "-f", "{{.State.Status}}", container_id], 
                                check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"