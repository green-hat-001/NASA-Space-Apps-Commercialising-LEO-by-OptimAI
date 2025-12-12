import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'super_secret_session_key'
socketio = SocketIO(app, async_mode='eventlet')
DB_FILE = "chat.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, content TEXT, timestamp TEXT)''')
        conn.commit()

def is_setup_complete():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM config WHERE key='setup_complete'")
        row = c.fetchone()
        return row and row[0] == 'true'

def get_secret_key():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM config WHERE key='secret_key'")
        row = c.fetchone()
        return row[0] if row else "aniwood" # Default fallback if not set but setup marked true

@app.route('/')
def index():
    if not is_setup_complete():
        return render_template('login.html', show_setup=True)
    return render_template('login.html', show_setup=False)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if is_setup_complete():
        return redirect(url_for('index'))

    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        # email = request.form.get('email') # Not strictly needed for config, but user might enter it.
        
        if secret_key:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('secret_key', ?)", (secret_key,))
                c.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('setup_complete', 'true')")
                conn.commit()
            return redirect(url_for('index'))

    return render_template('setup.html')

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    name = request.form.get('name')

    if not name or not email:
        return redirect(url_for('index'))

    real_key = get_secret_key()

    if name == real_key:
        session['authenticated'] = True
        session['user_email'] = email
        session['user_name'] = name # This is the key, but also their "name" in this context?
        # Actually, if the name IS the key, then everyone appears as the Key?
        # The prompt says "Name (which acts as the password)".
        # But usually chat participants have names.
        # Maybe the "Name" field IS just the password field labeled "Name"?
        # "If the name entered is the secret key... user is authenticated"
        # "To provide a persistent, real-time chat between two or more parties"
        # If I type "aniwood", do I show up as "aniwood"?
        # Use Email as the display name?
        # "The app requires two pieces of information: an Email and a Name"
        # Let's use Email as the sender name in chat, or maybe part of the email.
        return redirect(url_for('chat'))
    else:
        return redirect(url_for('decoy'))

@app.route('/chat')
def chat():
    if not session.get('authenticated'):
        return redirect(url_for('decoy'))

    # Load history
    messages = []
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT sender, content, timestamp FROM messages ORDER BY id ASC")
        messages = [{'sender': row[0], 'content': row[1], 'timestamp': row[2]} for row in c.fetchall()]
        
    return render_template('chat.html', messages=messages, user_email=session.get('user_email'))

@app.route('/decoy')
def decoy():
    return render_template('decoy.html')

@socketio.on('message')
def handle_message(data):
    if not session.get('authenticated'):
        return

    content = data.get('msg')
    sender = session.get('user_email') # Use email as sender identifier
    timestamp = datetime.now().strftime('%H:%M')

    if content:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender, content, timestamp) VALUES (?, ?, ?)",
                      (sender, content, timestamp))
            conn.commit()

        emit('message', {'sender': sender, 'content': content, 'timestamp': timestamp}, broadcast=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
