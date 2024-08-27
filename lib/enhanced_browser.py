import os
import hashlib
from PyQt6.QtWidgets import QTabWidget, QMenu, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineDownloadRequest
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QDesktopServices

def get_cache_path(url):
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(cache_dir, url_hash)

class DownloadManager(QObject):
    download_finished = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def handle_download(self, download):
        default_path = QFileDialog.getSaveFileName(None, "Save File", download.suggestedFileName())[0]
        if default_path:
            download.setDownloadDirectory(os.path.dirname(default_path))
            download.setDownloadFileName(os.path.basename(default_path))
            download.stateChanged.connect(lambda state: self.on_download_state_changed(state, download))
            download.accept()
        else:
            download.cancel()

    def on_download_state_changed(self, state, download):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.download_finished.emit(download.downloadFileName())
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            # You might want to emit a signal for download failure here
            pass

class EnhancedWebEnginePage(QWebEnginePage):
    new_tab_requested = pyqtSignal(QWebEnginePage)

    def __init__(self, profile, parent):
        super().__init__(profile, parent)

    def createWindow(self, _):
        new_page = EnhancedWebEnginePage(self.profile(), self.parent())
        self.new_tab_requested.emit(new_page)
        return new_page

class EnhancedWebEngineView(QWebEngineView):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.page = EnhancedWebEnginePage(profile, self)
        self.setPage(self.page)
        self.page.new_tab_requested.connect(self.handle_new_tab_requested)

    def handle_new_tab_requested(self, new_page):
        tab_widget = self.find_tab_widget()
        if tab_widget:
            tab_widget.create_new_tab_with_page(new_page)

    def find_tab_widget(self):
        parent = self.parent()
        while parent:
            if isinstance(parent, EnhancedTabWidget):
                return parent
            parent = parent.parent()
        return None

class EnhancedTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

        self.download_manager = DownloadManager(self)

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
        if isinstance(widget, QWebEngineView):
            widget.reload()

    def open_in_external_browser(self, index):
        widget = self.widget(index)
        if isinstance(widget, QWebEngineView):
            url = widget.url().toString()
            QDesktopServices.openUrl(QUrl(url))

    def close_tab(self, index):
        self.removeTab(index)

    def create_web_tab(self, name, url):
        profile = QWebEngineProfile(self)
        profile.setPersistentStoragePath(get_cache_path(url))
        profile.downloadRequested.connect(self.download_manager.handle_download)

        web_view = EnhancedWebEngineView(profile, self)
        web_view.setUrl(QUrl(url))

        index = self.addTab(web_view, name)
        self.setCurrentIndex(index)
        return web_view

    def create_new_tab_with_page(self, new_page):
        new_view = EnhancedWebEngineView(new_page.profile(), self)
        new_view.setPage(new_page)
        index = self.addTab(new_view, "New Tab")
        self.setCurrentIndex(index)
        return new_view

def get_tab_data(tab_widget):
    tab_data = []
    for i in range(tab_widget.count()):
        web_view = tab_widget.widget(i)
        if isinstance(web_view, QWebEngineView):
            tab_data.append((tab_widget.tabText(i), web_view.url().toString()))
    return tab_data