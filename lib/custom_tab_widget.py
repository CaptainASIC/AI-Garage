from PyQt6.QtWidgets import QTabWidget, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QAction
from PyQt6.QtCore import QUrl

class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        index = self.tabBar().tabAt(position)
        if index != -1:
            menu = QMenu()
            reload_action = QAction("Reload", self)
            open_external_action = QAction("Open in External Browser", self)
            
            menu.addAction(reload_action)
            menu.addAction(open_external_action)
            
            reload_action.triggered.connect(lambda: self.reload_tab(index))
            open_external_action.triggered.connect(lambda: self.open_in_external_browser(index))
            
            menu.exec(self.mapToGlobal(position))

    def reload_tab(self, index):
        widget = self.widget(index)
        if hasattr(widget, 'reload'):
            widget.reload()

    def open_in_external_browser(self, index):
        widget = self.widget(index)
        if hasattr(widget, 'url'):
            url = widget.url().toString()
            QDesktopServices.openUrl(QUrl(url))