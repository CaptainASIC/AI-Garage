import os
import json
from PyQt6.QtNetwork import QNetworkCookie
from PyQt6.QtCore import QUrl

class CustomCookieJar:
    def __init__(self, app_name):
        self.app_name = app_name
        self.cookie_file = os.path.join(os.path.expanduser('~'), f'.{app_name}_cookies.json')
        self.cookies = self._read_from_file()

    def save_cookies(self, url, cookie_list):
        domain = QUrl(url).host()
        if domain not in self.cookies:
            self.cookies[domain] = []
        for cookie in cookie_list:
            cookie_data = cookie.toRawForm().data().decode()
            if cookie_data not in self.cookies[domain]:
                self.cookies[domain].append(cookie_data)
        self._write_to_file()

    def load_cookies(self, url):
        domain = QUrl(url).host()
        cookie_data = self.cookies.get(domain, [])
        return [QNetworkCookie.parseCookies(cookie.encode())[0] for cookie in cookie_data]

    def remove_cookie(self, url, cookie_name):
        domain = QUrl(url).host()
        if domain in self.cookies:
            self.cookies[domain] = [c for c in self.cookies[domain] if cookie_name.encode() not in c]
            self._write_to_file()

    def _write_to_file(self):
        with open(self.cookie_file, 'w') as f:
            json.dump(self.cookies, f)

    def _read_from_file(self):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r') as f:
                return json.load(f)
        return {}