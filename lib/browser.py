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

def save_tabs(llm_page, sd_page, tts_page, sts_page):
    llm_tabs = []
    sd_tabs = []
    tts_tabs = []
    sts_tabs = []

    for i in range(llm_page.count()):
        browser = llm_page.widget(i)
        llm_tabs.append((llm_page.tabText(i), browser.url().toString()))

    for i in range(sd_page.count()):
        browser = sd_page.widget(i)
        sd_tabs.append((sd_page.tabText(i), browser.url().toString()))

    for i in range(tts_page.count()):
        browser = tts_page.widget(i)
        tts_tabs.append((tts_page.tabText(i), browser.url().toString()))

    for i in range(sts_page.count()):
        browser = sts_page.widget(i)
        sts_tabs.append((sts_page.tabText(i), browser.url().toString()))

    return {'llm': llm_tabs, 'sd': sd_tabs, 'tts': tts_tabs, 'sts': sts_tabs}

def load_tabs(parent, saved_tabs, llm_page, sd_page, tts_page, sts_page):
    for name, url in saved_tabs['llm']:
        create_web_tab(parent, name, url, llm_page)

    for name, url in saved_tabs['sd']:
        create_web_tab(parent, name, url, sd_page)

    for name, url in saved_tabs['tts']:
        create_web_tab(parent, name, url, tts_page)

    for name, url in saved_tabs['sts']:
        create_web_tab(parent, name, url, sts_page)

def handle_new_tab_request(url):
    QDesktopServices.openUrl(url)