import sys
import time
import configparser
import subprocess
import os
import hashlib
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplashScreen, QStatusBar, QTabWidget, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QHBoxLayout, QStackedWidget, QFormLayout, QLineEdit, QScrollArea)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from lib.settings import SettingsPage
from lib.session_manager import session_manager

APP_VERSION = "1.0"
BUILD_DATE = "Jul 2024"

def get_cache_path(url):
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(cache_dir, url_hash)

class CasePreservingConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__(QPixmap("img/splash.png"))
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

    def drawContents(self, painter: QPainter):
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Loading...")

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Captain ASIC's AI Garage - Version {APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set app icon
        self.setWindowIcon(QIcon("img/ASIC.ico"))

        # Set initial color theme
        self.set_color_theme(self.config.get('Settings', 'ColorTheme', fallback='Dark Red'))
        
        # Create main layout
        main_layout = QHBoxLayout()
        
        # Create menu panel
        menu_panel = QWidget()
        menu_layout = QVBoxLayout(menu_panel)
        self.home_button = QPushButton("Home")
        self.llm_button = QPushButton("LLMs")
        self.sd_button = QPushButton("Stable Diffusion")
        self.settings_button = QPushButton("Settings")
        
        for button in [self.home_button, self.llm_button, self.sd_button, self.settings_button]:
            button.setFixedSize(150, 50)
            menu_layout.addWidget(button)
        
        menu_layout.addStretch()

        # Add ASIC.png image
        asic_label = QLabel()
        asic_pixmap = QPixmap("img/ASIC.png")
        asic_label.setPixmap(asic_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        asic_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        menu_layout.addWidget(asic_label)

        main_layout.addWidget(menu_panel)
        
        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create home page
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)
        home_image = QLabel()
        home_image.setPixmap(QPixmap("img/splash.png").scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio))
        home_layout.addWidget(home_image, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(home_page)
        
        # Create LLM page
        llm_page = QTabWidget()
        self.stacked_widget.addWidget(llm_page)
        
        # Create Stable Diffusion page
        sd_page = QTabWidget()
        self.stacked_widget.addWidget(sd_page)
        
        # Set up central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Debug print
        print("Containers in config:")
        for container_name, container_value in self.config['Containers'].items():
            print(f"  {container_name} = {container_value}")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create a widget to hold all status indicators
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setSpacing(5)  # Reduce spacing between indicators
        status_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Create status indicators dynamically
        self.status_indicators = {}
        self.status_indicators['Podman'] = self.create_status_indicator("Podman")
        status_layout.addWidget(self.status_indicators['Podman'])
        
        for container_name in self.config['Containers']:
            print(f"Creating indicator for: {container_name}")  # Debug print
            self.status_indicators[container_name] = self.create_status_indicator(container_name)
            status_layout.addWidget(self.status_indicators[container_name])
        
        # Set a fixed width for the status widget to prevent scrollbar
        total_width = sum(indicator.width() for indicator in self.status_indicators.values())
        status_widget.setFixedWidth(total_width + (len(self.status_indicators) - 1) * 5)  # Add spacing
        
        self.status_bar.addPermanentWidget(status_widget)
        
        # Increase status bar height and text size
        self.status_bar.setFixedHeight(40)
        status_font = self.status_bar.font()
        status_font.setPointSize(9)
        self.status_bar.setFont(status_font)
        
        # Set up LLM tabs
        for key, url in self.config['LLMs'].items():
            self.create_web_tab(key, url, llm_page)
        
        # Set up Stable Diffusion tabs
        for key, url in self.config['StableDiffusion'].items():
            self.create_web_tab(key, url, sd_page)
        
        # Create Settings page
        self.settings_page = SettingsPage(self.config)
        self.settings_page.save_and_reload.connect(self.reload_ui)
        self.stacked_widget.addWidget(self.settings_page)
        
        # Connect buttons
        self.home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.llm_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.sd_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # Update status indicators
        self.update_status_indicators()
        
        # Set up a timer to periodically update status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status_indicators)
        self.timer.start(5000)  # Update every 5 seconds

    def set_color_theme(self, theme):
        color_map = {
            "Dark Red": ("#8B0000", "#4B0000"),
            "Dark Blue": ("#00008B", "#00004B"),
            "Dark Green": ("#006400", "#003400"),
            "Dark Purple": ("#4B0082", "#250041"),
            "Blackout": ("#000000", "#000000")
        }
        base_color, gradient_start = color_map.get(theme, ("#8B0000", "#4B0000"))  # Default to Dark Red

        # Set gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(gradient_start))
        gradient.setColorAt(1, QColor(0, 0, 0))  # Black at bottom
        
        palette = self.palette()
        palette.setBrush(self.backgroundRole(), gradient)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # Update StyleSheet
        self.setStyleSheet(f"""
            QMainWindow, QTabWidget, QStatusBar, QWidget {{
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
        """)

    def reload_ui(self, theme):
        self.set_color_theme(theme)
        self.setup_ui()
        self.update()

    def create_web_tab(self, name, url, tab_widget):
        profile = QWebEngineProfile(tab_widget)
        profile.setPersistentStoragePath(get_cache_path(url))
        
        page = QWebEnginePage(profile, tab_widget)
        page.setUrl(QUrl(url))
        
        browser = QWebEngineView(tab_widget)
        browser.setPage(page)
        
        tab_widget.addTab(browser, name)  # Use the key (name) as the tab title

    def create_status_indicator(self, name):
        print(f"Creating status indicator for: {name}")  # Debug print
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedSize(100, 30)  # Reduced width
        label.setStyleSheet("""
            QLabel {
                border: 2px solid #ff4d4d;
                border-radius: 10px;
                padding: 2px;
            }
        """)
        return label

    def update_status_indicators(self):
        self.update_podman_status()
        for container_name in self.config['Containers']:
            print(f"Updating status for: {container_name}")  # Debug print
            self.update_container_status(container_name, self.status_indicators[container_name])

    def update_podman_status(self):
        try:
            subprocess.run(["podman", "info"], check=True, capture_output=True)
            self.set_status_color(self.status_indicators['Podman'], "green")
        except subprocess.CalledProcessError:
            self.set_status_color(self.status_indicators['Podman'], "red")

    def update_container_status(self, container_name, status_widget):
        try:
            print(f"Checking status for container: {container_name}")  # Debug print
            result = subprocess.run(["podman", "inspect", "-f", "{{.State.Status}}", self.config['Containers'][container_name]], 
                                    check=True, capture_output=True, text=True)
            status = result.stdout.strip()
            print(f"Status for {container_name}: {status}")  # Debug print
            if status == "running":
                self.set_status_color(status_widget, "green")
            elif status == "exited":
                self.set_status_color(status_widget, "red")
            else:
                self.set_status_color(status_widget, "yellow")
        except subprocess.CalledProcessError as e:
            print(f"Error checking status for {container_name}: {e}")  # Debug print
            # Check if the exit status is 125
            if e.returncode == 125:
                self.set_status_color(status_widget, "red")
            else:
                self.set_status_color(status_widget, "yellow")

    def set_status_color(self, widget, color):
        widget.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: black;
                border: 2px solid #ff4d4d;
                border-radius: 10px;
                padding: 2px;
            }}
        """)

    def closeEvent(self, event):
        with open('cfg/config.ini', 'w') as configfile:
            self.config.write(configfile)
        event.accept()

def main():
    print("Starting application...")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("img/ASIC.ico"))  # Set app icon for the entire application
    print("QApplication created")
    
    # Read config
    config = CasePreservingConfigParser()
    config.read('cfg/config.ini')

    # Show splash screen
    splash = SplashScreen()
    print("Splash screen created")
    splash.show()
    print("Splash screen shown")
    

    # Process session data
    session_data = {'user_id': 123, 'username': 'john'}  # example session data
    cookies = [{'name': 'cookie1', 'value': 'value1'}, {'name': 'cookie2', 'value': 'value2'}]  # example cookies

    session_manager.save_session(session_data)
    session_manager.save_cookies(cookies)

    session_data = session_manager.load_session()
    if session_data:
        # restore session data
        print("Restored session:", session_data)

    cookies = session_manager.load_cookies()
    if cookies:
        # restore cookies
        print("Restored cookies:", cookies)

    # Simulate loading time
    start_time = time.time()
    while time.time() - start_time < 2:
        app.processEvents()
    print("Loading time simulated")
    
    # Create and show main window
    main_window = MainWindow(config)
    print("Main window created")
    main_window.show()
    print("Main window shown")
    
    # Close splash screen
    splash.finish(main_window)
    print("Splash screen finished")
    
    print("Entering main event loop")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()