import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
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
        # Insert default values if not present
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('decoy_url', '/decoy')")
        # panic_key default is empty (disabled) or some default
        conn.commit()

def get_config(key, default=None):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM config WHERE key=?", (key,))
        row = c.fetchone()
        return row[0] if row else default

def set_config(key, value):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def is_setup_complete():
    return get_config('setup_complete') == 'true'

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

        if secret_key:
            set_config('secret_key', secret_key)
            set_config('setup_complete', 'true')
            return redirect(url_for('index'))

    return render_template('setup.html')

@app.route('/auth', methods=['POST'])
def auth():
    email = request.form.get('email')
    name = request.form.get('name')

    if not name or not email:
        return redirect(url_for('index'))

    real_key = get_config('secret_key', 'aniwood')
    decoy_link = get_config('decoy_url', '/decoy')

    if name == real_key:
        session['authenticated'] = True
        session['user_email'] = email
        return redirect(url_for('chat'))
    else:
        # Redirect to external URL or internal route
        if decoy_link.startswith('http'):
            return redirect(decoy_link)
        return redirect(decoy_link)

@app.route('/chat')
def chat():
    if not session.get('authenticated'):
        decoy_link = get_config('decoy_url', '/decoy')
        return redirect(decoy_link if decoy_link.startswith('http') else url_for('decoy'))

    # Load history
    messages = []
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT sender, content, timestamp FROM messages ORDER BY id ASC")
        messages = [{'sender': row[0], 'content': row[1], 'timestamp': row[2]} for row in c.fetchall()]

    panic_key = get_config('panic_key', '')
    decoy_url = get_config('decoy_url', '/decoy')

    return render_template('chat.html',
                           messages=messages,
                           user_email=session.get('user_email'),
                           panic_key=panic_key,
                           decoy_url=decoy_url)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('authenticated'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        decoy_url = request.form.get('decoy_url')
        panic_key = request.form.get('panic_key')

        if secret_key:
            set_config('secret_key', secret_key)

        if decoy_url:
            set_config('decoy_url', decoy_url)

        set_config('panic_key', panic_key if panic_key else '')
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))

    current_decoy = get_config('decoy_url', '/decoy')
    current_panic = get_config('panic_key', '')

    return render_template('settings.html',
                           decoy_url=current_decoy,
                           panic_key=current_panic)

@app.route('/decoy')
def decoy():
    return render_template('decoy.html')

@socketio.on('message')
def handle_message(data):
    if not session.get('authenticated'):
        return

    content = data.get('msg')
    sender = session.get('user_email')
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
