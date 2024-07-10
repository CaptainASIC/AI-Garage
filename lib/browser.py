import os
import hashlib
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

def get_cache_path(url):
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(cache_dir, url_hash)

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
        
        page = QWebEnginePage(profile, self.parent)
        page.setUrl(QUrl(self.url))
        
        browser = CustomWebEngineView(self.parent)
        browser.setPage(page)
        
        return browser

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