# app.py — CLOUD-DASH ULTIMATE 2025 EDITION (WITH SEXY ADMIN LOGIN)
from flask import Flask, render_template_string, request, jsonify, session, redirect
import sqlite3
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cloud-dash-ultimate-2025-forever"

DB_FILE = "cloud_dash.db"
ADMIN_PASSWORD = "cloud12."
PLACEHOLDER = "https://placehold.co/200x160/000/facc15?text=CLOUD-DASH"
CATEGORIES = ['Action', 'Puzzle', 'Strategy', 'Arcade', 'Simulation', 'Other']

# ====================== DB INIT ======================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY, title TEXT, category TEXT, image TEXT, description TEXT,
        type TEXT, sourceUrl TEXT, htmlContent TEXT, likeCount INTEGER DEFAULT 0,
        reportCount INTEGER DEFAULT 0, createdAt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, game_id TEXT, reason TEXT, user_id TEXT, timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    c.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)',
              ("announcement", json.dumps({"title": "Welcome to Cloud-Dash!", "message": "Your private arcade is ready!", "isActive": True})))
    conn.commit()
    conn.close()

init_db()

# ====================== ICONS ======================
ICONS = {
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/></svg>',
    "plus": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>',
    "key": '<svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>',
    "flag": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
}
def icon(name): return ICONS.get(name, "")

# ====================== FULL HTML TEMPLATES ======================
HTML = '''<!DOCTYPE html>
<html lang="en" class="h-full"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>CLOUD-DASH</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="min-h-screen bg-gray-900 text-white flex flex-col">
  {% if announcement.isActive %}
  <div class="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-center font-bold shadow-2xl sticky top-0 z-50 flex justify-between items-center">
    <div class="flex items-center gap-3"><span>{{ icon("zap")|safe }}</span> <span>{{ announcement.title }} — {{ announcement.message }}</span></div>
    <button onclick="this.parentElement.remove()" class="bg-white/20 hover:bg-white/30 px-3 py-1 rounded">X</button>
  </div>
  {% endif %}

  <header class="bg-gray-800 p-6 shadow-xl">
    <div class="max-w-7xl mx-auto flex justify-between items-center">
      <h1 class="text-5xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-4">
        {{ icon("cloud")|safe }} Cloud-Dash
      </h1>
      <a href="/admin" class="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 px-8 py-4 rounded-full text-xl font-bold shadow-2xl transform hover:scale-105 transition">
        Admin Panel
      </a>
    </div>
  </header>

  <main class="flex-grow max-w-7xl mx-auto p-8 w-full">
    <div id="grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
      {% for g in games %}
      <div class="bg-gray-800 rounded-2xl overflow-hidden shadow-2xl hover:scale-105 transition transform cursor-pointer border-4 border-transparent hover:border-purple-500"
           onclick="location.href='/play/{{ g.id }}'">
        <img src="{{ g.image or placeholder }}" class="w-full h-48 object-cover" onerror="this.src='{{ placeholder }}'">
        <div class="p-6">
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-2xl font-bold truncate">{{ g.title }}</h3>
            <span class="bg-purple-600 px-3 py-1 rounded-full text-sm">{{ g.category }}</span>
          </div>
          <p class="text-gray-400 text-sm mb-4 line-clamp-2">{{ g.description or "No description" }}</p>
          <div class="flex justify-between items-center">
            <button onclick="event.stopPropagation(); like('{{ g.id }}')" class="flex items-center gap-2 text-pink-500 hover:text-pink-400">
              {{ icon("heart")|safe }} <span id="l{{ g.id }}">{{ g.likeCount }}</span>
            </button>
            <span class="text-red-500 text-sm">{{ g.reportCount }} reports</span>
          </div>
        </div>
      </div>
      {% else %}
      <p class="col-span-full text-center text-3xl text-gray-500 py-20">No games yet — time to add some!</p>
      {% endfor %}
    </div>
  </main>

  <script>
    function like(id){
      fetch("/like/"+id,{method:"POST"}).then(r=>r.json()).then(d=>{
        document.getElementById("l"+id).textContent = d.likes;
      });
    }
  </script>
</body></html>'''

# ====================== SEXY ADMIN PANEL WITH LOGIN ======================
ADMIN_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Cloud-Dash Admin</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 min-h-screen flex items-center justify-center p-4">

  <!-- LOGIN SCREEN -->
  <div id="login" class="bg-white rounded-2xl shadow-2xl p-10 max-w-md w-full text-center">
    <div class="w-32 h-32 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-full mx-auto flex items-center justify-center mb-8 shadow-xl">
      {{ icon("key")|safe }}
    </div>
    <h1 class="text-5xl font-extrabold text-gray-800 mb-4">Admin Access</h1>
    <p class="text-gray-600 mb-8">Enter the master password</p>
    
    <form method="post" class="space-y-6">
      <input type="password" name="pwd" placeholder="Password..." autocomplete="off"
             class="w-full px-6 py-5 text-xl border-2 border-gray-300 rounded-2xl focus:border-purple-600 focus:outline-none transition"/>
      {% if error %}<p class="text-red-500 font-bold text-lg">{{ error }}</p>{% endif %}
      <button class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-5 rounded-2xl text-2xl shadow-2xl transform hover:scale-105 transition">
        Unlock Panel
      </button>
    </form>
    <p class="text-xs text-gray-500 mt-6">Default: gameadder123</p>
  </div>

  <!-- FULL ADMIN DASHBOARD -->
  <div id="panel" class="{% if not session.admin %}hidden{% endif %} bg-white rounded-2xl shadow-2xl max-w-6xl w-full mx-auto overflow-hidden">
    <div class="bg-gradient-to-r from-indigo-600 to-purple-700 p-10 text-white">
      <h1 class="text-5xl font-extrabold flex items-center gap-4">
        Cloud-Dash Admin Control
      </h1>
      <p class="text-xl mt-2">You are now in full control, boss.</p>
    </div>

    <div class="p-10 space-y-12">
      <!-- Announcement -->
      <div class="bg-yellow-50 border-4 border-yellow-400 rounded-3xl p-8">
        <h2 class="text-3xl font-bold text-yellow-900 mb-6">Global Announcement</h2>
        <form action="/admin/announcement" method="post" class="space-y-6">
          <input name="title" value="{{ announcement.title }}" placeholder="Title" class="w-full p-5 rounded-xl text-xl"/>
          <textarea name="message" rows="3" placeholder="Message..." class="w-full p-5 rounded-xl">{{ announcement.message }}</textarea>
          <label class="flex items-center gap-4 text-xl">
            <input type="checkbox" name="active" {{ 'checked' if announcement.isActive else '' }} class="w-8 h-8"/>
            <span>Show banner</span>
          </label>
          <button class="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-5 rounded-xl text-2xl">Update Banner</button>
        </form>
      </div>

      <!-- Add Game -->
      <div class="bg-indigo-50 border-4 border-indigo-400 rounded-3xl p-8">
        <h2 class="text-3xl font-bold text-indigo-900 mb-6">Add New Game</h2>
        <form action="/admin/add" method="post" class="space-y-6">
          <input name="title" placeholder="Game Title" required class="w-full p-5 rounded-xl text-xl"/>
          <select name="category" class="w-full p-5 rounded-xl text-xl">
            {% for c in categories %}<option>{{ c }}</option>{% endfor %}
          </select>
          <input name="image" value="{{ placeholder }}" placeholder="Image URL" class="w-full p-5 rounded-xl"/>
          <textarea name="description" placeholder="Description" rows="3" class="w-full p-5 rounded-xl"></textarea>
          
          <div class="flex gap-8 text-xl">
            <label><input type="radio" name="type" value="url" checked onclick="t('url')"> External URL</label>
            <label><input type="radio" name="type" value="html" onclick="t('html')"> Raw HTML</label>
          </div>
          
          <input name="sourceUrl" id="url-field" placeholder="https://..." class="w-full p-5 rounded-xl"/>
          <textarea name="htmlContent" id="html-field" placeholder="<iframe>...</iframe>" rows="10" class="w-full p-5 rounded-xl font-mono text-sm hidden"></textarea>
          
          <button class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-6 rounded-xl text-3xl shadow-2xl">
            PUBLISH GAME
          </button>
        </form>
      </div>

      <a href="/" class="block text-center text-white bg-gray-800 hover:bg-gray-700 py-4 rounded-xl text-xl font-bold">
        {{ icon("home")|safe }} Back to Arcade
      </a>
    </div>
  </div>

  <script>
    function t(mode){
      document.getElementById('url-field').classList.toggle('hidden', mode !== 'url');
      document.getElementById('html-field').classList.toggle('hidden', mode !== 'html');
    }
    {% if session.admin %}t('url');{% endif %}
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
    games = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
    c.execute("SELECT value FROM config WHERE key='announcement'")
    announcement = json.loads(c.fetchone()[0]) if c.fetchone() else {"title":"Welcome!","message":"","isActive":True}
    conn.close()

    return render_template_string(HTML, games=games, announcement=announcement,
                                  user_id=session["user_id"], placeholder=PLACEHOLDER,
                                  categories=CATEGORIES, icon=icon)

@app.route("/play/<game_id>")
def play(game_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, type, sourceUrl, htmlContent FROM games WHERE id=?", (game_id,))
    row = c.fetchone()
    conn.close()
    if not row: return "Game not found", 404
    title, type_, url, html = row
    src = f"data:text/html;charset=utf-8,{html}" if type_ == "html" else url
    return f'''
    <!DOCTYPE html><html><head><title>{title}</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-black text-white"><div class="p-4 bg-yellow-600 text-center">Playing: {title}</div>
    <iframe src="{src}" class="w-full h-screen" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen></iframe>
    <a href="/" class="fixed top-4 left-4 bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-full z-50">Back</a>
    </body></html>
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

    # Load announcement
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='announcement'")
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
    conn.execute("UPDATE config SET value = ? WHERE key = 'announcement'", (data,))
    conn.commit(); conn.close()
    return redirect("/admin")

@app.route("/admin/add", methods=["POST"])
def add_game():
    if not session.get("admin"): return redirect("/admin")
    gid = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''INSERT INTO games (id,title,category,image,description,type,sourceUrl,htmlContent,createdAt)
                    VALUES (?,?,?,?,?,?,?,?,?)''', (
        gid, request.form["title"], request.form["category"], request.form["image"],
        request.form["description"], request.form["type"], request.form.get("sourceUrl",""),
        request.form.get("htmlContent",""), datetime.now().isoformat()
    ))
    conn.commit(); conn.close()
    return redirect("/")

@app.route("/like/<game_id>", methods=["POST"])
def like(game_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE games SET likeCount = likeCount + 1 WHERE id = ?", (game_id,))
    c = conn.cursor()
    c.execute("SELECT likeCount FROM games WHERE id = ?", (game_id,))
    likes = c.fetchone()[0]
    conn.commit(); conn.close()
    return jsonify({"likes": likes})

if __name__ == "__main__":
    print("CLOUD-DASH ULTIMATE 2025 IS LIVE")
    print("http://127.0.0.1:5000")
    print("Admin password: gameadder123")
    app.run(host="0.0.0.0", port=5000, debug=True)