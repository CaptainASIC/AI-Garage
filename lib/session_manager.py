import os
import sqlite3
from dotenv import load_dotenv, dotenv_values
import json

class SessionManager:
    def __init__(self):
        self.db_dir = 'db'
        self.db_file = os.path.join(self.db_dir, 'app.db')
        self.env_dir = 'env'
        self.dotenv_file = os.path.join(self.env_dir, 'app_cookies.env')
        
        # Ensure the database and environment directories exist
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.env_dir, exist_ok=True)
        
        # Connect to the database (this will create the file if it doesn't exist)
        self.conn = sqlite3.connect(self.db_file)
        self.c = self.conn.cursor()
        
        # Initialize the database schema
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
        return json.loads(row[0]) if row else None

    def save_cookies(self, cookies):
        with open(self.dotenv_file, 'w') as f:
            for cookie in cookies:
                f.write(f"{cookie['name']}={cookie['value']}\n")

    def load_cookies(self):
        cookies = []
        if os.path.exists(self.dotenv_file):
            env_values = dotenv_values(self.dotenv_file)
            for key, value in env_values.items():
                cookies.append({'name': key, 'value': value})
        return cookies

    def get_session(self):
        return self.load_session() or {}

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

session_manager = SessionManager()