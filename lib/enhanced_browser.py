import os
import hashlib
from PyQt6.QtWidgets import QTabWidget, QMenu, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineDownloadRequest
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtNetwork import QNetworkCookie
from lib.custom_cookie_jar import CustomCookieJar


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
    def __init__(self, profile, parent):
        super().__init__(profile, parent)

    def certificateError(self, error):
        # Ignore certificate errors (use with caution!)
        return True

class EnhancedWebEngineView(QWebEngineView):
    def __init__(self, profile, cookie_jar, parent=None):
        super().__init__(parent)
        self.cookie_jar = cookie_jar
        self.page = EnhancedWebEnginePage(profile, self)
        self.setPage(self.page)
        self.loadFinished.connect(self.on_load_finished)

        # Set up cookie handling
        self.cookie_store = self.page.profile().cookieStore()
        self.cookie_store.cookieAdded.connect(self.on_cookie_added)
        self.cookie_store.cookieRemoved.connect(self.on_cookie_removed)

    def createWindow(self, window_type):
        new_view = EnhancedWebEngineView(self.page.profile(), self.cookie_jar, self.parent())
        self.parent().addTab(new_view, "New Tab")
        return new_view

    def on_load_finished(self, ok):
        if ok:
            print(f"Page loaded: {self.url().toString()}")

    def on_cookie_added(self, cookie):
        url = QUrl(f"http://{cookie.domain()}")
        self.cookie_jar.save_cookies(url.toString(), [cookie])

    def on_cookie_removed(self, cookie):
        url = QUrl(f"http://{cookie.domain()}")
        cookies = self.cookie_jar.load_cookies(url.toString())
        cookies = [c for c in cookies if c.name() != cookie.name()]
        self.cookie_jar.save_cookies(url.toString(), cookies)

    def setUrl(self, url):
        cookies = self.cookie_jar.load_cookies(url.toString())
        for cookie in cookies:
            self.cookie_store.setCookie(cookie, url)
        super().setUrl(url)

class EnhancedTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

        self.download_manager = DownloadManager(self)
        self.cookie_jar = CustomCookieJar("AI-Garage")
        
        # Create a profile
        self.profile = QWebEngineProfile("AI-Garage", self)
        self.profile.downloadRequested.connect(self.download_manager.handle_download)

    def create_web_tab(self, name, url):
        web_view = EnhancedWebEngineView(self.profile, self.cookie_jar, self)
        web_view.setUrl(QUrl(url))

        index = self.addTab(web_view, name)
        self.setCurrentIndex(index)
        return web_view

    def create_persistent_profile(self, retries=5):
        persistent_path = get_persistent_storage_path()
        for attempt in range(retries):
            try:
                self.persistent_profile = QWebEngineProfile("AI-Garage", self)
                self.persistent_profile.setPersistentStoragePath(persistent_path)
                self.persistent_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
                self.persistent_profile.downloadRequested.connect(self.download_manager.handle_download)
                
                # Force the profile to initialize its databases
                self.persistent_profile.httpCacheType()
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(1)  # Wait for a second before retrying
                else:
                    print("Failed to create persistent profile after multiple attempts.")
                    # Fallback to a non-persistent profile
                    self.persistent_profile = QWebEngineProfile(self)

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
        web_view = EnhancedWebEngineView(self.profile, self.cookie_jar, self)
        web_view.setUrl(QUrl(url))

        index = self.addTab(web_view, name)
        self.setCurrentIndex(index)
        return web_view

    def create_new_tab_with_page(self, new_page):
        new_view = EnhancedWebEngineView(self.persistent_profile, self)
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