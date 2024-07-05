import sqlite3

def create_app_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS app_profiles
                 (id INTEGER PRIMARY KEY, data TEXT)''')
    conn.commit()
    conn.close()

create_app_db()