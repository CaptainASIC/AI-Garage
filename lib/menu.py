import psutil
import platform
import subprocess
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
                             QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtCore import Qt, pyqtSignal, QUrl

APP_VERSION = "1.3.5"
BUILD_DATE = "Aug 2024"

class MenuPanel(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self, theme_color, app_version, build_date):
        super().__init__()
        self.theme_color = theme_color
        self.app_version = app_version
        self.build_date = build_date
        self.setup_ui()
        self.current_index = 0  # Track the current selected index

    def setup_ui(self):
        # Set fixed width for the entire panel
        self.setFixedWidth(200)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 10)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Button layout
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)  # Add some spacing between buttons
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

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
            button_layout.addWidget(button)

        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        # Bottom info layout
        bottom_info = QFrame()
        bottom_layout = QVBoxLayout(bottom_info)
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Add ASIC.png image (clickable)
        self.asic_label = QLabel()
        asic_pixmap = QPixmap("img/ASIC.png")
        self.asic_label.setPixmap(asic_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.asic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asic_label.mousePressEvent = self.show_about_popup
        self.asic_label.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom_layout.addWidget(self.asic_label)

        # Add system info label
        self.system_info_label = QLabel()
        self.system_info_label.setStyleSheet("color: lightgray; font-size: 10px;")
        self.system_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.system_info_label.setWordWrap(True)
        bottom_layout.addWidget(self.system_info_label)

        main_layout.addWidget(bottom_info, alignment=Qt.AlignmentFlag.AlignBottom)

        # Update system info
        self.update_system_info()

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

    def show_about_popup(self, event):
        about_text = f"""
        <h2>Captain ASIC's AI Garage</h2>
        <p>Version: {self.app_version}</p>
        <p>Build Date: {self.build_date}</p>
        <p>Thank you for using Captain ASIC's AI Garage!</p>
        <p>This application is designed to provide a comprehensive environment for AI development and experimentation.</p>
        <p>For more information, updates, and to contribute, please visit our GitHub repository:</p>
        <p><a href="https://github.com/CaptainASIC/AI-Garage">https://github.com/CaptainASIC/AI-Garage</a></p>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About Captain ASIC's AI Garage")

        # Create a QLabel with the about text
        label = QLabel(about_text)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        # Set the label as the message box's informative text
        msg_box.setInformativeText(about_text)

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.theme_color};
                color: white;
            }}
            QLabel {{
                color: white;
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid white;
                border-radius: 5px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 45);
            }}
        """)

        msg_box.exec()

    def update_system_info(self):
        cpu_info = self.get_cpu_info()
        total_memory = psutil.virtual_memory().total / (1024**3)  # in GB
        gpu_info = self.get_gpu_info()
        disk_info = self.get_disk_info()
        os_info = self.get_os_info()
        info_text = f"Detected System Specs:\n"
        info_text += f"{cpu_info}\n\n"
        info_text += f"{gpu_info}\n\n"
        info_text += f"{total_memory:.1f} GB System RAM\n\n"

        info_text += f"Disks:\n{disk_info}\n\n"
        info_text += f"{os_info}"

        self.system_info_label.setText(info_text)

    def get_cpu_info(self):
        try:
            # Try to get CPU info from lscpu
            cpu_info = subprocess.check_output("lscpu | grep 'Model name'", shell=True).decode().strip()
            cpu_model = cpu_info.split(':')[1].strip()

            # Get CPU frequency
            freq = psutil.cpu_freq()
            if freq:
                max_freq = freq.max / 1000  # Convert to GHz
            else:
                max_freq = None

            # Get CPU core count
            core_count = psutil.cpu_count(logical=False)
            thread_count = psutil.cpu_count(logical=True)

            if "AMD Ryzen" in cpu_model:
                return f"{cpu_model}\n({thread_count}Threads) @ {max_freq:.3f}GHz"
            else:
                return f"{cpu_model}\n({core_count} cores, {thread_count} threads) @ {max_freq:.3f}GHz"
        except:
            # Fallback to platform.processor() if the above method fails
            return platform.processor()
        
    def get_gpu_info(self):
        try:
            if self.is_nvidia():
                return self.get_nvidia_gpu_info()
            elif self.is_amd():
                return self.get_amd_gpu_info()
            elif self.is_intel():
                return self.get_intel_gpu_info()
            else:
                return "GPU information not available"
        except Exception as e:
            return f"Error getting GPU info: {str(e)}"

    def is_nvidia(self):
        try:
            subprocess.check_output(['nvidia-smi'])
            return True
        except:
            return False

    def is_amd(self):
        return self._check_vendor('0x1002')  # AMD vendor ID

    def is_intel(self):
        return self._check_vendor('0x8086')  # Intel vendor ID

    def _check_vendor(self, vendor_id):
        for card in ['card0', 'card1']:
            try:
                with open(f'/sys/class/drm/{card}/device/vendor', 'r') as f:
                    if f.read().strip() == vendor_id:
                        return True
            except:
                pass
        return False

    def get_nvidia_gpu_info(self):
        output = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits']).decode('utf-8').strip()
        name, memory = output.split(',')
        memory = int(memory) / 1024  # Convert to GB
        return f"NVIDIA {name.strip()} {memory:.0f}GB"

    def get_amd_gpu_info(self):
        try:
            output = subprocess.check_output(['lspci', '-v'], text=True)
            vga_devices = re.findall(r'VGA compatible controller: (.*)|Display controller: (.*)', output)
            for device in vga_devices:
                device = device[0] if device[0] else device[1]  # Choose the non-empty string
                if 'AMD' in device or 'ATI' in device:
                    # Extract model name
                    model = re.search(r'AMD/ATI\] (.*?) (\(rev .*?\))?$', device)
                    if model:
                        gpu_model = model.group(1).strip()
                        # For 7900 series, extract the specific model
                        if "Navi 31" in gpu_model:
                            # Check for XTX first, then XT
                            if "7900 XTX" in gpu_model:
                                return "AMD Radeon RX 7900 XTX 24GB"
                            elif "7900 XT" in gpu_model:
                                return "AMD Radeon RX 7900 XT 20GB"
                            else:
                                return f"AMD {gpu_model} (Memory size unavailable)"
                        
                        # Try to get memory info for other models
                        mem_info = re.search(r'Memory at .* \(([0-9]+)M\)', output)
                        if mem_info:
                            memory = int(mem_info.group(1)) // 1024  # Convert MB to GB
                            return f"AMD {gpu_model} {memory}GB"
                        else:
                            return f"AMD {gpu_model} (Memory size unavailable)"
            return "AMD GPU (details unavailable)"
        except Exception as e:
            return f"AMD GPU (Error: {str(e)})"
        

    def get_disk_info(self):
        physical_disks = {}
        partitions = psutil.disk_partitions(all=True)
        
        for partition in partitions:
            if partition.device.startswith('/dev/sd') or partition.device.startswith('/dev/nvme'):
                # Extract the base device
                if partition.device.startswith('/dev/sd'):
                    base_device = re.match(r'(/dev/sd[a-z])', partition.device).group(1)
                else:  # NVMe drive
                    base_device = re.match(r'(/dev/nvme\d+n\d+)', partition.device).group(1)
                
                if base_device not in physical_disks:
                    physical_disks[base_device] = None

        disk_info = []
        for device in physical_disks:
            try:
                # Use lsblk to get the true size of the physical drive
                output = subprocess.check_output(['lsblk', '-bdn', '-o', 'SIZE', device]).decode().strip()
                size_bytes = int(output)
                size_gb = size_bytes / (1024**3)
                
                # Get the used space of the first partition (approximation)
                for part in partitions:
                    if part.device.startswith(device):
                        try:
                            usage = psutil.disk_usage(part.mountpoint)
                            used_gb = usage.used / (1024**3)
                            break
                        except:
                            used_gb = 0
                
                # Format the output
                if size_gb > 1024:
                    size_str = f"{size_gb/1024:.2f}TB"
                    used_str = f"{used_gb/1024:.2f}TB"
                else:
                    size_str = f"{size_gb:.0f}GB"
                    used_str = f"{used_gb:.0f}GB"
                
                disk_info.append(f"{device}: {used_str}/{size_str}")
            except subprocess.CalledProcessError:
                disk_info.append(f"{device}: Size information unavailable")

        return "\n".join(disk_info) if disk_info else "Disk information unavailable"
    
    def get_os_info(self):
        try:
            # Get pretty name of OS
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
            pretty_name = re.search(r'PRETTY_NAME="(.*)"', os_release)
            if pretty_name:
                os_name = pretty_name.group(1)
            else:
                os_name = platform.system()

            # Get kernel version
            kernel_version = platform.release()

            return f"OS: {os_name}\nKernel: {kernel_version}"
        except:
            # Fallback to platform.platform() if the above method fails
            return f"OS: {platform.platform()}"