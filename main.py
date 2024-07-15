import sys
import time
import configparser
import os
import pickle
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QStatusBar, QTabWidget, QVBoxLayout, QLabel, 
                             QPushButton, QHBoxLayout, QStackedWidget)
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QMouseEvent
from PyQt6.QtCore import Qt, QTimer, QPoint
from lib.settings import SettingsPage
from lib.session_manager import session_manager
from lib.podman import create_status_indicator, update_podman_status, update_container_status, show_container_action_dialog
from lib.theme import set_color_theme, get_color_theme
from lib.menu import MenuPanel
from lib.perfmon import PerformanceMonitor
from lib.browser import create_web_tab, load_tabs, get_tab_data
from lib.chat import LLMPage
from lib.custom_tab_widget import CustomTabWidget

APP_VERSION = "1.2.3"
BUILD_DATE = "Jul 2024"
os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'

class CasePreservingConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.pixmap = QPixmap("img/splash.png")
        self.setFixedSize(self.pixmap.size())
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        self.close()

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.dragging = False
        self.offset = QPoint()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Captain ASIC's AI Garage - Version {APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Get the theme color
        theme_color = self.config.get('Settings', 'ColorTheme', fallback='Dark Red')
        base_color, _ = get_color_theme(theme_color)

        # Set app icon
        self.setWindowIcon(QIcon("img/ASIC.ico"))

        # Set initial color theme
        self.set_color_theme(theme_color)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create title bar
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create app icon
        app_icon = QLabel()
        app_icon_pixmap = QPixmap("img/ASIC.ico").scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
        app_icon.setPixmap(app_icon_pixmap)
        title_bar_layout.addWidget(app_icon)
        
        title_label = QLabel(f"Captain ASIC's AI Garage - Version {APP_VERSION}")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        
        min_button = QPushButton("_")
        max_button = QPushButton("□")
        close_button = QPushButton("×")
        
        min_button.clicked.connect(self.showMinimized)
        max_button.clicked.connect(self.toggle_maximize)
        close_button.clicked.connect(self.close)
        
        for button in [min_button, max_button, close_button]:
            button.setFixedSize(30, 30)
            title_bar_layout.addWidget(button)
        
        main_layout.addWidget(title_bar)
        
        # Make the entire title bar draggable
        title_bar.mousePressEvent = self.mousePressEvent
        title_bar.mouseMoveEvent = self.mouseMoveEvent
        title_bar.mouseReleaseEvent = self.mouseReleaseEvent
        
        # Create content layout
        content_layout = QHBoxLayout()
        
        # Create menu panel
        self.menu_panel = MenuPanel(base_color)
        self.menu_panel.page_changed.connect(self.change_page)
        content_layout.addWidget(self.menu_panel)
        
        # Create performance gauges
        self.perf_monitor = PerformanceMonitor()
        self.menu_panel.layout().insertWidget(self.menu_panel.layout().count() - 1, self.perf_monitor)

        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addLayout(content_layout)
        
        # Create pages
        self.home_page = self.create_home_page()
        self.llm_page = LLMPage(self.config, base_color)
        self.sd_page = CustomTabWidget()
        self.tts_page = CustomTabWidget()
        self.sts_page = CustomTabWidget()
        self.settings_page = SettingsPage(self.config)
        self.settings_page.save_and_reload.connect(self.on_save_and_reload)

        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.llm_page)
        self.stacked_widget.addWidget(self.sd_page)
        self.stacked_widget.addWidget(self.tts_page)
        self.stacked_widget.addWidget(self.sts_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        # Set up central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
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
        self.status_indicators['Podman'] = create_status_indicator("Podman")
        status_layout.addWidget(self.status_indicators['Podman'])
        
        for container_name, container_id in self.config['Containers'].items():
            print(f"Creating indicator for: {container_name}")  # Debug print
            indicator = create_status_indicator(container_name)
            indicator.clicked.connect(lambda name=container_name: self.container_clicked(name))
            self.status_indicators[container_name] = indicator
            status_layout.addWidget(indicator)
        
        # Set a fixed width for the status widget to prevent scrollbar
        total_width = sum(indicator.width() for indicator in self.status_indicators.values())
        status_widget.setFixedWidth(total_width + (len(self.status_indicators) - 1) * 5)  # Add spacing
        
        self.status_bar.addPermanentWidget(status_widget)
        
        # Increase status bar height and text size
        self.status_bar.setFixedHeight(40)
        status_font = self.status_bar.font()
        status_font.setPointSize(9)
        self.status_bar.setFont(status_font)
        
        # Load saved tabs
        self.load_tabs()
        
        # Update status indicators
        self.update_status_indicators()
        
        # Set up a timer to periodically update status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status_indicators)
        self.timer.start(5000)  # Update every 5 seconds

    def on_save_and_reload(self, selected_theme):
        print(f"Reloading UI with theme: {selected_theme}")
        
        # Re-read the config file
        self.config.read('cfg/config.ini')

        # Apply the new theme
        self.apply_theme(selected_theme)

        # Reload other parts of the UI
        self.reload_ui_components()
        
        # Reload tabs
        self.load_tabs()

        # Reload other parts of the UI
        self.reload_ui_components()

        # Update the LLM page
        self.llm_page.load_local_services()

        # Force a repaint of the entire window
        self.repaint()

    def apply_theme(self, theme):
        set_color_theme(self, theme)

    def reload_ui_components(self):
        self.settings_page.refresh_tables()

        if hasattr(self, 'performance_monitor'):
            self.performance_monitor.cpu_type = self.config['Settings'].get('CPUType', 'Intel')
            self.performance_monitor.gpu_type = self.config['Settings'].get('GPUType', 'NVIDIA')

    def create_home_page(self):
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)
        home_layout.setContentsMargins(0, 0, 0, 0)  # Remove any margins
        home_image = QLabel()
        home_pixmap = QPixmap("img/splash.png")
        home_image.setPixmap(home_pixmap)
        home_image.setFixedSize(home_pixmap.size())  # Set fixed size to match the image
        home_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(home_image, alignment=Qt.AlignmentFlag.AlignCenter)
        return home_page

    def set_color_theme(self, theme):
        set_color_theme(self, theme)

    def load_tabs(self):
        try:
            with open('cfg/saved_tabs.pkl', 'rb') as f:
                saved_tabs = pickle.load(f)
        except FileNotFoundError:
            saved_tabs = {}

        # Clear existing tabs
        self.llm_page.tab_widget.clear()
        self.sd_page.clear()
        self.tts_page.clear()
        self.sts_page.clear()

        # Load tabs from config, restore saved state if available
        self.load_section_tabs('LLMs', self.llm_page.tab_widget, saved_tabs.get('llm', []))
        self.load_section_tabs('StableDiffusion', self.sd_page, saved_tabs.get('sd', []))
        self.load_section_tabs('TTS', self.tts_page, saved_tabs.get('tts', []))
        self.load_section_tabs('STS', self.sts_page, saved_tabs.get('sts', []))

    def load_section_tabs(self, section, tab_widget, saved_tabs):
        config_urls = {url: name for name, url in self.config[section].items()}
        
        # First, restore saved tabs that are still in the config
        for name, url in saved_tabs:
            if url in config_urls:
                create_web_tab(self, name, url, tab_widget)
                del config_urls[url]  # Remove this URL from the dict as it's been processed
        
        # Then, add any new tabs from the config
        for url, name in config_urls.items():
            create_web_tab(self, name, url, tab_widget)

    def reload_ui(self, theme):
        self.set_color_theme(theme)
        base_color, _ = get_color_theme(theme)
        self.menu_panel.theme_color = base_color
        self.llm_page.theme_color = base_color
        self.menu_panel.set_selected(self.menu_panel.current_index)
        if hasattr(self.llm_page, 'current_service'):
            self.llm_page.set_selected_service(self.llm_page.current_service)
        self.close()
        new_window = MainWindow(self.config)
        new_window.show()

    def update_status_indicators(self):
        update_podman_status(self.status_indicators['Podman'])
        for container_name, container_id in self.config['Containers'].items():
            print(f"Updating status for: {container_name}")  # Debug print
            update_container_status(container_name, container_id, self.status_indicators[container_name])

    def container_clicked(self, container_name):
        container_id = self.config['Containers'][container_name]
        show_container_action_dialog(self, container_name, container_id)
        self.update_status_indicators()

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def closeEvent(self, event):
        tabs_data = {
            'llm': get_tab_data(self.llm_page.tab_widget),
            'sd': get_tab_data(self.sd_page),
            'tts': get_tab_data(self.tts_page),
            'sts': get_tab_data(self.sts_page)
        }
        with open('cfg/saved_tabs.pkl', 'wb') as f:
            pickle.dump(tabs_data, f)
        with open('cfg/config.ini', 'w') as configfile:
            self.config.write(configfile)
        event.accept()

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.position().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_color_theme(self.config.get('Settings', 'ColorTheme', fallback='Dark Red'))

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
    screen = QApplication.primaryScreen().availableGeometry()
    splash_geo = splash.geometry()
    centered_pos = screen.center() - splash_geo.center()
    splash.move(centered_pos)
    print("Splash screen created")
    splash.show()
    print("Splash screen shown")
    
    # Process session data
    session_data = {'user_id': 1337, 'username': 'ai_garage'}  # example session data
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

    # Close splash screen and show main window
    splash.close()
    main_window.show()
    print("Main window shown")
    
    print("Entering main event loop")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()