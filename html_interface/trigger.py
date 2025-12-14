import sqlite3
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_session_key'
socketio = SocketIO(app, async_mode='eventlet')
DB_FILE = "chat.db"
UPLOAD_FOLDER = 'html_interface/static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')

        # Check if messages table has new columns, if not, recreate (simplest for this hackathon)
        # Actually, let's just use try/except to add columns or create table
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, content TEXT, timestamp TEXT,
                      msg_type TEXT DEFAULT 'text', media_path TEXT)''')

        # Create users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (email TEXT PRIMARY KEY, first_seen TEXT, last_seen TEXT)''')

        # Insert default values if not present
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('decoy_url', '/decoy')")
        conn.commit()

    # Simple migration attempt: try to add columns if they don't exist
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("ALTER TABLE messages ADD COLUMN msg_type TEXT DEFAULT 'text'")
            c.execute("ALTER TABLE messages ADD COLUMN media_path TEXT")
            conn.commit()
    except sqlite3.OperationalError:
        pass # Columns likely exist

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

        # Update user profile
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT email FROM users WHERE email=?", (email,))
            if c.fetchone():
                c.execute("UPDATE users SET last_seen=? WHERE email=?", (now, email))
            else:
                c.execute("INSERT INTO users (email, first_seen, last_seen) VALUES (?, ?, ?)", (email, now, now))
            conn.commit()

        return redirect(url_for('chat'))
    else:
        if decoy_link.startswith('http'):
            return redirect(decoy_link)
        return redirect(decoy_link)

@app.route('/chat')
def chat():
    if not session.get('authenticated'):
        decoy_link = get_config('decoy_url', '/decoy')
        return redirect(decoy_link if decoy_link.startswith('http') else url_for('decoy'))

    messages = []
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT sender, content, timestamp, msg_type, media_path FROM messages ORDER BY id ASC")
        messages = [{'sender': row[0], 'content': row[1], 'timestamp': row[2],
                     'type': row[3], 'media_path': row[4]} for row in c.fetchall()]

    panic_key = get_config('panic_key', '')
    decoy_url = get_config('decoy_url', '/decoy')

    return render_template('chat.html',
                           messages=messages,
                           user_email=session.get('user_email'),
                           panic_key=panic_key,
                           decoy_url=decoy_url)

@app.route('/gallery')
def gallery():
    if not session.get('authenticated'):
        return redirect(url_for('index'))

    images = []
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT sender, timestamp, media_path FROM messages WHERE msg_type='image' ORDER BY id DESC")
        images = [{'sender': row[0], 'timestamp': row[1], 'url': row[2]} for row in c.fetchall()]

    return render_template('gallery.html', images=images)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        url = url_for('static', filename=f"uploads/{filename}")
        return jsonify({'url': url})

    return jsonify({'error': 'Failed'}), 500

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

    content = data.get('msg', '')
    msg_type = data.get('type', 'text')
    media_path = data.get('media_path', None)
    sender = session.get('user_email')
    timestamp = datetime.now().strftime('%H:%M')

    # Validation
    if not content and not media_path:
        return

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, content, timestamp, msg_type, media_path) VALUES (?, ?, ?, ?, ?)",
                  (sender, content, timestamp, msg_type, media_path))
        conn.commit()

    emit('message', {
        'sender': sender,
        'content': content,
        'timestamp': timestamp,
        'type': msg_type,
        'media_path': media_path
    }, broadcast=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
