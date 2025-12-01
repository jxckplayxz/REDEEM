# app.py — CLOUD-DASH ULTIMATE 2025 — FULL FINAL VERSION (NO ERRORS, FULL HTML)
from flask import Flask, render_template_string, request, jsonify, session, redirect
import sqlite3
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cloud-dash-god-mode-forever-2025"

DB_FILE = "cloud_dash.db"
ADMIN_PASSWORD = "gameadder123"
PLACEHOLDER = "https://placehold.co/200x160/000/facc15?text=CLOUD-DASH"
CATEGORIES = ['Action', 'Puzzle', 'Strategy', 'Arcade', 'Simulation', 'Other']

# ====================== DATABASE SETUP ======================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY, title TEXT, category TEXT, image TEXT, description TEXT,
        type TEXT, sourceUrl TEXT, htmlContent TEXT, likeCount INTEGER DEFAULT 0,
        reportCount INTEGER DEFAULT 0, createdAt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    c.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)',
              ("announcement", json.dumps({"title": "Welcome to Cloud-Dash!", "message": "Your private arcade is ready • Use /admin (password: gameadder123)", "isActive": True})))
    conn.commit()
    conn.close()

init_db()

# ====================== ICONS ======================
ICONS = {
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/></svg>',
    "key": '<svg xmlns="http://www.w3.org/2000/svg" class="w-20 h-20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
}
def icon(name): return ICONS.get(name, "")

# ====================== FULL HOME PAGE HTML ======================
HTML = '''
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CLOUD-DASH • Your Private Arcade</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  </style>
</head>
<body class="min-h-screen bg-gray-900 text-white flex flex-col">

  {% if announcement.isActive %}
  <div class="bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 p-5 text-center font-bold text-xl shadow-2xl sticky top-0 z-50 flex justify-between items-center">
    <div class="flex items-center gap-4">
      {{ icon("zap")|safe }}
      <span>{{ announcement.title }} — {{ announcement.message }}</span>
    </div>
    <button onclick="this.parentElement.remove()" class="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-full">×</button>
  </div>
  {% endif %}

  <header class="bg-gray-800 p-8 shadow-2xl">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
      <h1 class="text-6xl font-extrabold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-6">
        {{ icon("cloud")|safe }} CLOUD-DASH
      </h1>
      <a href="/admin" class="bg-gradient-to-r from-indigo-600 to-purple-700 hover:from-indigo-700 hover:to-purple-800 px-10 py-5 rounded-full text-2xl font-bold shadow-2xl transform hover:scale-110 transition">
        Admin Panel
      </a>
    </div>
  </header>

  <main class="flex-grow max-w-7xl mx-auto p-8 w-full">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-10">
      {% for g in games %}
      <div onclick="location.href='/play/{{ g.id }}'" class="bg-gray-800 rounded-3xl overflow-hidden shadow-2xl hover:scale-105 transition-all cursor-pointer border-4 border-transparent hover:border-purple-500">
        <img src="{{ g.image or placeholder }}" class="w-full h-56 object-cover" onerror="this.src='{{ placeholder }}'" alt="{{ g.title }}">
        <div class="p-6">
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-2xl font-bold truncate">{{ g.title }}</h3>
            <span class="bg-purple-600 px-4 py-1 rounded-full text-sm">{{ g.category }}</span>
          </div>
          <p class="text-gray-400 text-sm line-clamp-2 mb-4">{{ g.description or "No description available" }}</p>
          <div class="flex justify-between items-center">
            <button onclick="event.stopPropagation(); like('{{ g.id }}')" class="flex items-center gap-2 text-pink-500 hover:text-pink-400 font-bold">
              {{ icon("heart")|safe }} <span id="l{{ g.id }}">{{ g.likeCount }}</span>
            </button>
            <span class="text-red-500 text-sm font-medium">{{ g.reportCount }} reports</span>
          </div>
        </div>
      </div>
      {% else %}
      <div class="col-span-full text-center py-20">
        <p class="text-4xl text-gray-500">No games yet...</p>
        <p class="text-2xl text-gray-400 mt-4">Go to <a href="/admin" class="text-indigo-400 underline">/admin</a> and add some!</p>
      </div>
      {% endfor %}
    </div>
  </main>

  <script>
    function like(id) {
      fetch("/like/" + id, {method: "POST"})
        .then(r => r.json())
        .then(d => document.getElementById("l" + id).textContent = d.likes);
    }
  </script>
</body>
</html>
'''

# ====================== FULL ADMIN PANEL HTML (WITH SEXY LOGIN) ======================
ADMIN_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cloud-Dash • Admin Panel</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 min-h-screen flex items-center justify-center p-6">

  <!-- LOGIN SCREEN -->
  <div id="login-screen" class="{% if session.admin %}hidden{% endif %} bg-white rounded-3xl shadow-3xl p-16 max-w-2xl w-full text-center transform transition-all duration-700">
    <div class="w-40 h-40 bg-gradient-to-br from-indigo-600 to-purple-700 rounded-full mx-auto flex items-center justify-center mb-10 shadow-2xl">
      {{ icon("key")|safe }}
    </div>
    <h1 class="text-6xl font-extrabold text-gray-800 mb-6">ADMIN ACCESS</h1>
    <p class="text-2xl text-gray-600 mb-12">Enter the master password to unlock full control</p>

    <form method="post" class="space-y-10">
      <input type="password" name="pwd" placeholder="Password..." autocomplete="off"
             class="w-full px-10 py-8 text-3xl text-center border-4 border-gray-300 rounded-3xl focus:border-purple-600 focus:outline-none transition"/>
      {% if error %}
        <p class="text-red-600 font-bold text-2xl animate-pulse">{{ error }}</p>
      {% endif %}
      <button class="w-full bg-gradient-to-r from-indigo-600 to-purple-700 hover:from-indigo-700 hover:to-purple-800 text-white font-black py-8 rounded-3xl text-4xl shadow-3xl transform hover:scale-105 transition">
        UNLOCK ADMIN PANEL
      </button>
    </form>
    <p class="text-gray-500 mt-10 text-lg">Default password: <code class="bg-gray-200 px-3 py-1 rounded">gameadder123</code></p>
  </div>

  <!-- FULL ADMIN DASHBOARD -->
  <div id="admin-dashboard" class="{% if not session.admin %}hidden{% endif %} bg-white rounded-3xl shadow-3xl max-w-7xl w-full mx-auto overflow-hidden">
    <div class="bg-gradient-to-r from-indigo-600 via-purple-700 to-pink-600 p-16 text-center text-white">
      <h1 class="text-7xl font-extrabold mb-4">CLOUD-DASH ADMIN</h1>
      <p class="text-3xl">Welcome back, God. Full control activated.</p>
    </div>

    <div class="p-16 space-y-16">

      <!-- ANNOUNCEMENT EDITOR -->
      <div class="bg-yellow-50 border-8 border-yellow-500 rounded-3xl p-12">
        <h2 class="text-5xl font-black text-yellow-900 mb-8">Global Announcement Banner</h2>
        <form action="/admin/announcement" method="post" class="space-y-8">
          <input name="title" value="{{ announcement.title }}" placeholder="Title (e.g. UPDATE!)" class="w-full p-6 text-2xl rounded-2xl border-4"/>
          <textarea name="message" rows="4" placeholder="Your message to all players..." class="w-full p-6 text-2xl rounded-2xl border-4">{{ announcement.message }}</textarea>
          <label class="flex items-center gap-6 text-3xl">
            <input type="checkbox" name="active" {{ 'checked' if announcement.isActive else '' }} class="w-12 h-12"/>
            <span>Show banner on homepage</span>
          </label>
          <button class="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-black py-8 rounded-2xl text-4xl shadow-2xl">
            UPDATE ANNOUNCEMENT
          </button>
        </form>
      </div>

      <!-- ADD GAME -->
      <div class="bg-indigo-50 border-8 border-indigo-500 rounded-3xl p-12">
        <h2 class="text-5xl font-black text-indigo-900 mb-8">Add New Game</h2>
        <form action="/admin/add" method="post" class="space-y-8">
          <input name="title" placeholder="Game Title" required class="w-full p-6 text-2xl rounded-2xl border-4"/>
          <select name="category" class="w-full p-6 text-2xl rounded-2xl border-4">
            {% for c in categories %}<option>{{ c }}</option>{% endfor %}
          </select>
          <input name="image" value="{{ placeholder }}" placeholder="Thumbnail URL" class="w-full p-6 text-xl rounded-2xl border-4"/>
          <textarea name="description" placeholder="Short description..." rows="3" class="w-full p-6 text-xl rounded-2xl border-4"></textarea>

          <div class="flex gap-12 text-3xl font-bold">
            <label><input type="radio" name="type" value="url" checked onclick="toggleType('url')"> External URL</label>
            <label><input type="radio" name="type" value="html" onclick="toggleType('html')"> Raw HTML</label>
          </div>

          <input name="sourceUrl" id="url-input" placeholder="https://yourgame.com" class="w-full p-6 text-xl rounded-2xl border-4"/>
          <textarea name="htmlContent" id="html-input" placeholder="<iframe src=...></iframe>" rows="12" class="w-full p-6 font-mono text-sm rounded-2xl border-4 hidden"></textarea>

          <button class="w-full bg-gradient-to-r from-indigo-600 to-purple-700 hover:from-indigo-700 hover:to-purple-800 text-white font-black py-10 rounded-2xl text-5xl shadow-3xl transform hover:scale-105 transition">
            PUBLISH GAME NOW
          </button>
        </form>
      </div>

      <div class="text-center">
        <a href="/" class="inline-flex items-center gap-4 bg-gray-800 hover:bg-gray-700 text-white px-12 py-8 rounded-2xl text-3xl font-bold shadow-2xl">
          {{ icon("home")|safe }} Back to Arcade
        </a>
      </div>
    </div>
  </div>

  <script>
    function toggleType(mode) {
      document.getElementById('url-input').classList.toggle('hidden', mode !== 'url');
      document.getElementById('html-input').classList.toggle('hidden', mode !== 'html');
    }
    {% if session.admin %}toggleType('url');{% endif %}
  </script>
</body>
</html>
'''

# ====================== ROUTES ======================
@app.route("/")
def home():
    if "user_id" not in session:
        session["user_id"] = "user_" + str(uuid.uuid4())[:8]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games ORDER BY createdAt DESC")
    games = []
    for row in c.fetchall():
        games.append({
            "id": row[0], "title": row[1], "category": row[2], "image": row[3],
            "description": row[4], "likeCount": row[8], "reportCount": row[9]
        })

    c.execute("SELECT value FROM config WHERE key = 'announcement'")
    row = c.fetchone()
    announcement = json.loads(row[0]) if row else {"title": "Welcome!", "message": "Use /admin", "isActive": True}
    conn.close()

    return render_template_string(HTML, games=games, announcement=announcement,
                                  user_id=session["user_id"], placeholder=PLACEHOLDER, icon=icon)

@app.route("/play/<game_id>")
def play(game_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, type, sourceUrl, htmlContent FROM games WHERE id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "<h1>Game not found</h1>", 404
    title, typ, url, html = row
    src = f"data:text/html;charset=utf-8,{html}" if typ == "html" else url
    return f'''
    <!DOCTYPE html>
    <html><head><title>{title}</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-black text-white">
      <div class="fixed top-0 left-0 right-0 bg-gradient-to-r from-purple-600 to-indigo-600 p-6 text-center text-3xl font-bold z-50">
        Playing: {title}
      </div>
      <iframe src="{src}" class="w-full h-screen pt-24" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen></iframe>
      <a href="/" class="fixed bottom-8 left-8 bg-indigo-600 hover:bg-indigo-700 px-8 py-4 rounded-full text-2xl font-bold z-50">← Back</a>
    </body>
    </html>
    '''

@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None
    if request.method == "POST":
        if request.form.get("pwd") == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            error = "Wrong password!"

    if not session.get("admin"):
        session.pop("admin", None)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = 'announcement'")
    row = c.fetchone()
    announcement = json.loads(row[0]) if row else {"title":"Welcome","message":"","isActive":True}
    conn.close()

    return render_template_string(ADMIN_PANEL_HTML, error=error, announcement=announcement,
                                  categories=CATEGORIES, placeholder=PLACEHOLDER, icon=icon, session=session)

@app.route("/admin/announcement", methods=["POST"])
def update_announcement():
    if not session.get("admin"): return redirect("/admin")
    data = json.dumps({
        "title": request.form["title"],
        "message": request.form["message"],
        "isActive": "active" in request.form
    })
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('announcement', ?)", (data,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/add", methods=["POST"])
def add_game():
    if not session.get("admin"): return redirect("/admin")
    gid = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''INSERT INTO games 
        (id, title, category, image, description, type, sourceUrl, htmlContent, createdAt)
        VALUES (?,?,?,?,?,?,?,?,?)''', (
        gid,
        request.form["title"],
        request.form["category"],
        request.form["image"] or PLACEHOLDER,
        request.form["description"],
        request.form["type"],
        request.form.get("sourceUrl", ""),
        request.form.get("htmlContent", ""),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/like/<game_id>", methods=["POST"])
def like(game_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE games SET likeCount = likeCount + 1 WHERE id = ?", (game_id,))
    c = conn.cursor()
    c.execute("SELECT likeCount FROM games WHERE id = ?", (game_id,))
    likes = c.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"likes": likes})

if __name__ == "__main__":
    print("="*60)
    print("CLOUD-DASH ULTIMATE 2025 IS NOW LIVE")
    print("http://127.0.0.1:5000")
    print("Admin Panel: http://127.0.0.1:5000/admin")
    print("Password: gameadder123")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)