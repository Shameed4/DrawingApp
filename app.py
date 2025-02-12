import os
import sqlite3
import time
import base64
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
import eventlet
import eventlet.wsgi

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  
# or async_mode='gevent' if you prefer

DB_FILE = 'database.db'

# Add theme definitions
THEMES = {
    "barbenheimer": [
        "#E0218A", "#FF99CC", "#FFD1DC", "#D81B60", "#FF5733", "#FFC300",
        "#D98880", "#C70039", "#900C3F", "#581845", "#2C3E50", "#A93226",
        "#F4A261", "#1C1C1C", "#F5F5F5"
    ],
    "fooood": [
        "#FF6B35", "#FFB400", "#F8E16C", "#C41E3A", "#8D4004", "#FFDAB9",
        "#A6C36F", "#D1C4E9", "#F4A460", "#6B4226", "#D32F2F", "#9CCC65",
        "#C0C0C0", "#F5DEB3", "#D7A86E"
    ],
    "brainrot": [
        "#FF00FF", "#00FFFF", "#FFFF00", "#FF4500", "#800080", "#00FF00",
        "#FF1493", "#8A2BE2", "#2E2B5F", "#D3D3D3", "#6A5ACD", "#C71585",
        "#FF6347", "#A52A2A", "#333333"
    ],
    "wolfie": [
        "#C8102E", "#041E42", "#8B0000", "#DC143C", "#A52A2A", "#808080",
        "#1C1C1C", "#D3D3D3", "#4B0082", "#B22222", "#2E8B57", "#FFD700",
        "#708090", "#696969", "#F4A460"
    ]
}

# Update GAME_STATE with a current_theme property
GAME_STATE = {
    'in_progress': False,
    'voting_in_progress': False,
    'round_start_time': None,
    'round_duration': 600,  # Default to 10 minutes
    'voting_start_time': None,
    'voting_duration': 600,
    'round_has_ended': False,
    'voting_has_ended': False,
    'theme_colors': THEMES["barbenheimer"],
    'drawing_time': 600  # Default drawing time in seconds (10 minutes)
}


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_first_request
def init_db():
    # Create tables if they don't exist
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        canvas TEXT,
        webcam TEXT,
        score INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

    # Create a default admin if not present
    create_user_if_not_exists("Odinroast", "Toor", is_admin=True)

def create_user_if_not_exists(username, password, is_admin=False):
    conn = get_db_connection()
    c = conn.cursor()
    # check if user exists
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row:
        hashed = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                  (username, hashed, 1 if is_admin else 0))
        conn.commit()
    conn.close()

@app.route("/")
def home():
    # If user is logged in, go to drawing or whichever page is active
    if 'username' in session:
        return redirect(url_for('drawing'))
    return render_template('index.html')  # Standard user login

@app.route("/login", methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()

    if user:
        if check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            conn.close()
            return redirect(url_for('drawing'))
        else:
            conn.close()
            return "Invalid credentials", 401
    else:
        hashed_password = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, hashed_password, False))
        conn.commit()
        session['username'] = username
        session['is_admin'] = False
        conn.close()
        return redirect(url_for('drawing'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/admin")
def admin():
    # If already logged in as admin, go to admin dashboard
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route("/admin_login", methods=['POST'])
def admin_login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    # same check as normal
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password) and user['is_admin']:
        session['username'] = user['username']
        session['is_admin'] = True
        return redirect(url_for('admin_dashboard'))
    return "Invalid admin credentials", 401

@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    return render_template("admin_dashboard.html", GAME_STATE=GAME_STATE)

@app.route("/start_game", methods=['POST'])
def start_game():
    # Only admin can start
    if not session.get('is_admin'):
        return "Unauthorized", 403
    # Reset game state
    GAME_STATE['in_progress'] = True
    GAME_STATE['voting_in_progress'] = False
    GAME_STATE['round_start_time'] = time.time()
    GAME_STATE['round_has_ended'] = False
    GAME_STATE['voting_has_ended'] = False

    # Clear old submissions
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM submissions")
    conn.commit()
    conn.close()

    # Broadcast to all clients
    socketio.emit('startDrawing', {
        'duration': GAME_STATE['round_duration']
    })

    return redirect(url_for('admin_dashboard'))

@app.route("/start_voting", methods=['POST'])
def start_voting():
    if not session.get('is_admin'):
        return "Unauthorized", 403

    GAME_STATE['in_progress'] = False
    GAME_STATE['round_has_ended'] = True
    GAME_STATE['voting_in_progress'] = True
    GAME_STATE['voting_start_time'] = time.time()
    GAME_STATE['voting_has_ended'] = False

    # Broadcast to all clients
    socketio.emit('startVoting', {
        'duration': GAME_STATE['voting_duration']
    })

    return redirect(url_for('admin_dashboard'))

@app.route("/end_voting", methods=['POST'])
def end_voting():
    if not session.get('is_admin'):
        return "Unauthorized", 403

    GAME_STATE['voting_in_progress'] = False
    GAME_STATE['voting_has_ended'] = True

    # Broadcast to all clients
    socketio.emit('endVoting', {})

    return redirect(url_for('results'))

@app.route("/set_theme/<theme>", methods=['POST'])
def set_theme(theme):
    if not session.get('is_admin'):
        return "Unauthorized", 403
    if theme not in THEMES:
        return "Theme not found", 404
    GAME_STATE['theme_colors'] = THEMES[theme]
    return redirect(url_for('admin_dashboard'))

@app.route("/set_drawing_time", methods=['POST'])
def set_drawing_time():
    if not session.get('is_admin'):
        return "Unauthorized", 403

    drawing_time = int(request.form.get('drawing_time', 600))  # Default to 10 minutes
    GAME_STATE['round_duration'] = drawing_time
    return redirect(url_for('admin_dashboard'))

@app.route("/drawing")
def drawing():
    if 'username' not in session:
        return redirect(url_for('home'))
    if GAME_STATE['round_has_ended']:
        return "Drawing round ended. Please wait for voting or refresh."
    return render_template("drawing.html", game_state=GAME_STATE, theme_colors=GAME_STATE['theme_colors'])

@app.route("/submit_drawing", methods=['POST'])
def submit_drawing():
    # Called by the client at the end of 30s or if user finishes early
    if 'username' not in session:
        return "Unauthorized", 403
    data = request.json
    canvas_data = data.get('canvas')  # base64
    webcam_data = data.get('webcam')  # base64

    # store in DB
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO submissions (username, canvas, webcam, score) VALUES (?,?,?,?)",
              (session['username'], canvas_data, webcam_data, 0))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.route("/voting")
def voting():
    # Show all submissions, but hide the username
    if 'username' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, canvas, webcam, score FROM submissions")
    rows = c.fetchall()
    submissions = [dict(r) for r in rows]
    conn.close()

    # Pass them to the template
    return render_template("voting.html", submissions=submissions)

@app.route("/finalize_ratings", methods=['POST'])
def finalize_ratings():
    """
    Expects a JSON body with a dictionary of { submissionId: rating } pairs.
    Example:
      {
        "1": 3,
        "2": 5,
        "7": 2
      }
    Then we update the 'score' in 'submissions' for each given ID.
    """
    if 'username' not in session:
        return {"error": "Unauthorized"}, 403

    data = request.json  # e.g., {"1":3, "2":5}
    if not data:
        return {"error": "No data received"}, 400

    conn = get_db_connection()
    c = conn.cursor()

    # For each final rating: add it to the submission's score
    for sub_id_str, rating_val in data.items():
        sub_id = int(sub_id_str)
        rating = int(rating_val)
        c.execute("UPDATE submissions SET score = score + ? WHERE id = ?", (rating, sub_id))

    conn.commit()
    conn.close()

    return {"status": "ok"}

@app.route("/results")
def results():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, canvas, webcam, score FROM submissions ORDER BY score DESC")
    all_rows = c.fetchall()
    top3 = all_rows[:3]
    others = all_rows[3:]
    conn.close()
    return render_template("results.html", top3=top3, others=others)

if __name__ == "__main__":
    import eventlet
    import eventlet.wsgi
    # For production, run behind gunicorn or similar. For dev, do:
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
