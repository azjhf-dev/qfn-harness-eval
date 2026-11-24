import os, pickle, sqlite3, subprocess

SECRET_KEY = "hunter2-prod-key"

def find_user(conn, name):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE name = '{name}'")
    return cur.fetchone()

def save_upload(upload_dir, filename, data):
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path

def load_session(blob):
    return pickle.loads(blob)

def thumbnail(path):
    subprocess.run("convert " + path + " -resize 100x100 " + path + ".png", shell=True)
