import os
import hashlib
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineDownloadRequest
from PyQt6.QtCore import QUrl, QObject, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFileDialog

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
            print(f"Download finished: {download.downloadFileName()}")
            self.download_finished.emit(download.downloadFileName())
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            print(f"Download failed: {download.downloadFileName()}")

class CustomWebEngineView(QWebEngineView):
    def createWindow(self, window_type):
        page = self.page()
        if page is not None:
            url = page.requestedUrl()
            QDesktopServices.openUrl(url)
        return None

class BrowserTab:
    def __init__(self, parent, name, url):
        self.parent = parent
        self.name = name
        self.url = url
        self.view = self.create_web_view()

    def create_web_view(self):
        profile = QWebEngineProfile(self.parent)
        profile.setPersistentStoragePath(get_cache_path(self.url))
        
        # Set up download manager
        self.download_manager = DownloadManager(self.parent)
        profile.downloadRequested.connect(self.download_manager.handle_download)
        self.download_manager.download_finished.connect(self.on_download_finished)

        page = QWebEnginePage(profile, self.parent)
        page.setUrl(QUrl(self.url))
        
        browser = CustomWebEngineView(self.parent)
        browser.setPage(page)
        return browser

    def on_download_finished(self, filename):
        print(f"Download completed: {filename}")

def create_web_tab(parent, name, url, tab_widget):
    browser_tab = BrowserTab(parent, name, url)
    tab_widget.addTab(browser_tab.view, name)
    return browser_tab

def load_tabs(parent, saved_tabs, tab_widget):
    tab_widget.clear()
    for name, url in saved_tabs:
        create_web_tab(parent, name, url, tab_widget)

def get_tab_data(tab_widget):
    tab_data = []
    for i in range(tab_widget.count()):
        browser = tab_widget.widget(i)
        tab_data.append((tab_widget.tabText(i), browser.url().toString()))
    return tab_data

def handle_new_tab_request(url):
    QDesktopServices.openUrl(url)