import os
import sqlite3
from dotenv import load_dotenv, dotenv_values
import json

class SessionManager:
    def __init__(self):
        self.conn = sqlite3.connect('db/app.db')
        self.c = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS app_profiles
                         (id INTEGER PRIMARY KEY, data TEXT)''')
        self.conn.commit()

    def save_session(self, session_data):
        json_data = json.dumps(session_data)
        self.c.execute("INSERT OR REPLACE INTO app_profiles (id, data) VALUES (1, ?)", (json_data,))
        self.conn.commit()

    def load_session(self):
        self.c.execute("SELECT data FROM app_profiles WHERE id=1")
        row = self.c.fetchone()
        return row[0] if row else None

    def save_cookies(self, cookies):
        dotenv_file = 'env/app_cookies.env'
        with open(dotenv_file, 'w') as f:
            for cookie in cookies:
                f.write(f"{cookie['name']}={cookie['value']}\n")

    def load_cookies(self):
        dotenv_file = 'env/app_cookies.env'
        cookies = []
        if os.path.exists(dotenv_file):
            env_values = dotenv_values(dotenv_file)
            for key, value in env_values.items():
                cookies.append({'name': key, 'value': value})
        return cookies
    
    def get_session(self):
        self.c.execute("SELECT data FROM app_profiles WHERE id=1")
        row = self.c.fetchone()
        if row:
            return json.loads(row[0])
        else:
            return {}

session_manager = SessionManager()