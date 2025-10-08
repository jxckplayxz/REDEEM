# app.py
from flask import Flask, request, jsonify, g, render_template_string, redirect, url_for, session
import sqlite3
import os
from functools import wraps

# -------------------- CONFIG --------------------
DATABASE = 'clicks.db'
# Default admin password set as requested. You can override with environment variable ADMIN_PASS.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASS", "Admin121")
# Flask secret for session signing. Override in env for production.
SECRET_KEY = os.environ.get("FLASK_SECRET", "change_this_secret_key")
# Optional simple server token to require from clients. If you don't want this, leave empty "".
SERVER_TOKEN = os.environ.get("SERVER_TOKEN", "")

app = Flask(__name__)
app.secret_key = SECRET_KEY

# -------------------- DB HELPERS --------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS clicks (
        userId TEXT PRIMARY KEY,
        username TEXT,
        scriptId TEXT,
        clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS meta (
        k TEXT PRIMARY KEY,
        v TEXT
    );
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# -------------------- AUTH DECORATOR --------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return decorated

# -------------------- API ENDPOINTS --------------------
@app.route('/api/status', methods=['GET'])
def api_status():
    """
    Query params:
      - userId (required)
    Returns JSON: { clicked: bool, message: "..." }
    """
    userId = request.args.get('userId')
    db = get_db()
    clicked = False
    if userId:
        cur = db.execute('SELECT 1 FROM clicks WHERE userId=?', (userId,))
        row = cur.fetchone()
        clicked = bool(row)
    cur2 = db.execute('SELECT v FROM meta WHERE k="message"')
    r2 = cur2.fetchone()
    message = r2['v'] if r2 else ""
    return jsonify({"clicked": clicked, "message": message})

@app.route('/api/click', methods=['POST'])
def api_click():
    """
    Expects JSON body: { userId: "...", username: "...", scriptId: "..." }
    Optional: require header 'X-Server-Token' to match SERVER_TOKEN (if set).
    """
    # simple token protection (optional)
    if SERVER_TOKEN:
        token = request.headers.get('X-Server-Token', '')
        if token != SERVER_TOKEN:
            return jsonify({"error":"invalid token"}), 403

    data = request.json or {}
    userId = str(data.get('userId', 'unknown'))
    username = str(data.get('username', 'Unknown'))
    scriptId = str(data.get('scriptId', ''))
    db = get_db()
    # Insert or replace so the latest username/scriptId is stored
    db.execute('INSERT OR REPLACE INTO clicks(userId, username, scriptId) VALUES (?, ?, ?)', (userId, username, scriptId))
    db.commit()
    cur2 = db.execute('SELECT v FROM meta WHERE k="message"')
    r2 = cur2.fetchone()
    message = r2['v'] if r2 else ""
    return jsonify({"success": True, "clicked": True, "message": message})

# -------------------- ADMIN PAGES --------------------
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    # Simple password-based session login
    if request.method == 'POST':
        pw = request.form.get('password','')
        if pw == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(LOGIN_HTML, error="Wrong password")
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    cur = db.execute('SELECT userId, username, scriptId, clicked_at FROM clicks ORDER BY clicked_at DESC')
    rows = cur.fetchall()
    cur2 = db.execute('SELECT v FROM meta WHERE k="message"')
    r2 = cur2.fetchone()
    message = r2['v'] if r2 else ""
    return render_template_string(ADMIN_HTML, users=rows, message=message)

@app.route('/admin/delete_user/<userId>', methods=['POST'])
@admin_required
def admin_delete_user(userId):
    db = get_db()
    db.execute('DELETE FROM clicks WHERE userId=?', (userId,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/set_message', methods=['POST'])
@admin_required
def admin_set_message():
    msg = request.form.get('message','')
    db = get_db()
    db.execute('INSERT OR REPLACE INTO meta(k,v) VALUES ("message", ?)', (msg,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

# -------------------- SIMPLE INLINE HTML TEMPLATES --------------------
LOGIN_HTML = '''
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Admin Login</title></head>
<body>
  <h2>Admin login</h2>
  {% if error %}<p style="color:red">{{error}}</p>{% endif %}
  <form method="post">
    <input type="password" name="password" placeholder="password" />
    <button type="submit">Login</button>
  </form>
</body>
</html>
'''

ADMIN_HTML = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Admin Dashboard</title>
  <style>
    body{font-family:Arial,Helvetica,sans-serif;padding:20px}
    table{border-collapse:collapse;width:100%}
    th,td{border:1px solid #ddd;padding:8px;text-align:left}
    th{background:#f2f2f2}
    textarea{width:100%;box-sizing:border-box}
    form.inline{display:inline}
  </style>
</head>
<body>
  <h2>Admin Dashboard</h2>
  <p><a href="{{ url_for('admin_logout') }}">Logout</a></p>

  <h3>Current announcement message</h3>
  <form action="{{ url_for('admin_set_message') }}" method="post">
    <textarea name="message" rows="3" placeholder="Announcement...">{{message}}</textarea><br/>
    <button type="submit">Set message</button>
  </form>

  <h3>Clicked users</h3>
  <table>
    <tr><th>UserId</th><th>Username</th><th>ScriptId</th><th>When</th><th>Action</th></tr>
    {% for u in users %}
    <tr>
      <td>{{u['userId']}}</td>
      <td>{{u['username']}}</td>
      <td>{{u['scriptId']}}</td>
      <td>{{u['clicked_at']}}</td>
      <td>
        <form class="inline" action="{{ url_for('admin_delete_user', userId=u['userId']) }}" method="post" onsubmit="return confirm('Delete {{u['userId']}}?')">
          <button type="submit">Delete</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
'''

# -------------------- STARTUP --------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    # For local testing use debug=True. For production use gunicorn/uWSGI + nginx and set debug=False.
    app.run(host='0.0.0.0', port=5000, debug=True)